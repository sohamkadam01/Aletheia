import os
import sys
import json
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from handlers.compare_chat import (
    _doc_type,
    _get_schema_description,
    build_intelligent_comparison_framework,
    _extract_both_structures,
    _semantic_evidence_for_dimension,
    _embed_units,
    _cosine_similarity
)
import handlers.compare_cache as compare_cache
from handlers import compare_tool


def _assert_compare_rows_are_grounded(rows):
    assert rows, "Expected comparison rows"
    for row in rows:
        assert row.get("dimension"), f"Row missing dimension: {row}"
        assert "source_a_evidence" in row, f"Row missing Source A evidence: {row}"
        assert "source_b_evidence" in row, f"Row missing Source B evidence: {row}"
        assert row.get("status") in compare_tool.ALLOWED_ROW_STATUSES, f"Unexpected status: {row}"
        assert row.get("match_quality") in compare_tool.ALLOWED_MATCH_QUALITIES, f"Unexpected match quality: {row}"
        assert row.get("reason"), f"Row missing reason: {row}"


def _statuses(result):
    return {row["status"] for row in result["comparison_table"]}


def _row_for(result, dimension):
    for row in result["comparison_table"]:
        if row["dimension"] == dimension:
            return row
    raise AssertionError(f"Missing comparison row: {dimension}")


