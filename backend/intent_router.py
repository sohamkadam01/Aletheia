"""
Hybrid Intent Router for Aletheia.

Architecture:
  User Query
       ↓
  Regex Router  (Stage 1 — fast, deterministic)
       ↓
  Matched? ─── Yes ──→ Route
       │
       No
       ↓
  LLM Router  (Stage 2 — used only when regex is insufficient)
       ↓
  Confidence Check
    >= 0.80 → Route  →  Safety Layer  →  Execution Engine
    < 0.80  → Clarification Question

Intents:
  autofill_form | workflow_steps | page_analysis | chart | flowchart
  compare | page_action | normal_chat
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Intent constants ──────────────────────────────────────────────────────────

INTENT_AUTOFILL_FORM   = "autofill_form"
INTENT_WORKFLOW_STEPS  = "workflow_steps"
INTENT_PAGE_ANALYSIS   = "page_analysis"
INTENT_CHART           = "chart"
INTENT_FLOWCHART       = "flowchart"
INTENT_COMPARE         = "compare"
INTENT_PAGE_ACTION     = "page_action"
INTENT_NORMAL_CHAT     = "normal_chat"

ALL_INTENTS = [
    INTENT_AUTOFILL_FORM,
    INTENT_WORKFLOW_STEPS,
    INTENT_PAGE_ANALYSIS,
    INTENT_CHART,
    INTENT_FLOWCHART,
    INTENT_COMPARE,
    INTENT_PAGE_ACTION,
    INTENT_NORMAL_CHAT,
]

# Confidence threshold for routing without asking for clarification.
CONFIDENCE_THRESHOLD = 0.80


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class PageContext:
    """Signals extracted from the current page that improve classification."""
    page_has_form: bool = False
    visible_inputs: int = 0
    profile_exists: bool = False
    workflow_keywords_present: bool = False
    action_keywords_present: bool = False
    current_mode: str = "website"
    page_title: str = ""
    page_summary: str = ""


@dataclass
class IntentResult:
    """The output of the router — an intent with a confidence score."""
    intent: str
    confidence: float
    router: str                       # "regex" | "llm" | "fallback"
    reason: list[str] = field(default_factory=list)
    raw_query: str = ""
    needs_clarification: bool = False
    clarification_prompt: str = ""


# ── Intent log ────────────────────────────────────────────────────────────────

_intent_log: list[dict] = []
_INTENT_LOG_MAX = 200


def _log_intent(result: IntentResult) -> None:
    """Append a routing decision to the in-memory intent log."""
    entry = {
        "query": result.raw_query[:300],
        "intent": result.intent,
        "confidence": round(result.confidence, 4),
        "router": result.router,
        "reason": result.reason,
        "final_route": result.intent,
        "needs_clarification": result.needs_clarification,
        "ts": int(time.time()),
    }
    _intent_log.append(entry)
    del _intent_log[:-_INTENT_LOG_MAX]


def get_intent_log(limit: int = 50) -> list[dict]:
    """Return recent intent routing decisions (for debugging / tuning)."""
    return _intent_log[-max(1, min(limit, _INTENT_LOG_MAX)):]


# ── Safety patterns (compiled once at import) ─────────────────────────────────

_SENSITIVE_FIELD_RE = re.compile(
    r"\b(password|confirm[\s_\-]?password|otp|one[\s_\-]time[\s_\-]password"
    r"|pin|cvv|cvc|security[\s_\-]?answer|authentication[\s_\-]?code"
    r"|2fa|two[\s_\-]?factor|secret|token|passphrase|card[\s_\-]?number"
    r"|ssn|social[\s_\-]?security|tax[\s_\-]?id)\b",
    re.IGNORECASE,
)

_SUBMISSION_ACTION_RE = re.compile(
    r"\b(submit|register|purchase|pay|delete|transfer|confirm|checkout"
    r"|buy|sign[\s_\-]?up)\b",
    re.IGNORECASE,
)

SENSITIVE_FIELD_NAMES: frozenset[str] = frozenset({
    "password", "confirm_password", "confirmpassword", "otp", "pin",
    "cvv", "cvc", "security_answer", "securityanswer", "authentication_code",
    "auth_code", "2fa", "two_factor", "secret", "token", "passphrase",
    "card_number", "cardnumber", "ssn", "tax_id",
})


# ── Stage 1: Regex Router ─────────────────────────────────────────────────────

_AUTOFILL_PATTERNS: list[str] = [
    r"\b(auto[\s\-]?fill|autofill)\b",
    r"\bfill\s+(this\s+)?(form|application|fields?)\b",
    r"\bfill\s+(it|them)\s+out\b",
    r"\bfill\s+out\s+(the|this)\s+(form|application|fields?)\b",
    r"\bfill\s+the\s+form\b",
    r"\bcomplete\s+(this\s+)?(application|form|fields?)\b",
    r"\bpopulate\s+(the\s+)?(fields?|form|inputs?)\b",
    r"\bfill\s+in\s+(the|this)\s+(form|application|fields?)\b",
    r"\bcan\s+you\s+fill\b",
    r"\bfill\s+(this|the)\s+out\b",
    # Login / Sign-in
    r"\b(log\s*me\s+in|sign\s*me\s+in|login\s+for\s+me)\b",
    r"\b(do\s+the\s+login|complete\s+the\s+login|enter\s+(my\s+)?login)\b",
    r"\bfill\s+(my\s+)?(login|sign[\s\-]?in)\s+(details?|credentials?|info)\b",
    # Registration / Sign-up
    r"\b(register\s+me|sign\s*me\s+up|create\s+(my\s+)?account)\b",
    r"\bdo\s+the\s+(registration|sign\s*up|signup)\b",
    r"\bfill\s+(my\s+)?(registration|signup|sign[\s\-]?up)\s+(details?|form|info)\b",
    r"\bcomplete\s+(my\s+)?(registration|signup|account\s+creation)\b",
    # Natural language "do it for me"
    r"\bdo\s+(the\s+)?(paperwork|forms?|entry|entries)\s+(for\s+me|on\s+my\s+behalf)?\b",
    r"\benter\s+(my\s+)?(information|info|details?|data)\s+(for\s+me|here|into\s+the\s+form)?\b",
    r"\bfill\s+(everything|all\s+(the\s+)?fields?)\s+(for\s+me|in|out)?\b",
    r"\b(help\s+me\s+fill|assist\s+(me\s+)?with\s+(filling|the\s+form|this\s+form))\b",
    r"\bput\s+(my\s+)?(details?|info|data)\s+(in|into|on)\s+(the\s+)?(form|page|fields?)\b",
    r"\buse\s+my\s+(profile|info|details?)\s+(to\s+)?(fill|complete|populate)\b",
]

_WORKFLOW_PATTERNS: list[str] = [
    r"\b(admission|application|enrollment|registration|onboarding)\s+(process|steps?|procedure|flow|guide)\b",
    r"\bhow\s+(do\s+I|can\s+I|to)\s+apply\b",
    r"\bwhat\s+are\s+the\s+steps\b",
    r"\bstep[\s\-]?by[\s\-]?step\s+(process|guide|instructions?)\b",
    r"\bprocess\s+(to|for)\s+(apply|register|enroll|submit|get)\b",
    r"\bapplication\s+steps?\b",
    r"\beligibility\s+(criteria|requirements?|conditions?)\b",
    r"\bwhat\s+(documents?|requirements?|materials?)\s+(do\s+I\s+need|are\s+required|must\s+I\s+provide)\b",
    r"\bdeadline\s+for\s+(applying|submission|registration|enrollment)\b",
    r"\bhow\s+(long|much\s+time)\s+(does\s+it|will\s+it|does\s+the\s+process)\s+take\b",
    r"\bwhat\s+is\s+the\s+(application|admission|registration)\s+process\b",
    r"\bguide\s+(me|to)\s+(through|apply|register)\b",
    r"\bwalk\s+(me\s+)?through\s+(the\s+)?(process|application|steps?)\b",
    r"\bhow\s+do\s+I\s+(get|obtain|receive)\b",
    # Login / Account process explanations
    r"\bhow\s+(do\s+I|can\s+I|to)\s+(login|log\s*in|sign\s*in)\b",
    r"\bhow\s+(do\s+I|can\s+I|to)\s+(register|sign\s*up|create\s+(an?\s+)?account)\b",
    r"\bwhat\s+is\s+the\s+(login|sign[\s\-]?in|registration|sign[\s\-]?up)\s+(process|procedure|flow)\b",
    r"\bexplain\s+(the\s+)?(login|registration|sign[\s\-]?up|sign[\s\-]?in|account\s+creation)\s+(process|procedure|steps?)?\b",
    r"\btell\s+me\s+(about|how)\s+(to\s+)?(login|register|sign\s*in|sign\s*up)\b",
    # Concept / idea explanations
    r"\bhow\s+does\s+.{0,40}(work|function|operate)\b",
    r"\bexplain\s+(how\s+)?.{0,50}(works?|functions?|operates?)\b",
    r"\bwhat\s+is\s+(the\s+)?(concept|idea|purpose|goal|flow|process)\s+of\b",
    r"\bwhat\s+does\s+.{0,40}\s+mean\b",
    r"\bcan\s+you\s+explain\b",
    r"\bbreakdown\s+(of\s+)?(the\s+)?(process|steps?|workflow|flow)\b",
    r"\bguide\s+me\s+(on|about|through)\b",
    # From-start-to-finish / general process
    r"\b(from\s+start\s+to\s+finish|end[\s\-]?to[\s\-]?end|full\s+process|complete\s+workflow|entire\s+process)\b",
    r"\bsteps?\s+(to|for|involved\s+in)\s+(the\s+)?\w+(\s+\w+){0,4}(process|flow|application|registration)?\b",
    r"\bwhat\s+happens?\s+(after|when|next|then|before)\b",
]

_PAGE_ANALYSIS_PATTERNS: list[str] = [
    r"\bsummar[iy](ze|se|y)\s+(this\s+)?(page|site|website|document|content|article|post)?\b",
    r"\bwhat\s+is\s+this\s+(page|site|website|document|article|about)\b",
    r"\bwhat\s+(documents?|requirements?)\s+are\s+(required|needed|listed|mentioned)\b",
    r"\bkey\s+(takeaways?|points?|information|details?|findings?)\b",
    r"\bhighlight\s+(the\s+)?(important|key|main|critical)\b",
    r"\bextract\s+(the\s+)?(information|requirements?|details?|data)\b",
    r"\bwhat\s+(is|does)\s+this\s+(page|site|form|document)\s+(say|contain|about|cover)\b",
    r"\bdeadlines?\s+(on|in|from|mentioned\s+on)\s+this\b",
    r"\bidentify\s+(the\s+)?(requirements?|documents?|deadlines?|dates?|fees?)\b",
    r"\boverview\s+of\s+(this|the)\b",
    r"\bwhat\s+information\s+(is|can\s+I\s+find)\s+(on|in|here|this)\b",
    r"\banalyze\s+(this\s+)?(page|document|content|site)\b",
    r"\bwhat\s+(fees?|costs?|charges?|prices?|amounts?)\s+(are|is|do)\b",
]

_CHART_PATTERNS: list[str] = [
    r"\b(create|make|generate|show|draw|plot|build|give\s+me\s+a)\s+(a\s+)?chart\b",
    r"\b(create|make|generate|show|draw|plot|build)\s+(a\s+)?graph\b",
    r"\b(bar|pie|line|donut|radar|horizontal|scatter)\s+(chart|graph)\b",
    r"\bvisuali[sz]e\s+(the\s+)?(data|numbers|statistics|stats|metrics|values)\b",
    r"\bdata\s+(chart|graph|visualization|viz)\b",
    r"\bshow\s+(me\s+)?(the\s+)?(data|numbers|statistics|stats|metrics)\s+(as\s+a\s+)?(chart|graph|visual)\b",
    r"\bplot\s+(the\s+)?(data|numbers|values|distribution)\b",
]

_FLOWCHART_PATTERNS: list[str] = [
    r"\b(create|make|generate|show|draw|build)\s+(a\s+)?flowchart\b",
    r"\bflow[\s\-]?chart\b",
    r"\bflow[\s\-]?diagram\b",
    r"\bprocess[\s\-]?(diagram|map|flow)\b",
    r"\bdecision[\s\-]?tree\b",
    r"\barchitecture\s+(diagram|flow|map)\b",
    r"\bsystem\s+(diagram|map|flow)\b",
    r"\bmind[\s\-]?map\b",
    r"\b(draw|create|make|show)\s+(a\s+)?(diagram|process\s+map|dependency\s+map|concept\s+map)\b",
    r"\bvisuali[sz]e\s+(the\s+)?(flow|process|steps?|workflow|pipeline)\b",
    r"\bdependency\s+(graph|map|diagram)\b",
    r"\bdiagram\s+(this|the|these)\b",
]

_COMPARE_PATTERNS: list[str] = [
    r"\bcompare\s+(this\s+)?(page|document|site|with|to|against)\b",
    r"\bcompar(e|ison)\b.*\b(document|resume|cv|file|pdf|page)\b",
    r"\bhow\s+(does|do)\s+(it|this)\s+compare\b",
    r"\bdifference(s?)\s+between\b",
    r"\b\bvs\.?\s+\b",
    r"\bcheck\s+(my\s+)?(resume|cv|document|profile)\s+(against|with|vs\.?|versus)\b",
    r"\bmatch\s+(my\s+)?(resume|cv|document|profile)\s+(against|with|to|versus)\b",
    r"\bhow\s+well\s+(does|do)\s+(my|the)\b",
    r"\bcompare\s+(the\s+two|both)\b",
    r"\bside[\s\-]?by[\s\-]?side\s+(comparison|compare)\b",
]

_PAGE_ACTION_PATTERNS: list[str] = [
    r"\b(open|click|tap|press)\s+(the\s+)?(menu|button|link|tab|icon|dropdown)\b",
    r"\bnavigate\s+(to|back|forward|away|next|previous)\b",
    r"\bscroll\s+(to|down|up|top|bottom)\b",
    r"\bgo\s+to\s+(the\s+)?(next|previous|top|bottom|home|main)\b",
    r"\b(close|dismiss|hide|toggle)\s+(the\s+)?(modal|popup|dialog|overlay|menu|drawer)\b",
    r"\bclick\s+on\s+(the\s+)?\b",
    r"\bselect\s+(the\s+)?(dropdown|option|menu|item)\b",
]


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Intent → (compiled patterns, base confidence). Ordered by specificity.
# More specific intents are listed first so they win in ambiguous overlap.
_REGEX_RULES: list[tuple[str, list[re.Pattern], float]] = [
    (INTENT_FLOWCHART,      _compile(_FLOWCHART_PATTERNS),    0.95),
    (INTENT_AUTOFILL_FORM,  _compile(_AUTOFILL_PATTERNS),     0.95),
    (INTENT_CHART,          _compile(_CHART_PATTERNS),         0.95),
    (INTENT_PAGE_ACTION,    _compile(_PAGE_ACTION_PATTERNS),   0.90),
    (INTENT_COMPARE,        _compile(_COMPARE_PATTERNS),       0.90),
    (INTENT_WORKFLOW_STEPS, _compile(_WORKFLOW_PATTERNS),      0.88),
    (INTENT_PAGE_ANALYSIS,  _compile(_PAGE_ANALYSIS_PATTERNS), 0.88),
]


def regex_route(query: str) -> Optional[IntentResult]:
    """
    Stage 1 — deterministic regex matching.

    Returns an IntentResult if a high-confidence match is found, else None.
    Fast: no LLM calls, no I/O.
    """
    normalized = query.strip()
    for intent, patterns, confidence in _REGEX_RULES:
        for pat in patterns:
            if pat.search(normalized):
                return IntentResult(
                    intent=intent,
                    confidence=confidence,
                    router="regex",
                    reason=[f"regex:{pat.pattern[:80]}"],
                    raw_query=query,
                )
    return None


# ── Stage 2: LLM Router ───────────────────────────────────────────────────────

def build_llm_router_prompt(query: str, context: PageContext) -> str:
    """Build the prompt that asks the LLM to classify intent."""
    return f"""You are an intent classifier for a web assistant called Aletheia.
