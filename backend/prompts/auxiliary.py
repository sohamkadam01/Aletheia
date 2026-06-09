def _history_block(history: list[dict] | None, max_turns: int = 4) -> str:
    if not history:
        return ""

    lines = ["Conversation history:"]
    for msg in history[-max_turns:]:
        role = "User" if msg.get("sender") == "user" else "Assistant"
        lines.append(f"{role}: {msg.get('text')}")
    return "\n".join(lines) + "\n"


def build_suggestions_prompt(context: str, question: str, answer: str, history: list[dict] | None = None) -> str:
    history_str = _history_block(history, max_turns=4)
    return f"""
Based on the webpage context and the recent conversation below, suggest 3 concise follow-up questions the user might want to ask next.

{history_str}
Webpage context:
{context[:2000]}

Last Question: {question}
Last Answer: {answer}

Rules for suggestions:
1. Be very concise (max 6 words per question).
2. Ensure they are directly relevant to the current page content.
3. Vary the questions: one should be a deeper dive, one should be a related topic, and one should be a common user goal (like "How to contact?" or "See pricing").
4. Return ONLY the 3 questions, one per line. No numbers, no extra text.

Suggestions:
"""


def build_starter_questions_prompt(context: str, page_title: str = "") -> str:
    return f"""
Create exactly 3 starter questions a user should ask about this specific webpage.

Page title:
{page_title or "Unknown"}

Webpage context:
{context[:2500]}

Rules:
1. Each question must be directly grounded in the webpage context.
2. Do not use generic questions like "Summarize this page" unless the page context is too weak.
3. Mention specific topics, products, services, pricing, contact, policies, features, or actions from the page when available.
4. Keep each question under 9 words.
5. Return ONLY the 3 questions, one per line. No numbers, no extra text.

Starter questions:
"""


def build_safety_prompt(url: str, content_summary: str) -> str:
    return f"""
Analyze the safety and genuineness of the following website.
Look for signs of phishing, scams, deceptive practices, or suspicious domain patterns.

URL: {url}
Content Summary: {content_summary[:1500]}

Rules for analysis:
1. Is the domain suspicious? (e.g., misspellings of famous brands, strange TLDs like .xyz for a "bank").
2. Is the content asking for sensitive info in a suspicious way?
3. Does it promise unrealistic rewards?
4. Is it a well-known, high-trust domain? (e.g., google.com, github.com, official gov/edu sites).

Return a JSON-like response with exactly two fields:
"status": "safe" (if legitimate and trustworthy), "warning" (if suspicious or unverified), or "harmful" (if clearly malicious/phishing).
"reason": A very brief explanation (max 15 words) for the user.

Result:
"""


def build_external_search_check_prompt(context: str, question: str) -> str:
    return f"""
Can you answer the following question accurately and completely using ONLY the provided webpage context?
Reply with exactly one word: YES or NO.

Webpage Context:
{context[:1500]}

Question: {question}

Sufficient context?
"""
