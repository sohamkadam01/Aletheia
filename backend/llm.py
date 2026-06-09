import re
import json
import threading
from llm_providers import (
    OLLAMA_API_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_PREDICT,
    OLLAMA_TIMEOUT_SECONDS,
    OPENROUTER_MODELS,
    OPENROUTER_MAX_TOKENS,
    OPENROUTER_TIMEOUT_SECONDS,
    cancelled as _cancelled,
    clean_openrouter_response as _clean_openrouter_response,
    generate_with_ollama as _generate_with_ollama,
    has_openrouter_key as _has_openrouter_key,
    list_ollama_models,
    list_openrouter_models,
    mark_openrouter_unavailable as _mark_openrouter_unavailable,
    ollama_enabled as _ollama_enabled,
    ollama_payload as _ollama_payload,
    openrouter_available as _openrouter_available,
    openrouter_cooldown_reason,
    openrouter_headers as _openrouter_headers,
    openrouter_payload as _openrouter_payload,
    read_openrouter_stream as _read_openrouter_stream,
    resolve_ollama_model as _resolve_ollama_model,
    resolve_openrouter_models as _resolve_openrouter_models,
    session,
    short_error_body as _short_error_body,
    should_skip_openrouter_after_response as _should_skip_openrouter_after_response,
)
from prompts.auxiliary import (
    build_external_search_check_prompt,
    build_safety_prompt,
    build_starter_questions_prompt,
    build_suggestions_prompt,
)
from prompts.chat import build_chat_prompt, build_stream_chat_prompt, is_flowchart_request

# ── Token budgets per request type ───────────────────────────────────────────
# Normal chat is fast/small; flowchart and compare need larger budgets.
FLOWCHART_MAX_TOKENS  = 2400   # React Flow JSON is large
FLOWCHART_NUM_PREDICT = 2400
COMPARE_MAX_TOKENS    = 2000   # Compare reports are detailed
COMPARE_NUM_PREDICT   = 1200
COMPARE_NUM_CTX       = 4096   # Compare prompts are long — keep full context window
NORMAL_MAX_TOKENS     = 800    # Normal chat rarely needs more than 800 tokens
NORMAL_NUM_PREDICT    = 600    # Fast stop for prose answers
NORMAL_NUM_CTX        = 2048   # Normal prompts fit in 2048 — faster memory allocation

# ── Context compression limits per mode ──────────────────────────────────────
# Tighter for normal chat to reduce prompt size and speed up first token.
NORMAL_CONTEXT_MAX_CHARS  = 2400
COMPLEX_CONTEXT_MAX_CHARS = 3200

BROKEN_UTF8_REPLACEMENTS = {
    "\u00e2\u0080\u0091": "-",
    "\u00e2\u0080\u0093": "-",
    "\u00e2\u0080\u0094": "-",
    "\u00e2\u0080\u00a6": "...",
    "\u00e2\u0080\u0098": "'",
    "\u00e2\u0080\u0099": "'",
    "\u00e2\u0080\u009c": '"',
    "\u00e2\u0080\u009d": '"',
    "\u00c2\u00a0": " ",
    "\u00e3\u0080\u0090": "[",
    "\u00e3\u0080\u0091": "]",
}


def normalize_model_text(text: str) -> str:
    value = str(text or "")
    for broken, fixed in BROKEN_UTF8_REPLACEMENTS.items():
        value = value.replace(broken, fixed)
    return value


def warmup_ollama() -> None:
    """Send a lightweight ping to Ollama on startup so the model is preloaded into RAM."""
    if not _ollama_enabled():
        return

    def _ping() -> None:
        try:
            selected_model = _resolve_ollama_model(None)
            response = session.post(
                f"{OLLAMA_API_URL}/api/generate",
                json={
                    "model": selected_model,
                    "prompt": "hi",
                    "stream": False,
                    "keep_alive": "-1",
                    "options": {"num_predict": 1},
                },
                timeout=30,
            )
            if response.status_code == 200:
                print(f"Ollama warmup complete: model '{selected_model}' is loaded.")
            else:
                print(f"Ollama warmup returned {response.status_code} — model may still be cold.")
        except Exception as exc:
            print(f"Ollama warmup skipped: {exc}")

    threading.Thread(target=_ping, daemon=True).start()


def _answer_result(answer: str, provider: str, model: str, fallback_reason: str = "") -> dict:
    return {
        "answer": answer,
        "provider": provider,
        "model": model,
        "fallback_reason": fallback_reason,
    }


