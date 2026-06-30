import json
import os
import time

import requests
from dotenv import load_dotenv

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _genai = None
    _genai_types = None
    _GENAI_AVAILABLE = False

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

DEFAULT_OPENROUTER_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-4-31b-it:free",
]

OPENROUTER_MODELS = [
    model.strip()
    for model in os.getenv("OPENROUTER_MODELS", ",".join(DEFAULT_OPENROUTER_MODELS)).split(",")
    if model.strip()
]

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
ENABLE_OLLAMA_FALLBACK = os.getenv("ENABLE_OLLAMA_FALLBACK", "true").lower() in ("1", "true", "yes", "on")
OPENROUTER_TIMEOUT_SECONDS = int(os.getenv("OPENROUTER_TIMEOUT_SECONDS", os.getenv("LLM_TIMEOUT_SECONDS", "120")))
OPENROUTER_MAX_ATTEMPTS = int(os.getenv("OPENROUTER_MAX_ATTEMPTS", "1"))
# Base token limit for normal chat. Flowchart/compare use higher limits set in llm.py.
OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "800"))
OPENROUTER_TEMPERATURE = float(os.getenv("OPENROUTER_TEMPERATURE", "0.2"))
# top_p=1.0 when temperature is already low — redundant constraint removed, faster sampling.
OPENROUTER_TOP_P = float(os.getenv("OPENROUTER_TOP_P", "1.0"))
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
# Base num_predict for normal chat. Flowchart/compare use higher limits set in llm.py.
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "600"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
# top_p=1.0 when temperature is already low — redundant constraint removed, faster sampling.
OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "1.0"))
# num_ctx 2048 for normal chat. Compare mode overrides to 4096 in llm.py.
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "2048"))
# keep_alive=-1 keeps the model loaded in RAM between requests, eliminating cold-start delay.
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "-1")
OPENROUTER_COOLDOWN_SECONDS = int(os.getenv("OPENROUTER_COOLDOWN_SECONDS", "120"))
OPENROUTER_RATE_LIMIT_COOLDOWN_SECONDS = int(os.getenv("OPENROUTER_RATE_LIMIT_COOLDOWN_SECONDS", "300"))

# ── Gemini (Google AI) ────────────────────────────────────────────────
GOOGLE_API_KEY   = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL     = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2000"))
GEMINI_TIMEOUT   = int(os.getenv("GEMINI_TIMEOUT", "60"))
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
ENABLE_GEMINI    = os.getenv("ENABLE_GEMINI", "true").lower() in ("1", "true", "yes", "on")

session = requests.Session()
openrouter_unavailable_until = 0.0
openrouter_unavailable_reason = ""


def short_error_body(response: requests.Response) -> str:
    body = response.text.strip().replace("\n", " ")
    return body[:300] if body else "no response body"