Classify the user's query into exactly ONE intent from this list:

  autofill_form    – user wants to fill / autofill a form on the current page
  workflow_steps   – user wants a step-by-step process, requirements, or eligibility
  page_analysis    – user wants a summary, overview, key info, or extraction from this page
  chart            – user wants a data chart or graph
  flowchart        – user wants a flow diagram or process diagram
  compare          – user wants to compare this page/document with another source
  page_action      – user wants to navigate, click, scroll, or interact with the page UI
  normal_chat      – general question, greeting, or unrelated conversation

Page context signals (use these to resolve ambiguity):
  page_has_form: {context.page_has_form}
  visible_inputs: {context.visible_inputs}
  profile_exists: {context.profile_exists}
  workflow_keywords_present: {context.workflow_keywords_present}
  action_keywords_present: {context.action_keywords_present}
  current_mode: {context.current_mode}
  page_title: "{context.page_title or 'unknown'}"
  page_summary: "{(context.page_summary or '')[:300]}"

User query: "{query}"

Guidance:
- If the page has a form AND profile exists AND the user is asking the assistant to do the task or fill credentials/details (e.g. "log me in", "sign me in", "register me", "sign me up", "create my account", "fill my login", "complete registration") -> autofill_form
- Login/registration action phrases map to autofill_form when the user asks to perform the action: login, log in, sign in, register, registration, sign up, signup, create account, create my account.
- Explanations of concepts, ideas, or processes map to workflow_steps, even when not phrased with the exact word "workflow".
- Questions like "how do I create an account?", "how do I log in?", "what is the registration process?", "explain sign up", "walk me through login", or "tell me how registration works" -> workflow_steps
- If the query is broad ("help me with this application") and ambiguous -> low confidence
- Only return high confidence (>= 0.80) when the intent is unambiguous