def _build_answer_prompt(
    context: str,
    question: str,
    history: list[dict] = None,
    external_context: str = None,
    confidence: str = "high",
    feedback_guidance: str = "",
    concise_answer: bool = False,
) -> str:
    return build_stream_chat_prompt(
        context=context,
        question=question,
        history=history,
        external_context=external_context,
        confidence=confidence,
        feedback_guidance=feedback_guidance,
        concise_answer=concise_answer,
    )


def _effective_budgets(is_flowchart: bool, is_compare: bool) -> dict:
    """Return the right token and context budgets for this request type."""
    if is_flowchart:
        return {
            "max_tokens": FLOWCHART_MAX_TOKENS,
            "num_predict": FLOWCHART_NUM_PREDICT,
            "num_ctx": NORMAL_NUM_CTX,
            "context_max_chars": COMPLEX_CONTEXT_MAX_CHARS,
        }
    if is_compare:
        return {
            "max_tokens": COMPARE_MAX_TOKENS,
            "num_predict": COMPARE_NUM_PREDICT,
            "num_ctx": COMPARE_NUM_CTX,
            "context_max_chars": COMPLEX_CONTEXT_MAX_CHARS,
        }
    return {
        "max_tokens": NORMAL_MAX_TOKENS,
        "num_predict": NORMAL_NUM_PREDICT,
        "num_ctx": NORMAL_NUM_CTX,
        "context_max_chars": NORMAL_CONTEXT_MAX_CHARS,
    }


# ── React Flow JSON validation ────────────────────────────────────────────────

def _extract_json_block(answer: str) -> str:
    match = re.search(r"```json\s*([\s\S]*?)```", answer or "")
    if match:
        return match.group(1).strip()
    match = re.search(r"\{[\s\S]*\}", answer or "")
    if match:
        return match.group(0).strip()
    return ""


def _flowchart_json_complete(answer: str) -> bool:
    raw = _extract_json_block(answer)
    if not raw:
        return False
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False
    return bool(data.get("nodes")) and bool(data.get("edges"))


def is_flowchart_request_cached(answer: str) -> bool:
    return True


def _flowchart_repair_prompt(context: str, question: str, bad_answer: str) -> str:
    return f"""
The user asked for a flowchart but the previous JSON response was incomplete or truncated.

User request:
{question}

Relevant context:
---------------------
{context[:8000]}
---------------------

Previous incomplete answer:
---------------------
{bad_answer[:3000]}
---------------------

Regenerate the complete flowchart JSON from scratch. Output ONLY a fenced ```json block.
Rules:
- Include "diagram_topic", "context_basis", "layout", "nodes", and "edges".
- Use node types: terminal, input, process, decision, output.
- Use semantic IDs like "validate_input", never single letters.
- Every node must have a specific topic-grounded "label" (2-6 words).
- Close the JSON completely — do not truncate.
- Do not add any text outside the ```json block.

Answer:
"""


def _repair_flowchart_answer(
    answer: str,
    *,
    context: str,
    question: str,
    provider: str,
    model: str,
    headers: dict = None,
    cancel_event=None,
) -> str:
    if not is_flowchart_request(question):
        return answer
    if _flowchart_json_complete(answer):
        return answer
    if _cancelled(cancel_event):
        return answer

    print(f"Flowchart JSON incomplete — attempting repair via {provider}.")
    repair_prompt = _flowchart_repair_prompt(context, question, answer)

    try:
        if provider == "OpenRouter" and headers:
            payload = _openrouter_payload(
                model,
                repair_prompt,
                "You output only a complete fenced ```json React Flow flowchart block. No other text.",
                stream=True,
            )
            payload["max_tokens"] = FLOWCHART_MAX_TOKENS
            response = session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=OPENROUTER_TIMEOUT_SECONDS,
                stream=True,
            )
            if response.status_code == 200:
                repaired = _read_openrouter_stream(response, cancel_event)
                if repaired and _flowchart_json_complete(repaired):
                    print("Flowchart repair successful (OpenRouter).")
                    return repaired

        elif provider == "Ollama" and _ollama_enabled():
            if len(answer.strip()) > 100:
                repaired = _generate_with_ollama(
                    repair_prompt,
                    model=model,
                    cancel_event=cancel_event,
                    options_override={
                        "num_predict": FLOWCHART_NUM_PREDICT,
                        "num_ctx": NORMAL_NUM_CTX,
                    },
                )
                if repaired and _flowchart_json_complete(repaired):
                    print("Flowchart repair successful (Ollama).")
                    return repaired

    except Exception as exc:
        print(f"Flowchart repair failed: {exc}")

    return answer


