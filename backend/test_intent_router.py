"""Quick smoke-test for the Hybrid Intent Router."""
import intent_router as ir

CASES = [
    ("autofill this form",           ir.INTENT_AUTOFILL_FORM),
    ("fill out the application",      ir.INTENT_AUTOFILL_FORM),
    ("can you fill this out",         ir.INTENT_AUTOFILL_FORM),
    ("fill in the form",              ir.INTENT_AUTOFILL_FORM),
    ("create a flowchart",            ir.INTENT_FLOWCHART),
    ("flow diagram of the process",   ir.INTENT_FLOWCHART),
    ("draw a diagram",                ir.INTENT_FLOWCHART),
    ("show me a bar chart",           ir.INTENT_CHART),
    ("visualize the data",            ir.INTENT_CHART),
    ("how do I apply",                ir.INTENT_WORKFLOW_STEPS),
    ("what are the steps",            ir.INTENT_WORKFLOW_STEPS),
    ("what documents are required",   ir.INTENT_WORKFLOW_STEPS),
    ("eligibility criteria",          ir.INTENT_WORKFLOW_STEPS),
    ("summarize this page",           ir.INTENT_PAGE_ANALYSIS),
    ("what is this page about",       ir.INTENT_PAGE_ANALYSIS),
    ("identify the deadlines",        ir.INTENT_PAGE_ANALYSIS),
    ("compare this with my resume",   ir.INTENT_COMPARE),
    ("differences between the two",   ir.INTENT_COMPARE),
    ("click the menu",                ir.INTENT_PAGE_ACTION),
    ("scroll to the top",             ir.INTENT_PAGE_ACTION),
    ("hello how are you",             None),   # no regex match
    ("who created this website",      None),   # no regex match
]

passed = failed = 0
for query, expected in CASES:
    result = ir.regex_route(query)
    got = result.intent if result else None
    ok = (got == expected)
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {query!r:50s}  expected={expected}  got={got}")

print(f"\nRegex routing: {passed}/{passed+failed} passed")

# ── Safety layer ─────────────────────────────────────────────────────────────
actions = [
    {"type": "fill", "field": "Email", "value": "test@test.com", "confidence": 0.95},
    {"type": "fill", "field": "password", "value": "secret",       "confidence": 0.95},
    {"type": "fill", "field": "OTP",      "value": "123456",       "confidence": 0.95},
    {"type": "submit","field": "Submit",   "value": "",             "confidence": 0.99},
    {"type": "fill", "field": "Name",     "value": "John",         "confidence": 0.45},
]
safety = ir.safety_check_autofill(actions)
allowed_fields = [a["field"] for a in safety["allowed"]]
blocked_fields = [a["field"] for a in safety["blocked"]]
review_fields  = [a["field"] for a in safety["review"]]

print(f"\nSafety check:")
print(f"  allowed   = {allowed_fields}")
print(f"  blocked   = {blocked_fields}")
print(f"  review    = {review_fields}")
print(f"  violations= {safety['violations']}")

# Validate expectations
assert "Email" in allowed_fields,   "Email should be allowed"
assert "password" in blocked_fields, "password must be blocked"
assert "OTP" in blocked_fields,      "OTP must be blocked"
assert "Submit" in blocked_fields,   "Submit (submission action) must be blocked"
assert "Name" in review_fields,      "Name with low confidence must be flagged for review"
print("\nSafety assertions passed.")

# ── intent_check_intent ───────────────────────────────────────────────────────
low_conf = ir.IntentResult(intent=ir.INTENT_AUTOFILL_FORM, confidence=0.60, router="llm")
assert not ir.safety_check_intent(low_conf)["ok"], "Low confidence should block"
high_conf = ir.IntentResult(intent=ir.INTENT_AUTOFILL_FORM, confidence=0.95, router="regex")
assert ir.safety_check_intent(high_conf)["ok"], "High confidence should pass"
print("Intent safety assertions passed.\n")