def test_compare_tool_cases():
    print("Starting Dedicated Compare Tool Deterministic Tests...\n")

    # 1. Resume vs Job Description
    print("Compare Tool Test 1: Resume vs Job Description")
    resume_facts = {
        "skills": ["Python", "React", "FastAPI"],
        "experience_years": 4,
        "experience": {"summary": "Built APIs and dashboards for SaaS products."},
        "projects": ["React analytics dashboard", "FastAPI backend service"],
        "education": ["BS Computer Science"],
        "certifications": [],
    }
    job_facts = {
        "required_skills": ["Python", "React", "SQL"],
        "preferred_skills": ["FastAPI"],
        "required_experience": {"years_number": 3, "summary": "3+ years building APIs."},
        "responsibilities": ["Build APIs", "Create dashboards"],
        "required_education": ["BS Computer Science"],
        "required_certifications": ["AWS Certified"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(resume_facts, job_facts)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert "Partial Match" in _statuses(result), "Expected partial skill/responsibility matches"
    assert "Missing From A" in _statuses(result), "Expected missing certification from resume"
    assert "score_details" in result and "calculation" in result["score_details"], "Score must be explainable"
    skills_row = _row_for(result, "Skills vs Required Skills")
    assert "Python" in skills_row["source_a_evidence"] and "Python" in skills_row["source_b_evidence"], "Expected Python evidence on both sides"
    assert "SQL" not in skills_row["source_a_evidence"], "Source B requirement leaked into Source A evidence"
    assert skills_row["match_quality"] in {"Partial", "Good", "Excellent", "Perfect"}, f"Expected role-fit quality label, got {skills_row}"
    assert _row_for(result, "Required Skill: Python")["status"] == "Match", "Expected individual Python requirement row"
    assert _row_for(result, "Required Skill: SQL")["status"] == "Missing From A", "Expected individual SQL gap row"
    print("-> Resume vs JD tests PASSED\n")

    print("Compare Tool Test 1b: Role Fit Extras Are Not Conflicts")
    resume_with_extra_exp = {
        "skills": ["Python"],
        "experience_years": 1,
        "experience": {"summary": "1 year building Python APIs."},
        "projects": ["Python API"],
        "education": ["BS Computer Science"],
        "certifications": ["Azure Fundamentals"],
    }
    jd_without_exp_requirement = {
        "required_skills": ["Python"],
        "preferred_skills": [],
        "required_experience": {"years_number": 0, "summary": "No minimum years stated."},
        "responsibilities": ["Build Python APIs"],
        "required_education": [],
        "required_certifications": [],
    }
    result = compare_tool.pass_2_compare_extracted_facts(resume_with_extra_exp, jd_without_exp_requirement)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    exp_row = _row_for(result, "Experience Years vs Required Experience")
    assert exp_row["status"] == "Extra In A", f"Expected extra experience, got {exp_row}"
    assert exp_row["impact"] == "positive", f"Expected positive impact, got {exp_row}"
    assert exp_row["match_quality"] == "Good", f"Expected good extra evidence quality, got {exp_row}"
    assert "Conflict" not in _statuses(result), "Resume extras must not become role-fit conflicts"
    assert result["score_details"].get("comparison_strategy") == "role_fit_asymmetric", "Expected role-fit strategy"
    print("-> Role fit extra evidence tests PASSED\n")

    print("Compare Tool Test 1c: Role Fit Goal Forces Recruiter-Style Comparison")
    resume_text = """
    Candidate Resume
    B.Tech Computer Science. Skills: SQL, MySQL, PostgreSQL, Excel, PowerPoint.
    Teaching assistant with strong communication and team leadership experience.
    Built anomaly detection and monitoring projects. Streamlined workflows by 40%.
    """
    operations_role_text = """
    Role: Investigation Specialist
    Basic qualifications: Bachelor's degree, fluent English, Microsoft Office, SQL.
    Responsibilities include pattern identification, process improvement, data-driven
    investigation, quality audit, root cause analysis, SLA tracking, and stakeholder
    communication. Candidate must be open to 24x7 rotational shift and relocation to
    Bangalore or Hyderabad.
    """
    payload = compare_tool.build_compare_tool_payload(
        resume_text,
        operations_role_text,
        compare_goal="Role fit",
        labels={"a": "Resume", "b": "Role Page"},
    )
    result = payload["result"]
    assert result["document_types"]["a"] == "Resume / CV", f"Expected Source A resume type, got {result['document_types']}"
    assert result["document_types"]["b"] == "Job Description", f"Expected Source B job type, got {result['document_types']}"
    assert result["score_details"].get("comparison_strategy") == "role_fit_asymmetric", "Role fit goal should use recruiter-style comparison"
    assert result["type_resolution"].get("goal_aware") is True, "Expected goal-aware type resolution"
    assert "Conflict" not in _statuses(result), "Role-fit extras or unstated resume fields should not become generic conflicts"
    assert result.get("final_decision") in {"Apply", "Apply with caution", "Skip"}, f"Expected final decision guidance, got {result.get('final_decision')}"
    assert result.get("decision_reason"), "Expected decision reason"
    assert any(row["dimension"] == "Required Skill: SQL" for row in result["comparison_table"]), "Expected requirement-by-requirement SQL row"
    assert any(row["dimension"].startswith("Requirement:") for row in result["comparison_table"]), "Expected requirement/responsibility-level rows"
    improvements = result.get("resume_improvements") or {}
    assert isinstance(improvements.get("missing_keywords"), list), f"Expected missing keyword suggestions, got {improvements}"
    assert isinstance(improvements.get("what_to_add"), list), f"Expected what-to-add suggestions, got {improvements}"
    assert improvements.get("cover_letter_line"), f"Expected cover letter line, got {improvements}"
    print("-> Goal-aware role fit tests PASSED\n")

    # 2. Product A vs Product B
    print("Compare Tool Test 2: Product A vs Product B")
    product_a = {
        "features": ["Live chat", "Analytics dashboard", "Export CSV"],
        "payments": ["$29 per month"],
        "risks": ["No SSO"],
    }
    product_b = {
        "features": ["Live chat", "Analytics dashboard", "SSO"],
        "payments": ["$49 per month"],
        "risks": ["No CSV export"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(product_a, product_b)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert _row_for(result, "Features")["status"] in {"Partial Match", "Match"}, "Expected feature overlap"
    assert _row_for(result, "Payments")["status"] in {"Partial Match", "Conflict"}, "Expected pricing comparison"
    print("-> Product comparison tests PASSED\n")

    # 3. Policy A vs Policy B
    print("Compare Tool Test 3: Policy A vs Policy B")
    policy_a = {
        "obligations": ["Users must keep passwords private", "Admins review access quarterly"],
        "deadlines": ["Access review every 90 days"],
        "risks": ["Account suspension for misuse"],
    }
    policy_b = {
        "obligations": ["Users must keep passwords private", "Admins review access annually"],
        "deadlines": ["Access review every 12 months"],
        "risks": ["Account suspension for misuse"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(policy_a, policy_b)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert _row_for(result, "Obligations")["status"] in {"Partial Match", "Match"}, "Expected policy obligation overlap"
    assert _row_for(result, "Deadlines")["status"] in {"Partial Match", "Conflict"}, "Expected deadline difference"
    print("-> Policy comparison tests PASSED\n")

    # 4. Contract vs Contract
    print("Compare Tool Test 4: Contract vs Contract")
    contract_a = {
        "obligations": ["Vendor shall deliver reports monthly"],
        "payments": ["Payment due within 30 days"],
        "deadlines": ["Contract expires Dec 31 2026"],
    }
    contract_b = {
        "obligations": ["Vendor shall deliver reports monthly"],
        "payments": ["Payment due within 15 days"],
        "deadlines": ["Contract expires Dec 31 2026"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(contract_a, contract_b)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert _row_for(result, "Obligations")["status"] == "Match", "Expected matching contract obligation"
    assert _row_for(result, "Payments")["status"] in {"Partial Match", "Conflict"}, "Expected payment term difference"
    print("-> Contract comparison tests PASSED\n")

    # 5. Document vs Webpage
    print("Compare Tool Test 5: Document vs Webpage")
    document_facts = {
        "objectives": ["Apply for backend engineer role"],
        "claims": ["Candidate knows Python", "Candidate built APIs"],
    }
    webpage_facts = {
        "objectives": ["Hire backend engineer"],
        "claims": ["Role requires Python", "Role requires API development"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(document_facts, webpage_facts)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert result["score_details"]["applicable_rows"] >= 1, "Expected comparable document/webpage rows"
    print("-> Document vs webpage tests PASSED\n")

    # 6. Missing second source
    print("Compare Tool Test 6: Missing second source")
    try:
        compare_tool.run_compare_tool("Document A has enough readable text for validation.", "", "General comparison")
        raise AssertionError("Expected missing second source to raise ValueError")
    except ValueError as exc:
        assert "Document B" in str(exc), f"Expected Document B validation error, got {exc}"
    print("-> Missing second source tests PASSED\n")

    # 7. Very different document types
    print("Compare Tool Test 7: Very Different Document Types")
    resume_like = {
        "skills": ["Python", "React"],
        "experience_years": 2,
        "education": ["BS CS"],
    }
    refund_policy = {
        "obligations": ["Refund requests must be made within 14 days"],
        "payments": ["Refund fee is $10"],
        "risks": ["No refunds after 14 days"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(resume_like, refund_policy)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert {"Extra In A", "Extra In B"} & _statuses(result), "Expected extras for very different document types"
    print("-> Different document type tests PASSED\n")

    # 8. Same facts written differently
    print("Compare Tool Test 8: Same Facts Written Differently")
    source_a = {"features": ["Single sign-on", "CSV export", "Audit logs"]}
    source_b = {"features": ["SSO login", "Export CSV files", "Audit log history"]}
    result = compare_tool.pass_2_compare_extracted_facts(source_a, source_b)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert _row_for(result, "Features")["status"] in {"Match", "Partial Match"}, "Expected semantically similar feature wording to align at least partially"
    print("-> Same facts different wording tests PASSED\n")

    # 9. Conflicting dates/prices/requirements
    print("Compare Tool Test 9: Conflicting Dates, Prices, Requirements")
    source_a = {
        "deadlines": ["Launch date January 1 2027"],
        "payments": ["Price $99 per user"],
        "claims": ["Requires 2 years experience"],
    }
    source_b = {
        "deadlines": ["Launch date March 15 2027"],
        "payments": ["Price $149 per user"],
        "claims": ["Requires 5 years experience"],
    }
    result = compare_tool.pass_2_compare_extracted_facts(source_a, source_b)
    _assert_compare_rows_are_grounded(result["comparison_table"])
    assert "Conflict" in _statuses(result) or "Partial Match" in _statuses(result), "Expected conflicts or partial matches for differing values"
    for row in result["comparison_table"]:
        assert "source_a_evidence" in row and "source_b_evidence" in row, "Every row must carry both evidence fields"
    print("-> Conflict detection tests PASSED\n")

    print("ALL DEDICATED COMPARE TOOL TESTS PASSED!\n")

def test_pipeline():
    print("Starting Compare Mode Optimization Unit Tests...\n")
    
    # 1. Test Document Classification
    print("Test 1: Document Classification")
    resume_text = "John Doe. Senior Software Engineer. Experience: Python, Java, React. Education: BS Computer Science."
    jd_text = "Job Description: We are hiring a Senior Software Engineer. Requirements: Python, React, BS in CS."
    jd_with_resume_words = """
    Role: Catalog Quality Associate
    Basic qualifications: Bachelor's degree, fluent English, Microsoft Office, SQL.
    Responsibilities include quality audits, pattern identification, process improvement,
    data-driven investigation, and stakeholder communication. Preferred skills include
    Excel analytics and root cause analysis. Education and certifications are reviewed
    as part of eligibility. Candidate must support rotational shifts and relocation.
    """
    contract_text = "This Agreement is made on this day. The party shall pay the cost and be liable for breaches."
    
    type_resume = _doc_type(resume_text)
    type_jd = _doc_type(jd_text)
    type_jd_with_resume_words = _doc_type(jd_with_resume_words)
    type_contract = _doc_type(contract_text)
    
    assert type_resume == "Resume / CV", f"Expected Resume / CV, got {type_resume}"
    assert type_jd == "Job Description", f"Expected Job Description, got {type_jd}"
    assert type_jd_with_resume_words == "Job Description", f"JD with skills/education words should not be Resume / CV, got {type_jd_with_resume_words}"
    assert type_contract in ("Contract", "Policy Document"), f"Expected Contract or Policy Document, got {type_contract}"
    print("-> Document Classification tests PASSED\n")

    # 2. Test Cache Store and Retrieve
    print("Test 2: Structure Caching")
    test_text = "Unique content text for caching test " + str(time.time())
    test_struct = {"test_key": "test_value"}
    
    # Retrieve non-existent
    assert compare_cache.get_cached_structure(test_text) is None, "Cache hit on non-existent content"
    
    # Store and retrieve
    compare_cache.store_cached_structure(test_text, test_struct)
    cached = compare_cache.get_cached_structure(test_text)
    assert cached == test_struct, f"Cache retrieval failed, expected {test_struct}, got {cached}"
    print("-> Structure Caching tests PASSED\n")

    # 3. Test Fallback Structured Extraction (Parallel)
    print("Test 3: Parallel Fallback Extraction & Dynamic Templates")
    from unittest.mock import patch
    with patch("handlers.compare_chat._parse_json_from_text", return_value=None):
        struct_a, struct_b = _extract_both_structures(resume_text, jd_text, "Resume / CV", "Job Description")
    
    # Check that keys match our expected schema templates
    assert "skills" in struct_a, "Resume fallback extraction missing 'skills'"
    assert "required_skills" in struct_b, "JD fallback extraction missing 'required_skills'"
    assert "experience" in struct_a, "Resume fallback extraction missing 'experience'"
    assert "required_experience" in struct_b, "JD fallback extraction missing 'required_experience'"
    print("-> Parallel Fallback Extraction tests PASSED\n")

    # 4. Test Semantic Cosine Similarity & Alignment
    print("Test 4: Embedding-based Alignment")
    # Verify that get_embedding_function is callable
    try:
        from rag import get_embedding_function
        emb_fn = get_embedding_function()
        print("-> Embedding function loaded successfully.")
    except Exception as e:
        print(f"-> Embedding function loading failed: {e}")
        emb_fn = None
        
    if emb_fn:
        # Check cosine similarity
        text1 = ["Python coding"]
        text2 = ["Java programming"]
        text3 = ["Python software development"]
        
        emb1 = _embed_units(text1)[0]
        emb2 = _embed_units(text2)[0]
        emb3 = _embed_units(text3)[0]
        
        sim_1_2 = _cosine_similarity(emb1, emb2)
        sim_1_3 = _cosine_similarity(emb1, emb3)
        
        print(f"   Similarity ('Python coding', 'Java programming'): {sim_1_2:.3f}")
        print(f"   Similarity ('Python coding', 'Python software development'): {sim_1_3:.3f}")
        
        assert sim_1_3 > sim_1_2, "Semantic similarity failed: Python coding should align closer to Python software dev than Java programming"
        print("-> Semantic Cosine Similarity tests PASSED\n")
    else:
        print("-> Skipping embedding-based cosine similarity test (Offline model function failed to load).\n")

    # 5. Test Comparison Framework Construction
    print("Test 5: Comparison Framework Construction")
    framework_text = build_intelligent_comparison_framework(resume_text, jd_text, "Compare experience and skills")
    
    # Assert formatting contains baseline structures
    assert "INTELLIGENT DOCUMENT COMPARISON FRAMEWORK" in framework_text, "Framework text missing header"
    assert "Overall category-derived score:" in framework_text, "Framework text missing score header"
    assert "Structured Extraction Baselines" in framework_text, "Framework text missing JSON baselines header"
    assert "skills" in framework_text.lower(), "Framework text missing JSON schema keys"
    
    print("-> Comparison Framework Construction tests PASSED\n")
    
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pipeline()
    test_compare_tool_cases()