def stream_answer(
    context: str,
    question: str,
    history: list[dict] = None,
    external_context: str = None,
    ollama_model: str = None,
    openrouter_model: str = None,
    confidence: str = "high",
    feedback_guidance: str = "",
    force_provider: str = "",
    concise_answer: bool = False,
    cancel_event=None,
):
    prompt = _build_answer_prompt(context, question, history, external_context, confidence, feedback_guidance, concise_answer)
    fallback_reason = ""
    provider_preference = (force_provider or "").lower()
    is_flowchart = is_flowchart_request(question)
    budgets = _effective_budgets(is_flowchart=is_flowchart, is_compare=False)

    if provider_preference != "ollama" and _openrouter_available():
        headers = _openrouter_headers()
        for model in _resolve_openrouter_models(openrouter_model):
            payload = _openrouter_payload(
                model,
                prompt,
                "Answer naturally using only the provided webpage context. Use short paragraph-first formatting, use numbered lists for ordered steps/reasons/phases where helpful, bold important key terms with markdown, cite source labels, and use plain ASCII punctuation only.",
                stream=True
            )
            payload["max_tokens"] = budgets["max_tokens"]
            try:
                response = session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=OPENROUTER_TIMEOUT_SECONDS,
                    stream=True
                )
                if response.status_code == 200:
                    yield {"type": "meta", "provider": "OpenRouter", "model": model, "fallback_reason": ""}
                    for line in response.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data: "):
                            continue
                        raw = line[6:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            data = json.loads(raw)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield {"type": "delta", "text": normalize_model_text(_clean_openrouter_response(delta))}
                        except json.JSONDecodeError:
                            continue
                    yield {"type": "done", "provider": "OpenRouter", "model": model}
                    return

                fallback_reason = f"{model} failed with {response.status_code}: {_short_error_body(response)}"
                if _should_skip_openrouter_after_response(response, model):
                    break
            except Exception as e:
                fallback_reason = f"{model} request failed: {str(e)}"
                _mark_openrouter_unavailable(fallback_reason)
                break
    elif provider_preference == "openrouter":
        fallback_reason = "OpenRouter is unavailable."
    elif not _has_openrouter_key():
        fallback_reason = "OpenRouter API key is not configured."

    if provider_preference == "openrouter":
        yield {"type": "meta", "provider": "OpenRouter", "model": openrouter_model or "", "fallback_reason": fallback_reason}
        yield {"type": "delta", "text": "The selected OpenRouter model could not generate an answer. Please try another model or Auto mode."}
        yield {"type": "done", "provider": "OpenRouter", "model": openrouter_model or ""}
        return

    if not _ollama_enabled():
        yield {"type": "meta", "provider": "none", "model": "", "fallback_reason": fallback_reason}
        yield {"type": "delta", "text": "The AI service is temporarily unavailable. Please try again in a moment."}
        yield {"type": "done", "provider": "none", "model": ""}
        return

    selected_ollama_model = _resolve_ollama_model(ollama_model)
    yield {"type": "meta", "provider": "Ollama", "model": selected_ollama_model, "fallback_reason": fallback_reason}
    try:
        ollama_opts = {
            "num_predict": budgets["num_predict"],
            "num_ctx": budgets["num_ctx"],
        }
        response = session.post(
            f"{OLLAMA_API_URL}/api/generate",
            json=_ollama_payload(prompt, selected_ollama_model, options_override=ollama_opts),
            timeout=OLLAMA_TIMEOUT_SECONDS,
            stream=True
        )
        if response.status_code != 200:
            yield {"type": "delta", "text": "The local model failed while generating an answer."}
        else:
            for line in response.iter_lines(decode_unicode=True):
                if _cancelled(cancel_event):
                    response.close()
                    break
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("response"):
                    yield {"type": "delta", "text": normalize_model_text(data["response"])}
                if data.get("done"):
                    break
    except Exception as e:
        yield {"type": "delta", "text": f"All models failed. Last error from Ollama: {str(e)}"}
    yield {"type": "done", "provider": "Ollama", "model": selected_ollama_model}


def generate_answer(
    context: str,
    question: str,
    history: list[dict] = None,
    external_context: str = None,
    ollama_model: str = None,
    openrouter_model: str = None,
    confidence: str = "high",
    feedback_guidance: str = "",
    force_provider: str = "",
    concise_answer: bool = False,
    cancel_event=None,
    document_mode: str = "website",
) -> dict:
    prompt = build_chat_prompt(
        context=context,
        question=question,
        history=history,
        external_context=external_context,
        confidence=confidence,
        feedback_guidance=feedback_guidance,
        concise_answer=concise_answer,
    )

    is_flowchart = is_flowchart_request(question)
    is_compare = document_mode == "compare"
    budgets = _effective_budgets(is_flowchart=is_flowchart, is_compare=is_compare)

    fallback_reason = ""
    provider_preference = (force_provider or "").lower()
    if _cancelled(cancel_event):
        return _answer_result("", "cancelled", "", "Request cancelled.")

    if provider_preference != "ollama" and _openrouter_available():
        headers = _openrouter_headers()

        for model in _resolve_openrouter_models(openrouter_model):
            if _cancelled(cancel_event):
                return _answer_result("", "cancelled", "", "Request cancelled.")

            payload = _openrouter_payload(
                model,
                prompt,
                "You are a friendly website and document assistant. Answer in short clear paragraphs using the provided context, compare website and document sections when asked, bold important key terms with markdown, cite source labels, and use plain ASCII punctuation only.",
                stream=True
            )
            payload["max_tokens"] = budgets["max_tokens"]

            try:
                response = session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=OPENROUTER_TIMEOUT_SECONDS,
                    stream=True
                )

                if response.status_code == 200:
                    answer = _read_openrouter_stream(response, cancel_event)
                    if _cancelled(cancel_event):
                        return _answer_result("", "cancelled", "", "Request cancelled.")
                    if answer:
                        answer = normalize_model_text(answer)
                        answer = _clean_openrouter_response(answer)
                        answer = _repair_flowchart_answer(
                            answer,
                            context=context,
                            question=question,
                            provider="OpenRouter",
                            model=model,
                            headers=headers,
                            cancel_event=cancel_event,
                        )
                        return _answer_result(answer, "OpenRouter", model)
                    fallback_reason = f"{model} returned no streamed content."
                    print(fallback_reason)
                else:
                    fallback_reason = f"{model} failed with {response.status_code}: {_short_error_body(response)}"
                    print(f"OpenRouter model {fallback_reason}")
                    if _should_skip_openrouter_after_response(response, model):
                        break
            except Exception as e:
                fallback_reason = f"{model} request failed: {str(e)}"
                print(f"OpenRouter model {fallback_reason}")
                _mark_openrouter_unavailable(fallback_reason)
                break
    elif provider_preference == "ollama":
        fallback_reason = "Ollama was requested."
    elif not _has_openrouter_key():
        fallback_reason = "OpenRouter API key is not configured."
    else:
        fallback_reason = f"OpenRouter is cooling down: {openrouter_cooldown_reason()}"

    if provider_preference == "openrouter":
        return _answer_result(
            "The selected OpenRouter model could not generate an answer. Please try another model or Auto mode.",
            "OpenRouter",
            openrouter_model or "",
            fallback_reason
        )

    if not _ollama_enabled():
        if _has_openrouter_key():
            return _answer_result("The AI service is temporarily unavailable. Please try again in a moment.", "none", "", fallback_reason)
        return _answer_result("OpenRouter is not configured. Add OPENROUTER_API_KEY to enable chat responses.", "none", "", fallback_reason)

    selected_ollama_model = _resolve_ollama_model(ollama_model)
    print("Falling back to local Ollama model:", selected_ollama_model)
    try:
        ollama_opts_override = {
            "num_predict": budgets["num_predict"],
            "num_ctx": budgets["num_ctx"],
        }
        answer = _generate_with_ollama(
            prompt,
            model=selected_ollama_model,
            cancel_event=cancel_event,
            options_override=ollama_opts_override,
        )
        if _cancelled(cancel_event):
            return _answer_result("", "cancelled", "", "Request cancelled.")
        answer = normalize_model_text(answer or "")
        answer = _repair_flowchart_answer(
            answer,
            context=context,
            question=question,
            provider="Ollama",
            model=selected_ollama_model,
            cancel_event=cancel_event,
        )
        return _answer_result(
            answer or "The local model failed while generating an answer.",
            "Ollama",
            selected_ollama_model,
            fallback_reason
        )

    except Exception as e:
        return _answer_result(f"All models failed. Last error from Ollama: {str(e)}", "Ollama", selected_ollama_model, fallback_reason)


