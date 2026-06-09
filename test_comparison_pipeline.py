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

def test_pipeline():
    print("Starting Compare Mode Optimization Unit Tests...\n")
    
    # 1. Test Document Classification
    print("Test 1: Document Classification")
    resume_text = "John Doe. Senior Software Engineer. Experience: Python, Java, React. Education: BS Computer Science."
    jd_text = "Job Description: We are hiring a Senior Software Engineer. Requirements: Python, React, BS in CS."
    contract_text = "This Agreement is made on this day. The party shall pay the cost and be liable for breaches."
    
    type_resume = _doc_type(resume_text)
    type_jd = _doc_type(jd_text)
    type_contract = _doc_type(contract_text)
    
    assert type_resume == "Resume / CV", f"Expected Resume / CV, got {type_resume}"
    assert type_jd == "Job Description", f"Expected Job Description, got {type_jd}"
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