def has_openrouter_key() -> bool:
    return bool(OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here")


def ollama_enabled() -> bool:
    return ENABLE_OLLAMA_FALLBACK


def ollama_payload(prompt: str, model: str = None, options_override: dict = None) -> dict:
    options = {
        "num_predict": OLLAMA_NUM_PREDICT,
        "temperature": OLLAMA_TEMPERATURE,
        "top_p": OLLAMA_TOP_P,
        "num_ctx": OLLAMA_NUM_CTX,
    }
    if options_override:
        options.update(options_override)
    return {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": options,
    }


def openrouter_payload(model: str, prompt: str, system_message: str, stream: bool = False) -> dict:
    return {
        "model": model,
        "stream": stream,
        "temperature": OPENROUTER_TEMPERATURE,
        "top_p": OPENROUTER_TOP_P,
        "max_tokens": OPENROUTER_MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    }


def list_ollama_models() -> list[str]:
    try:
        response = session.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            print(f"Ollama model list failed with {response.status_code}: {short_error_body(response)}")
            return [OLLAMA_MODEL]
        models = response.json().get("models", [])
        names = [model.get("name") for model in models if model.get("name")]
        return names or [OLLAMA_MODEL]
    except Exception as e:
        print(f"Ollama model list failed: {str(e)}")
        return [OLLAMA_MODEL]


def list_openrouter_models() -> list[str]:
    return OPENROUTER_MODELS[:]


def resolve_openrouter_models(model: str = None) -> list[str]:
    requested = (model or "").strip()
    if not requested:
        return OPENROUTER_MODELS[:OPENROUTER_MAX_ATTEMPTS]
    # Always honour the user's explicit model choice — even if it's not in the
    # configured default list.  Falling back silently to defaults made the
    # model selector appear broken (UI showed model X, backend used model Y).
    return [requested]


def resolve_ollama_model(model: str = None) -> str:
    requested = (model or "").strip()
    if not requested:
        return OLLAMA_MODEL
    # Always honour the user's explicit model choice.
    # If it's not installed Ollama will return a clear error rather than
    # silently using a different model than what the user selected.
    return requested


def cancelled(cancel_event=None) -> bool:
    return bool(cancel_event and cancel_event.is_set())


_OPENROUTER_GARBAGE_RESPONSES = (
    "streaming had trouble",
    "trying a standard response",
    "i'm sorry, i can't",
    "i cannot fulfill",
    "i'm unable to assist",
    "as an ai, i cannot",
    "[error]",
    "something went wrong",
)


def _is_garbage_response(text: str) -> bool:
    lowered = (text or "").strip().lower()
    return any(phrase in lowered for phrase in _OPENROUTER_GARBAGE_RESPONSES)


def clean_openrouter_response(text: str) -> str:
    return str(text or "").replace("\r\n", "\n")


# ── Gemini helpers ────────────────────────────────────────────────────

def has_gemini() -> bool:
    return bool(GOOGLE_API_KEY and ENABLE_GEMINI and _GENAI_AVAILABLE)


def list_gemini_models() -> list[str]:
    if not has_gemini():
        return []
    return [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
    ]


def resolve_gemini_model(model: str = None) -> str:
    """Resolve a requested Gemini model to a valid one, falling back to the default."""
    requested = (model or "").strip()
    if not requested:
        return GEMINI_MODEL
    if requested in list_gemini_models():
        return requested
    print(f"Requested Gemini model '{requested}' is not available. Using {GEMINI_MODEL}.")
    return GEMINI_MODEL


def generate_with_gemini(
    prompt: str,
    max_tokens: int = None,
    system_message: str = "",
    cancel_event=None,
    model: str = None,
) -> str:
    """Call Gemini and return the text response. Returns empty string on failure."""
    if not has_gemini():
        return ""
    if cancelled(cancel_event):
        return ""
    selected_model = resolve_gemini_model(model)
    try:
        client = _genai.Client(api_key=GOOGLE_API_KEY)
        config = _genai_types.GenerateContentConfig(
            max_output_tokens=max_tokens or GEMINI_MAX_TOKENS,
            temperature=GEMINI_TEMPERATURE,
            system_instruction=system_message or None,
        )
        response = client.models.generate_content(
            model=selected_model,
            contents=prompt,
            config=config,
        )
        return (response.text or "").strip()
    except Exception as e:
        print(f"Gemini generation failed: {e}")
        return ""


def stream_with_gemini(
    prompt: str,
    max_tokens: int = None,
    system_message: str = "",
    cancel_event=None,
    model: str = None,
):
    """Generator that yields text chunks from Gemini streaming API."""
    if not has_gemini():
        return
    if cancelled(cancel_event):
        return
    selected_model = resolve_gemini_model(model)
    try:
        client = _genai.Client(api_key=GOOGLE_API_KEY)
        config = _genai_types.GenerateContentConfig(
            max_output_tokens=max_tokens or GEMINI_MAX_TOKENS,
            temperature=GEMINI_TEMPERATURE,
            system_instruction=system_message or None,
        )
        for chunk in client.models.generate_content_stream(
            model=selected_model,
            contents=prompt,
            config=config,
        ):
            if cancelled(cancel_event):
                return
            text = getattr(chunk, "text", "") or ""
            if text:
                yield text
    except Exception as e:
        print(f"Gemini stream failed: {e}")


def read_openrouter_stream(response: requests.Response, cancel_event=None) -> str:
    chunks = []
    for line in response.iter_lines(decode_unicode=True):
        if cancelled(cancel_event):
            response.close()
            return ""
        if not line or not line.startswith("data: "):
            continue
        raw = line[6:].strip()
        if raw == "[DONE]":
            break
        try:
            data = json.loads(raw)
            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                chunks.append(delta)
        except json.JSONDecodeError:
            continue

    result = "".join(chunks).strip()
    if _is_garbage_response(result):
        print(f"OpenRouter returned a garbage/canned response — treating as empty: {result[:120]}")
        return ""
    return result


def generate_with_ollama(prompt: str, timeout: int = None, model: str = None, cancel_event=None, options_override: dict = None) -> str:
    if cancelled(cancel_event):
        return ""

    selected_model = resolve_ollama_model(model)
    response = session.post(
        f"{OLLAMA_API_URL}/api/generate",
        json=ollama_payload(prompt, selected_model, options_override=options_override),
        timeout=timeout or OLLAMA_TIMEOUT_SECONDS,
        stream=True,
    )

    if response.status_code == 200:
        chunks = []
        for line in response.iter_lines(decode_unicode=True):
            if cancelled(cancel_event):
                response.close()
                return ""
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid Ollama stream chunk: {line[:120]}")
                continue
            if "response" in data:
                chunks.append(data["response"])
            if data.get("done"):
                break
        return "".join(chunks).strip()

    print(f"Ollama failed with {response.status_code}: {short_error_body(response)}")
    return ""


def openrouter_headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Website Chatbot",
    }


def openrouter_available() -> bool:
    if not has_openrouter_key():
        return False
    remaining = openrouter_unavailable_until - time.monotonic()
    if remaining > 0:
        print(f"Skipping OpenRouter for {remaining:.0f}s because it recently failed: {openrouter_unavailable_reason}")
        return False
    return True


def mark_openrouter_unavailable(reason: str, cooldown_seconds: int = None) -> None:
    global openrouter_unavailable_until, openrouter_unavailable_reason
    cooldown = cooldown_seconds or OPENROUTER_COOLDOWN_SECONDS
    openrouter_unavailable_until = time.monotonic() + cooldown
    openrouter_unavailable_reason = reason
    print(f"OpenRouter disabled for {cooldown}s: {reason}")


def openrouter_cooldown_reason() -> str:
    return openrouter_unavailable_reason


def should_skip_openrouter_after_response(response: requests.Response, model: str) -> bool:
    status = response.status_code
    reason = f"{model} returned {status}: {short_error_body(response)}"
    if status == 429:
        mark_openrouter_unavailable(reason, OPENROUTER_RATE_LIMIT_COOLDOWN_SECONDS)
        return True
    if status in (401, 403) or status >= 500:
        mark_openrouter_unavailable(reason)
        return True
    return False