Reply with ONLY a raw JSON object -- no markdown, no explanation:
{{
  "intent": "<one of the listed intents>",
  "confidence": <float 0.0-1.0>,
  "reason": ["<signal 1>", "<signal 2>"]
}}"""


def llm_route(
    query: str,
    context: PageContext,
    generate_fn,
    *,
    force_provider: str = "",
    ollama_model: str = "",
    openrouter_model: str = "",
    gemini_model: str = "",
) -> IntentResult:
    """
    Stage 2 — LLM-based intent classification.

    Only called when the regex router found no match.
    Uses a minimal prompt for low latency.
    """
    prompt = build_llm_router_prompt(query, context)
    try:
        llm_result = generate_fn(
            context=prompt,
            question="Classify the user query into exactly one intent. Reply with ONLY the JSON object.",
            history=None,
            force_provider=force_provider or "",
            ollama_model=ollama_model or "",
            openrouter_model=openrouter_model or "",
            gemini_model=gemini_model or "",
            concise_answer=True,
        )
        raw = (llm_result.get("answer") or "").strip()

        # Extract JSON even if the model added surrounding text
        json_match = re.search(r"\{[\s\S]*?\}", raw)
        if not json_match:
            raise ValueError(f"No JSON found in LLM router response: {raw[:200]}")

        data = json.loads(json_match.group(0))
        intent = str(data.get("intent", INTENT_NORMAL_CHAT)).strip()
        confidence = float(data.get("confidence", 0.5))
        reason = list(data.get("reason", []))

        # Sanitise
        if intent not in ALL_INTENTS:
            intent = INTENT_NORMAL_CHAT
            confidence = 0.5
            reason.append("unknown_intent_normalised")

        confidence = max(0.0, min(1.0, confidence))

        return IntentResult(
            intent=intent,
            confidence=confidence,
            router="llm",
            reason=reason,
            raw_query=query,
        )
    except Exception as exc:
        print(f"[IntentRouter] LLM router error: {exc}")
        return IntentResult(
            intent=INTENT_NORMAL_CHAT,
            confidence=0.5,
            router="fallback",
            reason=[f"llm_error:{str(exc)[:100]}"],
            raw_query=query,
        )


# ── Clarification templates ───────────────────────────────────────────────────

_CLARIFICATION_TEMPLATES: dict[frozenset, str] = {
    frozenset({INTENT_AUTOFILL_FORM, INTENT_WORKFLOW_STEPS}): (
        "I can help you in a couple of ways — which would you prefer?\n\n"
        "- **Explain the application process** step by step\n"
        "- **Autofill the form** on this page using your profile"
    ),
    frozenset({INTENT_PAGE_ANALYSIS, INTENT_WORKFLOW_STEPS}): (
        "I'm not sure what you'd like me to do. Could you clarify?\n\n"
        "- **Summarize this page** — give you a quick overview\n"
        "- **Explain the process** — step-by-step guide with requirements"
    ),
    frozenset({INTENT_AUTOFILL_FORM, INTENT_PAGE_ANALYSIS}): (
        "Did you want me to:\n\n"
        "- **Analyze this page** — summarize requirements and key info\n"
        "- **Autofill the form** — map your profile to the form fields"
    ),
}

_DEFAULT_CLARIFICATION = (
    "I want to make sure I help you correctly. Could you be more specific?\n\n"
    "I can:\n"
    "- **Summarize or analyze** this page\n"
    "- **Explain the process** step by step\n"
    "- **Autofill the form** using your profile\n"
    "- **Answer a question** about this page\n"
    "- **Create a chart or diagram** from page content"
)


def _clarification_for(primary: str, secondary: str) -> str:
    key = frozenset({primary, secondary})
    return _CLARIFICATION_TEMPLATES.get(key, _DEFAULT_CLARIFICATION)


# ── Hybrid Router ─────────────────────────────────────────────────────────────

def route(
    query: str,
    context: Optional[PageContext] = None,
    generate_fn=None,
    *,
    force_provider: str = "",
    ollama_model: str = "",
    openrouter_model: str = "",
    gemini_model: str = "",
    skip_llm: bool = False,
) -> IntentResult:
    """
    Hybrid router entry point.

    1. Try the regex router (fast, deterministic, zero cost).
    2. If no regex match AND generate_fn is available, try LLM router.
    3. Apply confidence threshold:
       - >= 0.80 → route to intent
       - < 0.80  → set needs_clarification = True

    Args:
        query:          The user's raw query string.
        context:        Page-level signals (form presence, inputs, etc.).
        generate_fn:    LLM generate function from llm.py (optional).
        skip_llm:       Skip Stage 2 entirely (for offline/test scenarios).
        force_provider / ollama_model / openrouter_model / gemini_model:
                        Provider selection forwarded to the LLM router.

    Returns:
        IntentResult with intent, confidence, router used, and optional
        clarification prompt.
    """
    ctx = context or PageContext()

    # Stage 1 ── Regex Router
    regex_result = regex_route(query)
    if regex_result is not None:
        _log_intent(regex_result)
        return regex_result

    # Stage 2 ── LLM Router
    if generate_fn and not skip_llm:
        llm_result = llm_route(
            query,
            ctx,
            generate_fn,
            force_provider=force_provider,
            ollama_model=ollama_model,
            openrouter_model=openrouter_model,
            gemini_model=gemini_model,
        )

        if llm_result.confidence >= CONFIDENCE_THRESHOLD:
            _log_intent(llm_result)
            return llm_result

        # Low confidence — flag for clarification
        llm_result.needs_clarification = True
        llm_result.clarification_prompt = _clarification_for(
            llm_result.intent, INTENT_NORMAL_CHAT
        )
        _log_intent(llm_result)
        return llm_result

    # Fallback — no regex match, no LLM available
    fallback = IntentResult(
        intent=INTENT_NORMAL_CHAT,
        confidence=0.70,
        router="fallback",
        reason=["no_regex_match", "llm_not_available" if not generate_fn else "skip_llm_set"],
        raw_query=query,
    )
    _log_intent(fallback)
    return fallback


# ── Safety Layer ──────────────────────────────────────────────────────────────

def safety_check_autofill(actions: list[dict]) -> dict:
    """
    Validate a list of autofill action-plan entries through the safety layer.

    Blocks:
      - Submission-type actions (submit, pay, register, …)
      - Sensitive field targets (password, OTP, CVV, PIN, …)

    Flags (does not block, but marks for user review):
      - Actions with confidence < 0.70

    Returns:
        {
            "safe":       bool   — True if no hard blocks,
            "allowed":    list   — actions that passed,
            "blocked":    list   — actions that were removed,
            "violations": list   — human-readable reasons for blocks,
            "review":     list   — allowed actions flagged for user review,
        }
    """
    allowed: list[dict] = []
    blocked: list[dict] = []
    review: list[dict] = []
    violations: list[str] = []

    for action in actions:
        action_type = (action.get("type") or "").lower().strip()
        field_raw = (action.get("field") or "").lower()
        field_key = re.sub(r"[\s\-]", "_", field_raw)
        confidence = float(action.get("confidence") or 0.0)

        # ── Hard block: submission actions ──
        if _SUBMISSION_ACTION_RE.search(action_type):
            blocked.append(action)
            violations.append(f"submission_action_blocked:{action_type}")
            continue

        # ── Hard block: sensitive field names (regex) ──
        if _SENSITIVE_FIELD_RE.search(field_raw):
            blocked.append(action)
            violations.append(f"sensitive_field_blocked:{field_raw[:50]}")
            continue

        # ── Hard block: exact sensitive field names ──
        if field_key in SENSITIVE_FIELD_NAMES:
            blocked.append(action)
            violations.append(f"sensitive_field_name_blocked:{field_key}")
            continue

        # ── Soft flag: low confidence → user must review ──
        if confidence < 0.70:
            flagged = dict(action)
            flagged["_needs_review"] = True
            flagged["_review_reason"] = f"low_confidence:{confidence:.2f}"
            allowed.append(flagged)
            review.append(flagged)
            continue

        allowed.append(action)

    return {
        "safe": len(blocked) == 0,
        "allowed": allowed,
        "blocked": blocked,
        "violations": violations,
        "review": review,
    }


def safety_check_intent(result: IntentResult) -> dict:
    """
    Top-level safety gate — called before any intent is executed.

    Rules:
      - Confidence < 0.70 → block (do not auto-execute, require user review)
      - All other intents → pass (inner engines have their own safety checks)

    Returns:
        {"ok": bool, "reason": str, "result": IntentResult}
    """
    if result.confidence < 0.70:
        return {"ok": False, "reason": "confidence_below_minimum", "result": result}

    return {"ok": True, "reason": "", "result": result}