def generate_suggestions(context: str, question: str, answer: str, history: list[dict] = None) -> list[str]:
    prompt = build_suggestions_prompt(context, question, answer, history)
    try:
        if _openrouter_available():
            headers = _openrouter_headers()
            payload = {
                "model": OPENROUTER_MODELS[0],
                "messages": [{"role": "user", "content": prompt}]
            }
            response = session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                text = response.json()["choices"][0]["message"]["content"]
                return [q.strip() for q in text.split("\n") if q.strip()][:3]
            _should_skip_openrouter_after_response(response, OPENROUTER_MODELS[0])

        if _ollama_enabled():
            text = _generate_with_ollama(prompt, timeout=10)
            if text:
                return [q.strip() for q in text.split("\n") if q.strip()][:3]
    except Exception as e:
        print(f"Suggestions generation failed: {str(e)}")

    return ["Tell me more", "Summarize this page", "Helpful links"]


def generate_starter_questions(context: str, page_title: str = "") -> list[str]:
    prompt = build_starter_questions_prompt(context, page_title)
    try:
        if _openrouter_available():
            headers = _openrouter_headers()
            payload = {
                "model": OPENROUTER_MODELS[0],
                "messages": [{"role": "user", "content": prompt}]
            }
            response = session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                text = response.json()["choices"][0]["message"]["content"]
                questions = [q.strip(" -0123456789.").strip() for q in text.split("\n") if q.strip()]
                return questions[:3]
            _should_skip_openrouter_after_response(response, OPENROUTER_MODELS[0])

        if _ollama_enabled():
            text = _generate_with_ollama(prompt, timeout=20)
            questions = [q.strip(" -0123456789.").strip() for q in text.split("\n") if q.strip()]
            return questions[:3]
    except Exception as e:
        print(f"Starter question generation failed: {str(e)}")

    return []


def rewrite_follow_up_question(question: str, history: list[dict] = None) -> str:
    normalized = " ".join((question or "").lower().split())
    vague_questions = {
        "tell me more", "explain more", "more details", "summarize briefly",
        "explain simply", "key takeaways", "list key details", "show important links",
        "find related pages", "how do i get started", "what about this", "why", "how",
    }
    is_vague = (
        normalized in vague_questions
        or len(normalized.split()) <= 3
        or normalized.startswith(("what about", "tell me more about", "explain that"))
    )
    if not is_vague or not history:
        return question

    previous_user_questions = [
        str(item.get("text", "")).strip()
        for item in history
        if item.get("sender") == "user" and str(item.get("text", "")).strip()
    ]
    previous_question = ""
    for candidate in reversed(previous_user_questions):
        if candidate.lower().strip() != normalized:
            previous_question = candidate
            break
    if not previous_question or previous_question.lower().strip() == normalized:
        return question

    return f"{question} about: {previous_question}"


def analyze_website_safety(url: str, content_summary: str) -> dict:
    prompt = build_safety_prompt(url, content_summary)
    try:
        if _openrouter_available():
            headers = _openrouter_headers()
            payload = {
                "model": OPENROUTER_MODELS[0],
                "messages": [{"role": "user", "content": prompt}]
            }
            response = session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            if response.status_code == 200:
                text = response.json()["choices"][0]["message"]["content"]
                status = "safe"
                if "harmful" in text.lower(): status = "harmful"
                elif "warning" in text.lower(): status = "warning"
                reason_match = re.search(r'"reason":\s*"([^"]+)"', text)
                reason = reason_match.group(1) if reason_match else "Verified safe by AI analysis."
                if status == "safe" and not reason_match: reason = "This website appears legitimate and safe."
                return {"status": status, "reason": reason}
            _should_skip_openrouter_after_response(response, OPENROUTER_MODELS[0])

        domain = url.split("//")[-1].split("/")[0]
        high_trust = ["google.com", "github.com", "microsoft.com", "apple.com", "amazon.com", "wikipedia.org"]
        if any(trusted in domain for trusted in high_trust):
            return {"status": "safe", "reason": "Known high-trust official domain."}

    except Exception as e:
        print(f"Safety analysis failed: {str(e)}")

    return {"status": "safe", "reason": "No immediate threats detected."}


def needs_external_search(context: str, question: str) -> bool:
    """Kept for backward compatibility. No longer makes an LLM call — uses context length as proxy."""
    return len(context) < 100
