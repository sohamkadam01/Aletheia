from __future__ import annotations

import re
import json
import hashlib
import concurrent.futures
import os
from collections import Counter
from math import sqrt
import handlers.compare_cache as compare_cache


STOPWORDS = {
    "about", "above", "after", "against", "also", "because", "before", "between",
    "could", "document", "during", "either", "every", "from", "have", "into",
    "more", "most", "only", "other", "page", "part", "section", "source", "that",
    "their", "there", "these", "this", "those", "through", "under", "until",
    "uploaded", "website", "were", "what", "when", "where", "which", "while",
    "with", "would",
}

COMPARE_TARGETS = {
    "dates": {
        "label": "dates, deadlines, durations, timelines, and time-sensitive details",
        "terms": {"date", "dates", "deadline", "deadlines", "duration", "timeline", "timelines", "time", "schedule", "start", "end", "expiry", "expires", "valid", "year", "month"},
        "patterns": [r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", r"\b\d{4}\b", r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b"],
    },
    "requirements": {
        "label": "requirements, eligibility, responsibilities, and must-have criteria",
        "terms": {"requirement", "requirements", "required", "mandatory", "qualification", "qualifications", "eligible", "eligibility", "responsibility", "responsibilities", "must", "need", "needs", "criteria"},
        "patterns": [r"\b(required|requirements?|mandatory|qualifications?|responsibilit(?:y|ies)|eligible|eligibility|must have|must-have)\b"],
    },
    "skills": {
        "label": "skills, tools, technologies, keywords, and role-fit signals",
        "terms": {"skill", "skills", "technology", "technologies", "tool", "tools", "keyword", "keywords", "language", "languages", "framework", "frameworks", "tech", "stack"},
        "patterns": [r"\b(python|java|javascript|typescript|react|node|sql|aws|azure|docker|kubernetes|excel|power bi|tableau|machine learning|ai|api)\b"],
    },
    "pricing": {
        "label": "pricing, cost, salary, fees, budget, and financial terms",
        "terms": {"price", "pricing", "cost", "costs", "salary", "fee", "fees", "budget", "payment", "compensation", "package", "amount", "money"},
        "patterns": [r"(?:\$|rs\.?|inr|usd|eur|gbp)\s?\d+", r"\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:k|lpa|lakhs?|crores?|million|billion)?\b"],
    },
    "features": {
        "label": "features, services, capabilities, benefits, and deliverables",
        "terms": {"feature", "features", "service", "services", "capability", "capabilities", "benefit", "benefits", "deliverable", "deliverables", "offer", "offers", "include", "includes"},
        "patterns": [r"\b(features?|services?|capabilit(?:y|ies)|benefits?|deliverables?|includes?)\b"],
    },
    "policies": {
        "label": "policies, rules, terms, conditions, limits, and compliance points",
        "terms": {"policy", "policies", "rule", "rules", "term", "terms", "condition", "conditions", "limit", "limits", "compliance", "privacy", "refund", "cancellation"},
        "patterns": [r"\b(policies?|rules?|terms?|conditions?|limits?|compliance|privacy|refund|cancellation)\b"],
    },
    "contact": {
        "label": "contact details, locations, links, names, and communication channels",
        "terms": {"contact", "email", "phone", "address", "location", "locations", "link", "links", "url", "website", "name", "person"},
        "patterns": [r"\b[\w.+-]+@[\w.-]+\.\w+\b", r"\b(?:phone|email|contact|address|location|linkedin|github)\b"],
    },
}

BASIS_KEYWORDS = {
    "Role fit / hiring alignment": {
        "terms": {"resume", "experience", "skills", "projects", "education", "job", "role", "requirements", "qualifications", "responsibilities", "candidate", "hiring"},
        "dimensions": ["role purpose", "required skills", "experience evidence", "education/qualification fit", "missing keywords", "responsibility coverage"],
    },
    "Feature / service alignment": {
        "terms": {"feature", "features", "service", "services", "product", "plan", "benefit", "capability", "offer", "deliverable", "solution"},
        "dimensions": ["main offering", "included features", "missing capabilities", "benefits", "limitations", "user value"],
    },
    "Policy / contract alignment": {
        "terms": {"policy", "agreement", "contract", "clause", "terms", "condition", "privacy", "refund", "termination", "liability", "compliance"},
        "dimensions": ["scope", "obligations", "limits", "exceptions", "dates/durations", "conflicts or risk"],
    },
    "Academic / research alignment": {
        "terms": {"research", "study", "abstract", "methodology", "method", "results", "findings", "references", "journal", "experiment"},
        "dimensions": ["research objective", "methodology", "evidence/findings", "scope", "claims", "missing support"],
    },
    "General content alignment": {
        "terms": set(),
        "dimensions": ["purpose", "main topics", "key claims", "shared concepts", "missing details", "conflicts"],
    },
}

TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue", "node", "node.js",
    "express", "spring", "spring boot", "django", "flask", "fastapi", "sql", "mysql",
    "postgresql", "mongodb", "redis", "aws", "azure", "gcp", "docker", "kubernetes",
    "linux", "git", "github", "rest", "api", "graphql", "html", "css", "tailwind",
    "bootstrap", "machine learning", "deep learning", "nlp", "pandas", "numpy",
    "tensorflow", "pytorch", "scikit-learn", "power bi", "tableau", "excel", "jira",
    "figma", "ci/cd", "jenkins", "terraform", "spark", "hadoop", "selenium",
}

SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "collaboration", "problem solving",
    "analytical", "adaptability", "ownership", "stakeholder", "presentation",
    "mentoring", "time management", "critical thinking",
}

EDUCATION_TERMS = {
    "bachelor", "bachelors", "b.tech", "btech", "be", "b.e", "master", "masters",
    "m.tech", "mtech", "mba", "phd", "degree", "computer science", "engineering",
}

CERTIFICATION_TERMS = {
    "certified", "certification", "certificate", "aws certified", "azure certified",
    "scrum", "pmp", "cisco", "ccna", "oracle certified", "google cloud certified",
}


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", (text or "").lower())
        if token not in STOPWORDS and not token.startswith(("http", "www"))
    ]


def _contains_any(text: str, terms: set[str]) -> bool:
    lowered = (text or "").lower()
    return any(term in lowered for term in terms)


def _detect_resume_job_pair(document_a: str, document_b: str) -> dict:
    type_a = _doc_type(document_a)
    type_b = _doc_type(document_b)
    a_is_resume = type_a in {"Resume / CV", "Resume/Profile"}
    b_is_resume = type_b in {"Resume / CV", "Resume/Profile"}
    a_is_jd = type_a == "Job Description"
    b_is_jd = type_b == "Job Description"

    if a_is_resume and b_is_jd:
        return {"is_pair": True, "resume": document_a, "job": document_b, "resume_label": "Document A", "job_label": "Document B"}
    if b_is_resume and a_is_jd:
        return {"is_pair": True, "resume": document_b, "job": document_a, "resume_label": "Document B", "job_label": "Document A"}
    return {"is_pair": False, "resume": "", "job": "", "resume_label": "", "job_label": ""}


def _extract_skill_terms(text: str) -> set[str]:
    lowered = (text or "").lower()
    found = {skill for skill in TECH_SKILLS | SOFT_SKILLS if skill in lowered}
    token_set = set(_tokens(text))
    found.update(token for token in token_set if token in TECH_SKILLS or token in SOFT_SKILLS)
    return found


def _extract_years(text: str) -> int:
    lowered = (text or "").lower()
    values = []
    for match in re.finditer(r"\b(\d{1,2})\+?\s*(?:years?|yrs?)\b", lowered):
        try:
            values.append(int(match.group(1)))
        except ValueError:
            pass
    return max(values) if values else 0


def _requirement_lines(text: str, preferred: bool = False) -> list[str]:
    markers = (
        "preferred", "nice to have", "good to have", "plus", "bonus"
    ) if preferred else (
        "required", "requirements", "must", "mandatory", "qualification", "qualifications",
        "responsibilities", "experience with", "proficient", "knowledge of"
    )
    lines = []
    for unit in _comparison_units(text, limit=60):
        lowered = unit.lower()
        if any(marker in lowered for marker in markers):
            lines.append(_format_evidence(unit, max_chars=220))
    return lines[:12]


def _match_list(required: set[str], available: set[str]) -> tuple[list[str], list[str]]:
    matched = sorted(required & available)
    missing = sorted(required - available)
    return matched, missing


def _percent(matched: int, total: int) -> float:
    return matched / max(1, total)


def calculate_weighted_percentage(components: list[dict]) -> dict:
    """Calculate a transparent weighted percentage from category-level evidence."""
    applicable = [
        component for component in components
        if component.get("applicable", True) and component.get("weight", 0) > 0
    ]
    total_weight = sum(component["weight"] for component in applicable)
    if total_weight <= 0:
        return {
            "percentage": 0,
            "total_weight": 0,
            "components": components,
            "calculation_note": "No applicable weighted categories were found.",
        }

    weighted_points = 0.0
    normalized_components = []
    for component in applicable:
        ratio = max(0.0, min(1.0, float(component.get("ratio", 0.0))))
        points = ratio * component["weight"]
        weighted_points += points
        normalized_components.append({
            **component,
            "ratio": round(ratio, 3),
            "points": round(points, 2),
        })

    percentage = round((weighted_points / total_weight) * 100)
    return {
        "percentage": max(0, min(100, percentage)),
        "total_weight": total_weight,
        "components": normalized_components,
        "calculation_note": "Percentage is calculated from applicable category weights only; non-required categories are not silently awarded points.",
    }


def _format_score_components(components: list[dict]) -> str:
    if not components:
        return "- No applicable score components."
    return "\n".join(
        f"- {component['name']}: {component['points']:.2f}/{component['weight']} "
        f"({round(component['ratio'] * 100)}%) - {component.get('evidence', 'No evidence note.')}"
        for component in components
    )


def _fit_band(score: int) -> str:
    if score >= 85:
        return "Strong fit"
    if score >= 70:
        return "Good fit"
    if score >= 50:
        return "Moderate fit"
    if score >= 30:
        return "Weak fit"
    return "Low fit"


def _generate_ascii_scorecard(score_result: dict, matched: list, missing: list) -> str:
    # Build Matches / Gaps lists
    matches_text = []
    gaps_text = []
    for m in matched[:5]:
        matches_text.append(f"{m[:20]:<20} ✅ MATCH")
    for g in missing[:5]:
        gaps_text.append(f"{g[:20]:<20} ❌ Missing")
    
    # Pad to equal length
    max_len = max(len(matches_text), len(gaps_text), 1)
    while len(matches_text) < max_len: matches_text.append(f"{'':<20}        ")
    while len(gaps_text) < max_len: gaps_text.append(f"{'':<20}          ")
    
    top_section = "================================================================================\n"
    top_section += "  ✅ MATCHES (Good)                    ❌ GAPS (Needs Work)\n"
    top_section += "================================================================================\n"
    for m, g in zip(matches_text, gaps_text):
        top_section += f"  {m}      {g}\n"
    
    # Build Scorecard Table
    table_section = "\n================================================================================\n"
    table_section += "  SCORECARD\n"
    table_section += "================================================================================\n"
    table_section += "  ┌───────────────────┬─────────┬─────────┬─────────────────────────────────┐\n"
    table_section += "  │ Category          │ Score   │ Max     │ Bar                             │\n"
    table_section += "  ├───────────────────┼─────────┼─────────┼─────────────────────────────────┤\n"
    
    for comp in score_result.get("components", []):
        name = comp["name"][:17]
        score_val = int(comp["ratio"] * 100)
        blocks = int(comp["ratio"] * 20)
        bar_str = ("█" * blocks) + ("░" * (20 - blocks))
        icon = "✅" if score_val >= 70 else "❌"
        # Pad the bar string to ensure alignment
        pad_score = f"{score_val}%"
        table_section += f"  │ {name:<17} │ {score_val:<7} │ 100     │ {bar_str} {pad_score:<4} {icon:<1} │\n"
        
    table_section += "  └───────────────────┴─────────┴─────────┴─────────────────────────────────┘\n"
    table_section += "================================================================================\n"
    return "```text\n" + top_section + table_section + "```\n"

def build_resume_job_fit_analysis(document_a: str, document_b: str, provider: str = "") -> str:
    pair = _detect_resume_job_pair(document_a, document_b)
    if not pair["is_pair"]:
        return ""

    resume = pair["resume"]
    job = pair["job"]
    struct_resume, struct_job = _extract_both_structures(resume, job, "Resume / CV", "Job Description")
    
    resume_skills = set(struct_resume.get("skills", []) or [])
    job_skills = set(struct_job.get("required_skills", []) or [])
    job_pref_skills = set(struct_job.get("preferred_skills", []) or [])
    
    # Fallback to lexical if empty
    if not resume_skills: resume_skills = _extract_skill_terms(resume)
    if not job_skills: job_skills = {s for s in _extract_skill_terms(job) if s in TECH_SKILLS}
    
    matched_required, missing_required = _match_list(job_skills, resume_skills)
    matched_preferred, missing_preferred = _match_list(job_pref_skills, resume_skills)

    resume_years = struct_resume.get("calculated_total_years_experience")
    if resume_years is None: resume_years = _extract_years(resume)
    
    job_years_dict = struct_job.get("required_experience", {})
    job_years = job_years_dict.get("years_number", 0) if isinstance(job_years_dict, dict) else _extract_years(job)
    experience_ratio = 1.0 if not job_years else min(1.0, float(resume_years) / max(1, float(job_years)))

    resume_seniority = str(struct_resume.get("seniority_level_inferred", "Mid")).lower()
    job_seniority = str(struct_job.get("seniority_level", "Mid")).lower()
    
    # Simple seniority check
    seniority_match = 1.0
    if ("lead" in job_seniority or "executive" in job_seniority or "senior" in job_seniority) and ("entry" in resume_seniority or "junior" in resume_seniority):
        seniority_match = 0.0
    elif ("senior" in job_seniority) and ("mid" in resume_seniority):
        seniority_match = 0.5

    education_match = _contains_any(resume, EDUCATION_TERMS) and _contains_any(job, EDUCATION_TERMS)
    certification_match = _contains_any(resume, CERTIFICATION_TERMS) and _contains_any(job, CERTIFICATION_TERMS)
    project_relevance = bool((resume_skills & job_skills) and re.search(r"\b(project|projects|built|developed|implemented)\b", resume, re.I))
    domain_terms = set(_top_terms(job, limit=20)) & set(_top_terms(resume, limit=30))

    education_required = _contains_any(job, EDUCATION_TERMS) or bool(struct_job.get("required_education"))
    certification_required = _contains_any(job, CERTIFICATION_TERMS) or bool(struct_job.get("required_certifications"))
    project_ratio = min(1.0, (len(domain_terms) / 8) + (0.35 if project_relevance else 0))
    
    score_result = calculate_weighted_percentage([
        {
            "name": "Skills Match",
            "weight": 35,
            "ratio": _percent(len(matched_required), len(job_skills)),
            "evidence": f"Matched required skills: {', '.join(matched_required) or 'none'}; missing: {', '.join(missing_required) or 'none'}",
            "applicable": bool(job_skills),
        },
        {
            "name": "Experience Match",
            "weight": 25,
            "ratio": experience_ratio,
            "evidence": f"Candidate years detected: {resume_years or 'not explicit'}; required years detected: {job_years or 'not explicit'}",
            "applicable": bool(job_years),
        },
        {
            "name": "Seniority Alignment",
            "weight": 10,
            "ratio": seniority_match,
            "evidence": f"JD requires {job_seniority}; candidate inferred as {resume_seniority}",
            "applicable": True,
        },
        {
            "name": "Education Match",
            "weight": 10,
            "ratio": 1.0 if education_match else 0.0,
            "evidence": f"Education requirement detected: {education_required}; resume evidence: {education_match}",
            "applicable": education_required,
        },
        {
            "name": "Certifications Match",
            "weight": 10,
            "ratio": 1.0 if certification_match else 0.0,
            "evidence": f"Certification requirement detected: {certification_required}; resume evidence: {certification_match}",
            "applicable": certification_required,
        },
        {
            "name": "Project/Domain Relevance",
            "weight": 10,
            "ratio": project_ratio,
            "evidence": f"Shared domain terms: {', '.join(sorted(domain_terms)[:12]) or 'limited'}; project evidence detected: {bool(project_relevance)}",
            "applicable": True,
        },
    ])
    fit_score = score_result["percentage"]

    matched_required_text = ", ".join(matched_required) or "No explicit required technical-skill matches found in extracted text"
    missing_required_text = ", ".join(missing_required) or "No major required technical-skill gaps detected from extracted keywords"
    matched_preferred_text = ", ".join(matched_preferred) or "No explicit preferred/soft-skill matches found in extracted text"
    
    # Identify missed leadership/client responsibilities
    missing_responsibilities = []
    resume_lower = resume.lower()
    for resp in struct_job.get("leadership_management_responsibilities", []):
        if not _contains_any(resume, {"manage", "lead", "mentor", "direct"}):
            missing_responsibilities.append(f"Leadership: {resp}")
    for resp in struct_job.get("client_facing_responsibilities", []):
        if not _contains_any(resume, {"client", "customer", "stakeholder"}):
            missing_responsibilities.append(f"Client Facing: {resp}")
            
    critical_must_haves = struct_job.get("critical_must_haves", [])
    critical_text = " / ".join(critical_must_haves) if critical_must_haves else "None identified"
    
    missing_resp_text = "; ".join(missing_responsibilities) or "None"

    base_context = (
        "RESUME VS JOB DESCRIPTION FIT BASELINE - USE THIS INSTEAD OF GENERIC DOCUMENT SIMILARITY:\n"
        f"Resume source lane: {pair['resume_label']}\n"
        f"Job Description source lane: {pair['job_label']}\n"
        "Primary objective: evaluate candidate-job fit, requirement fulfillment, qualification alignment, and job readiness. "
        "Do not say the resume and job description are not directly comparable. Do not score zero because they are different document types.\n"
        f"Overall Match Score: {fit_score}/100 ({_fit_band(fit_score)})\n"
        "Weighted score components from deterministic calculator:\n"
        f"{_format_score_components(score_result['components'])}\n"
        f"Score calculation note: {score_result['calculation_note']}\n"
        f"Critical Must-Haves from JD: {critical_text}\n"
        f"Missing Critical Responsibilities (Leadership/Client): {missing_resp_text}\n"
        f"Preferred/soft-skill evidence: matched={matched_preferred_text}\n"
        "Required final output structure for this pair:\n"
        "1. Candidate Overview\n"
        "2. Job Requirement Overview\n"
        "3. Matched Skills\n"
        "4. Missing Skills & Responsibilities\n"
        "5. Experience Analysis (Years and Seniority Level)\n"
        "6. Education & Certifications Analysis\n"
        "7. Project Relevance\n"
        "8. Overall Match Score\n"
        "9. Hiring Recommendation\n"
        "Scoring rule: final score represents candidate-job fit, not document similarity. Every score must be supported by matched or missing requirements.\n"
    )

    if provider == "ollama":
        ascii_scorecard = _generate_ascii_scorecard(score_result, matched_required, missing_required)
        base_context += (
            "\n[OLLAMA OVERRIDE INSTRUCTION]\n"
            "Do not attempt to calculate or format the scorecard table yourself. "
            "You MUST output the exact PRE-GENERATED SCORECARD provided below at the very beginning of your response. "
            "After pasting it, write ONLY a short Candidate Overview and Hiring Recommendation based on the numbers.\n"
            "PRE-GENERATED SCORECARD:\n"
            f"{ascii_scorecard}\n"
        )

    return base_context



def _top_terms(text: str, limit: int = 24) -> list[str]:
    counts = Counter(_tokens(text))
    return [term for term, _count in counts.most_common(limit)]


def _key_phrases(text: str, limit: int = 8) -> list[str]:
    units = _comparison_units(text, limit=20)
    ranked = []
    top_terms = set(_top_terms(text, limit=18))

    for index, unit in enumerate(units):
        unit_tokens = set(_tokens(unit))
        score = len(unit_tokens & top_terms)
        lowered = unit.lower()
        if any(marker in lowered for marker in ("purpose", "objective", "summary", "about", "responsibilities", "requirements", "features", "services")):
            score += 3
        ranked.append((score, -index, unit))

    selected = []
    for _score, _neg_index, unit in sorted(ranked, reverse=True):
        cleaned = _format_evidence(unit, max_chars=180)
        if cleaned and cleaned not in selected:
            selected.append(cleaned)
        if len(selected) >= limit:
            break
    return selected


def _central_idea(text: str, doc_type: str) -> str:
    phrases = _key_phrases(text, limit=3)
    terms = _top_terms(text, limit=6)
    if phrases:
        return f"{doc_type}; main evidence points: " + " / ".join(phrases)
    if terms:
        return f"{doc_type}; main concepts: " + ", ".join(terms)
    return f"{doc_type}; no clear central idea extracted from the available text"


def _basis_category(document_a: str, document_b: str, target: dict) -> str:
    combined_terms = set(_tokens(f"{document_a} {document_b}"))
    best_label = "General content alignment"
    best_score = 0
    for label, spec in BASIS_KEYWORDS.items():
        score = len(combined_terms & spec["terms"])
        if score > best_score:
            best_label = label
            best_score = score

    if target.get("key") == "requirements" and best_score < 2:
        return "Role fit / hiring alignment"
    if target.get("key") in {"features", "pricing"} and best_score < 2:
        return "Feature / service alignment"
    if target.get("key") == "policies" and best_score < 2:
        return "Policy / contract alignment"
    return best_label


def _basis_dimensions(category: str, target: dict) -> list[str]:
    dimensions = list(BASIS_KEYWORDS.get(category, BASIS_KEYWORDS["General content alignment"])["dimensions"])
    target_key = target.get("key")
    if target_key == "dates":
        dimensions = ["exact dates", "deadlines/durations", "timeline meaning", "missing dates", "conflicting dates"]
    elif target_key == "pricing":
        dimensions = ["amounts", "included/excluded costs", "conditions", "missing financial terms", "conflicts"]
    elif target_key == "skills":
        dimensions = ["matched skills", "missing skills", "tools/technologies", "experience evidence", "keyword strength"]
    elif target_key == "requirements":
        dimensions = ["must-have requirements", "candidate/source evidence", "partial coverage", "missing criteria", "conflicts"]
    elif target_key == "contact":
        dimensions = ["names", "email/phone/address", "links", "locations", "missing contact details"]
    return dimensions


def build_comparison_basis(document_a: str, document_b: str, question: str, target: dict) -> dict:
    doc_type_a = _doc_type(document_a)
    doc_type_b = _doc_type(document_b)
    category = _basis_category(document_a, document_b, target)
    terms_a = _top_terms(document_a, limit=16)
    terms_b = _top_terms(document_b, limit=16)
    shared_terms = [term for term in terms_a if term in set(terms_b)][:10]
    only_a = [term for term in terms_a if term not in set(terms_b)][:8]
    only_b = [term for term in terms_b if term not in set(terms_a)][:8]
    target_label = target.get("label") or "overall alignment"
    basis_reason = (
        f"The chosen basis is {category} because Document A is detected as {doc_type_a}, "
        f"Document B is detected as {doc_type_b}, and the user is asking about {target_label}."
    )
    if shared_terms:
        basis_reason += f" Shared concepts include: {', '.join(shared_terms[:6])}."
    else:
        basis_reason += " The available text has limited shared concepts, so gaps and missing evidence must be emphasized."

    return {
        "category": category,
        "document_a_idea": _central_idea(document_a, doc_type_a),
        "document_b_idea": _central_idea(document_b, doc_type_b),
        "basis_reason": basis_reason,
        "dimensions": _basis_dimensions(category, target),
        "shared_terms": shared_terms,
        "only_a": only_a,
        "only_b": only_b,
    }


def _evidence_bank(text: str, label: str, target: dict) -> list[str]:
    units = _comparison_units(text, limit=32)
    focused = _focus_units(units, target, fallback_limit=8)
    selected_units = focused or units[:8]
    bank = []

    for index, unit in enumerate(selected_units, start=1):
        evidence = _format_evidence(unit, max_chars=190)
        if evidence:
            bank.append(f"{label}{index}: {evidence}")
    return bank


def _format_evidence_bank(bank: list[str]) -> str:
    return "\n".join(f"- {item}" for item in bank) if bank else "- No source-specific evidence extracted."


def _clean_unit(text: str) -> str:
    return " ".join(re.sub(r"^(Source|Website|Document)\s+[A-Z0-9]+:\s*.*$", "", text or "", flags=re.I | re.M).split())


def _comparison_units(text: str, limit: int = 18) -> list[str]:
    raw_units = re.split(r"\n{2,}|(?<=[.!?])\s+(?=[A-Z0-9])", text or "")
    units = []
    seen = set()

    for raw_unit in raw_units:
        unit = _clean_unit(raw_unit)
        if len(unit) < 45:
            continue
        if len(unit) > 520:
            unit = unit[:520].rsplit(" ", 1)[0].strip()
        fingerprint = re.sub(r"\W+", " ", unit.lower())[:260]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        units.append(unit)
        if len(units) >= limit:
            break

    if not units:
        compact = _clean_unit(text)
        if compact:
            units.append(compact[:520].rsplit(" ", 1)[0].strip())
    return units


def detect_compare_target(question: str) -> dict:
    normalized = " ".join((question or "").lower().split())
    query_terms = set(_tokens(normalized))
    best_key = "overall"
    best_score = 0

    for key, spec in COMPARE_TARGETS.items():
        score = len(query_terms & spec["terms"])
        if score > best_score:
            best_key = key
            best_score = score

    if best_key == "overall":
        return {
            "key": "overall",
            "label": "overall alignment across the most important comparable points",
            "query_terms": [term for term in _tokens(question) if term not in {"compare", "alignment", "score"}][:12],
            "patterns": [],
            "specific": False,
        }

    spec = COMPARE_TARGETS[best_key]
    return {
        "key": best_key,
        "label": spec["label"],
        "query_terms": sorted(query_terms & spec["terms"])[:12],
        "patterns": spec["patterns"],
        "specific": True,
    }


def build_compare_retrieval_query(question: str) -> str:
    target = detect_compare_target(question)
    normalized = " ".join((question or "").split())
    lowered = normalized.lower()

    if any(term in lowered for term in ("resume", "cv", "job description", "jd", "ats", "candidate", "hiring", "role fit", "fit score")):
        return (
            f"{normalized}\n"
            "Resume vs Job Description comparison target: candidate-job fit, not document similarity.\n"
            "Retrieve from BOTH sources: skills, technical skills, soft skills, tools, technologies, years of experience, domain experience, "
            "education, certifications, projects, responsibilities, required qualifications, preferred qualifications, and missing requirements. "
            "Prioritize exact requirement language from the job description and exact evidence from the resume."
        )

    if target.get("specific"):
        return (
            f"{normalized}\n"
            f"Comparison target: {target['label']}.\n"
            "Retrieve source text from BOTH Document A and Document B that directly mentions this target. "
            "Also retrieve the purpose, objective, summary, main idea, role, product, policy scope, or topic statement from each source so the basis of comparison is clear. "
            "Prioritize exact values, requirements, dates, keywords, names, amounts, clauses, and nearby explanatory wording. "
            "Also include directly related missing or contradictory details needed for a focused comparison."
        )

    return (
        f"{normalized}\n"
        "Before comparing, retrieve document type clues and the user's likely comparison intent from BOTH sources. "
        "Retrieve structured attributes from BOTH sources: key topics, skills, requirements, responsibilities, technologies, experience levels, "
        "education requirements, certifications, objectives, constraints, deliverables, important entities, risks, gaps, and important differences. "
        "Do not retrieve only semantically similar wording; retrieve requirement and purpose evidence needed for a document-type-aware comparison."
    )


def _target_score(unit: str, target: dict) -> int:
    if not target or not target.get("specific"):
        return 0
    lower_unit = (unit or "").lower()
    score = sum(2 for term in target.get("query_terms", []) if term in lower_unit)
    score += sum(3 for pattern in target.get("patterns", []) if re.search(pattern, lower_unit, flags=re.I))
    return score


def _focus_units(units: list[str], target: dict, fallback_limit: int = 18) -> list[str]:
    if not target or not target.get("specific"):
        return units[:fallback_limit]

    ranked = [
        (score, index, unit)
        for index, unit in enumerate(units)
        for score in [_target_score(unit, target)]
        if score > 0
    ]
    if not ranked:
        return []

    focused = [unit for _score, _index, unit in sorted(ranked, key=lambda item: (-item[0], item[1]))]
    return focused[:fallback_limit]


def _token_similarity(left: str, right: str) -> float:
    left_tokens = set(_tokens(left))
    right_tokens = set(_tokens(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def _embed_units(units: list[str]) -> list[list[float]]:
    try:
        from rag import get_embedding_function

        embeddings = get_embedding_function()(units)
        return [list(map(float, embedding)) for embedding in embeddings]
    except Exception as exc:
        print(f"Compare embeddings unavailable; using lexical similarity: {exc}")
        return []


def _status_for_score(score: float) -> str:
    if score >= 0.72:
        return "Match"
    if score >= 0.44:
        return "Partial"
    return "Missing"


def _has_conflict(left: str, right: str, similarity: float) -> bool:
    if similarity < 0.35:
        return False

    left_text = f" {_clean_unit(left).lower()} "
    right_text = f" {_clean_unit(right).lower()} "
    opposing_pairs = [
        (" required ", " optional "),
        (" mandatory ", " optional "),
        (" remote ", " onsite "),
        (" onsite ", " remote "),
        (" full-time ", " part-time "),
        (" part-time ", " full-time "),
        (" paid ", " unpaid "),
        (" yes ", " no "),
        (" allowed ", " prohibited "),
        (" allow ", " prohibit "),
        (" includes ", " excludes "),
    ]
    if any(left in left_text and right in right_text for left, right in opposing_pairs):
        return True
    if any(right in left_text and left in right_text for left, right in opposing_pairs):
        return True

    negation_terms = (" not ", " no ", " never ", " without ", " excludes ", " prohibited ")
    shared_terms = set(_tokens(left_text)) & set(_tokens(right_text))
    return bool(shared_terms and (any(term in left_text for term in negation_terms) != any(term in right_text for term in negation_terms)))


def _match_units(document_a: str, document_b: str, target: dict = None) -> dict:
    all_units_a = _comparison_units(document_a, limit=36)
    all_units_b = _comparison_units(document_b, limit=36)
    units_a = _focus_units(all_units_a, target)
    units_b = _focus_units(all_units_b, target)
    embeddings_a = _embed_units(units_a)
    embeddings_b = _embed_units(units_b) if embeddings_a else []
    using_embeddings = bool(embeddings_a and embeddings_b)
    rows = []

    if not units_a and units_b:
        for index, unit_b in enumerate(units_b[:8]):
            rows.append({
                "area": _label_for_unit(unit_b, index),
                "document_a": "Not found in Document A",
                "document_b": unit_b,
                "similarity": 0.0,
                "status": "Missing",
                "impact": "Target detail appears in Document B but was not found in Document A.",
                "target_weight": _target_score(unit_b, target),
            })

    for index, unit_a in enumerate(units_a):
        best_score = 0.0
        best_unit_b = ""

        for b_index, unit_b in enumerate(units_b):
            if using_embeddings:
                score = _cosine_similarity(embeddings_a[index], embeddings_b[b_index])
            else:
                score = _token_similarity(unit_a, unit_b)
            if score > best_score:
                best_score = score
                best_unit_b = unit_b

        status = "Conflict" if _has_conflict(unit_a, best_unit_b, best_score) else _status_for_score(best_score)
        target_weight = _target_score(unit_a, target)
        rows.append({
            "area": _label_for_unit(unit_a, index),
            "document_a": unit_a,
            "document_b": best_unit_b,
            "similarity": round(best_score, 3),
            "status": status,
            "impact": _impact_for_status(best_score, status),
            "target_weight": target_weight,
        })

    rows.sort(key=lambda row: (-row.get("target_weight", 0), row["status"] == "Missing", row["status"] != "Conflict", -row["similarity"]))
    avg_similarity = sum(row["similarity"] for row in rows) / max(1, len(rows))
    matched = sum(1 for row in rows if row["status"] == "Match")
    partial = sum(1 for row in rows if row["status"] == "Partial")
    missing = sum(1 for row in rows if row["status"] == "Missing")
    conflicts = sum(1 for row in rows if row["status"] == "Conflict")
    coverage = (matched + 0.5 * partial) / max(1, len(rows))

    return {
        "rows": rows[:10],
        "average_similarity": avg_similarity,
        "coverage": coverage,
        "matched": matched,
        "partial": partial,
        "missing": missing,
        "conflicts": conflicts,
        "total": len(rows),
        "method": "embedding cosine similarity" if using_embeddings else "lexical token similarity fallback",
        "target_specific_rows": sum(1 for row in rows if row.get("target_weight", 0) > 0),
    }


def _label_for_unit(unit: str, index: int) -> str:
    terms = _top_terms(unit, limit=4)
    if terms:
        return " / ".join(term.title() for term in terms)
    return f"Point {index + 1}"


def _impact_for_status(score: float, status: str = "") -> str:
    if status == "Conflict":
        return "Potential contradiction; verify the exact wording in both sources."
    if score >= 0.72:
        return "Strong evidence appears in both sources."
    if score >= 0.44:
        return "Partially covered; review scope, detail, dates, or wording."
    return "Coverage gap; Document B does not clearly support this Document A point."


def _format_evidence(value: str, max_chars: int = 150) -> str:
    cleaned = _clean_unit(value).replace("|", "/")
    if len(cleaned) <= max_chars:
        return cleaned or "Not found"
    return cleaned[:max_chars].rsplit(" ", 1)[0].strip() + "..."


def _format_table_cell(value: str, max_chars: int = 80) -> str:
    cleaned = _clean_unit(value).replace("|", "/")
    if len(cleaned) <= max_chars:
        return cleaned or "Not found"
    return cleaned[:max_chars].rsplit(" ", 1)[0].strip() + "..."


def _headings(text: str) -> set[str]:
    candidates = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip().strip("#:- ")
        if not line or len(line) > 80:
            continue
        if re.match(r"^(source|website|document)\s+[a-z0-9]+:", line, re.I):
            continue
        if raw_line.startswith(("#", "##")) or line.istitle() or line.isupper():
            cleaned = " ".join(_tokens(line)[:6])
            if cleaned:
                candidates.append(cleaned)
    return set(candidates[:20])


DOC_TYPE_SIGNALS = {
    "Resume / CV": {
        "resume", "curriculum vitae", "professional summary", "work experience", "employment",
        "education", "skills", "projects", "certifications", "linkedin", "github", "portfolio",
    },
    "Job Description": {
        "job description", "responsibilities", "requirements", "required qualifications",
        "preferred qualifications", "must have", "nice to have", "apply now", "role", "candidate",
        "we are hiring", "salary", "benefits", "experience required",
    },
    "Research Paper": {
        "abstract", "methodology", "methods", "results", "discussion", "conclusion",
        "references", "citation", "journal", "experiment", "study", "literature review",
    },
    "Contract": {
        "agreement", "contract", "clause", "party", "parties", "termination", "liability",
        "indemnity", "governing law", "payment terms", "confidentiality", "effective date",
    },
    "Policy Document": {
        "policy", "policies", "procedure", "compliance", "guideline", "scope",
        "governance", "approval", "privacy policy", "refund policy", "security policy",
    },
    "Technical Specification": {
        "technical specification", "specification", "architecture", "api", "endpoint",
        "functional requirements", "non-functional", "system requirements", "schema",
        "integration", "performance", "security requirements",
    },
    "Project Proposal": {
        "proposal", "project proposal", "objectives", "scope of work", "deliverables",
        "milestones", "timeline", "budget", "resources", "stakeholders",
    },
    "Meeting Notes": {
        "meeting notes", "minutes", "attendees", "agenda", "action items", "decisions",
        "next steps", "discussion", "follow-up",
    },
    "Report": {
        "report", "executive summary", "findings", "analysis", "recommendations",
        "metrics", "status", "overview",
    },
    "Article": {
        "article", "author", "published", "news", "blog", "opinion", "story",
    },
}


def _classification_scores(text: str) -> dict[str, int]:
    lowered = f" {(text or '').lower()} "
    scores = {}
    for doc_type, signals in DOC_TYPE_SIGNALS.items():
        score = 0
        for signal in signals:
            if signal in lowered:
                score += 3 if " " in signal else 1
        scores[doc_type] = score

    # JDs often contain "skills" and "education"; prioritize explicit requirement language over resume sections.
    if re.search(r"\b(required|requirements?|responsibilit(?:y|ies)|qualifications?|must have|preferred|apply now|we are hiring)\b", lowered):
        scores["Job Description"] += 8
    if re.search(r"\b(work experience|professional summary|projects?|github|linkedin|curriculum vitae|resume)\b", lowered):
        scores["Resume / CV"] += 8
    return scores


def _doc_type(text: str) -> str:
    scores = _classification_scores(text)
    best_type, best_score = max(scores.items(), key=lambda item: item[1])
    return best_type if best_score > 0 else "Other"


def _score_components(document_a: str, document_b: str, target: dict = None) -> dict:
    unit_matches = _match_units(document_a, document_b, target)
    terms_a = _top_terms(document_a)
    terms_b = _top_terms(document_b)
    set_a = set(terms_a)
    set_b = set(terms_b)
    shared = set_a & set_b
    min_terms = max(1, min(len(set_a), len(set_b)))
    coverage_base = max(1, len(set_a))

    heading_a = _headings(document_a)
    heading_b = _headings(document_b)
    heading_overlap = len(heading_a & heading_b) / max(1, min(len(heading_a), len(heading_b))) if heading_a and heading_b else 0
    same_type = _doc_type(document_a) == _doc_type(document_b)

    semantic = round(40 * unit_matches["average_similarity"])
    coverage = round(30 * unit_matches["coverage"])
    exact = round(20 * (len(shared) / min_terms))
    structural = round(10 * heading_overlap) if heading_overlap else (6 if same_type else 3)

    return {
        "semantic_similarity": min(40, semantic),
        "requirement_coverage": min(30, coverage),
        "exact_concept_matches": min(20, exact),
        "structural_alignment": min(10, structural),
        "shared_terms": sorted(shared, key=lambda term: terms_a.index(term) if term in terms_a else 999)[:12],
        "only_a": [term for term in terms_a if term not in set_b][:12],
        "only_b": [term for term in terms_b if term not in set_a][:12],
        "document_a_type": _doc_type(document_a),
        "document_b_type": _doc_type(document_b),
        "unit_matches": unit_matches,
    }


def _score_band(score: int) -> str:
    if score >= 90:
        return "Nearly identical"
    if score >= 70:
        return "Strong alignment"
    if score >= 50:
        return "Moderate alignment"
    if score >= 30:
        return "Weak alignment"
    return "Very limited alignment"


COMPARISON_STRATEGIES = {
    ("Resume / CV", "Job Description"): {
        "name": "Candidate Fit Analysis",
        "dimensions": ["required skills", "preferred skills", "experience", "education", "certifications", "projects", "domain knowledge"],
        "weights": {"Skills Match": 40, "Experience Match": 25, "Education Match": 15, "Certifications Match": 10, "Project Relevance": 10},
    },
    ("Job Description", "Resume / CV"): {
        "name": "Candidate Fit Analysis",
        "dimensions": ["required skills", "preferred skills", "experience", "education", "certifications", "projects", "domain knowledge"],
        "weights": {"Skills Match": 40, "Experience Match": 25, "Education Match": 15, "Certifications Match": 10, "Project Relevance": 10},
    },
    ("Contract", "Contract"): {
        "name": "Clause Comparison",
        "dimensions": ["obligations", "deadlines", "payment terms", "legal clauses", "risks", "exceptions"],
        "weights": {"Obligations": 25, "Payment/Deadlines": 25, "Legal Clauses": 25, "Risk/Exceptions": 25},
    },
    ("Research Paper", "Research Paper"): {
        "name": "Topic & Methodology Comparison",
        "dimensions": ["research objective", "methodology", "dataset/evidence", "results", "limitations"],
        "weights": {"Topic Alignment": 25, "Methodology": 30, "Evidence/Results": 30, "Limitations": 15},
    },
    ("Policy Document", "Policy Document"): {
        "name": "Requirement & Compliance Comparison",
        "dimensions": ["requirements", "scope", "compliance obligations", "exceptions", "risk"],
        "weights": {"Requirement Coverage": 35, "Compliance": 30, "Scope/Exceptions": 20, "Risk": 15},
    },
    ("Technical Specification", "Technical Specification"): {
        "name": "Functional Gap Analysis",
        "dimensions": ["functional requirements", "non-functional requirements", "architecture", "interfaces", "constraints"],
        "weights": {"Functional Coverage": 35, "Technical Interfaces": 25, "Constraints": 20, "Risks": 20},
    },
}


DIMENSION_TERMS = {
    "required skills": TECH_SKILLS,
    "preferred skills": SOFT_SKILLS,
    "experience": {"experience", "years", "domain", "senior", "junior", "lead"},
    "education": EDUCATION_TERMS,
    "certifications": CERTIFICATION_TERMS,
    "projects": {"project", "projects", "built", "developed", "implemented", "portfolio"},
    "domain knowledge": {"domain", "industry", "business", "healthcare", "finance", "education", "ecommerce", "saas"},
    "obligations": {"obligation", "obligations", "shall", "must", "responsible", "duty", "duties"},
    "deadlines": {"deadline", "date", "duration", "timeline", "effective", "expiry", "termination"},
    "payment terms": {"payment", "fee", "fees", "invoice", "salary", "compensation", "amount", "budget"},
    "legal clauses": {"clause", "liability", "indemnity", "confidentiality", "governing", "law"},
    "risks": {"risk", "risks", "penalty", "breach", "liability", "non-compliance"},
    "exceptions": {"exception", "exceptions", "exclusion", "excluded", "limit", "limitations"},
    "research objective": {"objective", "research", "hypothesis", "problem", "question"},
    "methodology": {"method", "methodology", "experiment", "survey", "model", "approach"},
    "dataset/evidence": {"dataset", "data", "sample", "evidence", "participants", "source"},
    "results": {"result", "results", "finding", "findings", "accuracy", "performance"},
    "limitations": {"limitation", "limitations", "future work", "constraint"},
    "requirements": {"requirement", "requirements", "required", "mandatory", "criteria"},
    "scope": {"scope", "applies", "coverage", "included", "excluded"},
    "compliance obligations": {"compliance", "audit", "standard", "regulation", "approval"},
    "functional requirements": {"function", "feature", "requirement", "workflow", "capability"},
    "non-functional requirements": {"performance", "security", "scalability", "availability", "latency"},
    "architecture": {"architecture", "component", "service", "module", "system"},
    "interfaces": {"api", "endpoint", "integration", "interface", "schema"},
    "constraints": {"constraint", "constraints", "limit", "dependency", "assumption"},
}


def _strategy_for_types(type_a: str, type_b: str) -> dict:
    exact = COMPARISON_STRATEGIES.get((type_a, type_b))
    if exact:
        return exact
    if type_a == type_b:
        return {
            "name": f"{type_a} Gap Analysis",
            "dimensions": ["key topics", "objectives", "requirements", "constraints", "risks"],
            "weights": {"Topic/Purpose": 25, "Requirement Coverage": 35, "Gaps": 25, "Risks": 15},
        }
    return {
        "name": "Purpose-Aware Cross-Document Analysis",
        "dimensions": ["key topics", "objectives", "requirements", "constraints", "deliverables", "risks"],
        "weights": {"Purpose Fit": 25, "Requirement Fulfillment": 35, "Evidence Coverage": 25, "Risk/Gaps": 15},
    }


def _dimension_terms(dimension: str) -> set[str]:
    return DIMENSION_TERMS.get(dimension, set(_tokens(dimension)))


def _dimension_evidence(text: str, dimension: str, limit: int = 4) -> list[str]:
    terms = _dimension_terms(dimension)
    matches = []
    for unit in _comparison_units(text, limit=50):
        lowered = unit.lower()
        if any(term in lowered for term in terms):
            matches.append(_format_evidence(unit, max_chars=190))
        if len(matches) >= limit:
            break
    return matches


def _dimension_status(evidence_a: list[str], evidence_b: list[str], terms_a: set[str], terms_b: set[str]) -> str:
    if evidence_a and evidence_b:
        overlap = terms_a & terms_b
        return "Fully matched" if overlap else "Partially matched"
    if evidence_a or evidence_b:
        return "Missing / one-sided"
    return "Not found"


def build_intelligent_comparison_framework(document_a: str, document_b: str, question: str = "") -> str:
    type_a = _doc_type(document_a)
    type_b = _doc_type(document_b)
    strategy = _strategy_for_types(type_a, type_b)
    target = detect_compare_target(question)
    dimensions = strategy["dimensions"]
    weights = strategy["weights"]
    rows = []

    # Get comparison units and their embeddings
    units_a = _comparison_units(document_a, limit=36)
    units_b = _comparison_units(document_b, limit=36)
    embeddings_a = _embed_units(units_a)
    embeddings_b = _embed_units(units_b) if embeddings_a else []

    # Pass 1: Concurrent structured extraction
    struct_a, struct_b = _extract_both_structures(document_a, document_b, type_a, type_b)

    for dimension in dimensions:
        # BGE Embedding-based semantic evidence alignment
        evidence_a = _semantic_evidence_for_dimension(units_a, embeddings_a, dimension)
        evidence_b = _semantic_evidence_for_dimension(units_b, embeddings_b, dimension)
        
        score = 0.0
        if evidence_a and evidence_b:
            emb_ea = _embed_units([evidence_a[0]])
            emb_eb = _embed_units([evidence_b[0]]) if emb_ea else []
            if emb_ea and emb_eb:
                score = _cosine_similarity(emb_ea[0], emb_eb[0])
            else:
                score = _token_similarity(evidence_a[0], evidence_b[0])
                
        # Programmatic matching rules
        if not evidence_a and not evidence_b:
            status = "Not found"
        elif not evidence_a or not evidence_b:
            status = "Missing / one-sided"
        else:
            if _has_conflict(evidence_a[0], evidence_b[0], score):
                status = "Conflict"
            elif score >= 0.62:
                status = "Fully matched"
            else:
                status = "Partially matched"

        rows.append({
            "dimension": dimension,
            "document_a": "; ".join(evidence_a[:2]) or "Not found in Document A",
            "document_b": "; ".join(evidence_b[:2]) or "Not found in Document B",
            "status": status,
            "gap": "Compare exact evidence; missing or one-sided evidence is a gap." if status != "Fully matched" else "No major gap in extracted evidence.",
        })

    score_components = []
    for component, weight in weights.items():
        component_terms = _dimension_terms(component.lower())
        if not component_terms:
            related_rows = rows
        else:
            related_rows = [
                row for row in rows
                if set(_tokens(row["dimension"])) & component_terms or any(term in row["dimension"].lower() for term in component_terms)
            ] or rows
        matched_weight = sum(1 for row in related_rows if row["status"] == "Fully matched")
        partial_weight = sum(1 for row in related_rows if row["status"] == "Partially matched")
        ratio = (matched_weight + 0.5 * partial_weight) / max(1, len(related_rows))
        score_components.append({
            "name": component,
            "weight": weight,
            "ratio": ratio,
            "evidence": f"{matched_weight} fully matched and {partial_weight} partially matched relevant dimensions out of {len(related_rows)}.",
            "applicable": bool(related_rows),
        })

    score_result = calculate_weighted_percentage(score_components)
    score = score_result["percentage"]
    table_rows = "\n".join(
        "| {dimension} | {doc_a} | {doc_b} | {status} | {gap} |".format(
            dimension=row["dimension"].title(),
            doc_a=_format_table_cell(row["document_a"], max_chars=130),
            doc_b=_format_table_cell(row["document_b"], max_chars=130),
            status=row["status"],
            gap=_format_table_cell(row["gap"], max_chars=120),
        )
        for row in rows
    )
    score_text = _format_score_components(score_result["components"])

    json_blocks = (
        "Structured Extraction Baselines (Pass 1):\n"
        f"Document A ({type_a}) Extracted JSON:\n"
        f"```json\n{json.dumps(struct_a, indent=2, ensure_ascii=False)}\n```\n\n"
        f"Document B ({type_b}) Extracted JSON:\n"
        f"```json\n{json.dumps(struct_b, indent=2, ensure_ascii=False)}\n```\n"
    )

    return (
        "INTELLIGENT DOCUMENT COMPARISON FRAMEWORK - USE THIS INSTEAD OF GENERIC SEMANTIC SIMILARITY:\n"
        f"Document A classified type: {type_a}\n"
        f"Document B classified type: {type_b}\n"
        f"Comparison intent/strategy: {strategy['name']}\n"
        f"User comparison target detected: {target['label']}\n"
        "Critical rules:\n"
        "- Do not compare document wording; compare document meaning, purpose, requirements, and evidence.\n"
        "- Never assume different document types are poorly aligned because they serve different functions.\n"
        "- Prioritize requirement fulfillment and relevant dimensions over semantic similarity.\n"
        "- Explain every score using matched, partial, missing, additional strength, or risk evidence.\n"
        "- Ignore irrelevant dimensions for the detected document types.\n"
        f"Selected dimensions: {', '.join(dimensions)}\n"
        f"Overall category-derived score: {score}/100\n"
        "Score components:\n"
        f"{score_text}\n"
        f"Score calculation note: {score_result['calculation_note']}\n"
        "Structured comparison matrix:\n"
        "| Dimension | Document A Evidence | Document B Evidence | Status | Gap/Risk Meaning |\n"
        "|-----------|---------------------|---------------------|--------|------------------|\n"
        f"{table_rows}\n\n"
        f"{json_blocks}\n"
        "Final answer must include: Summary, Strengths, Weaknesses, Missing requirements/items, Risk assessment, Final fit/alignment assessment, and Recommendation.\n"
    )


def build_alignment_analysis(document_a: str, document_b: str, question: str = "", provider: str = "") -> str:
    """Create deterministic comparison signals for the LLM to use as a stable baseline."""
    if not (document_a or "").strip() or not (document_b or "").strip():
        return (
            "Deterministic alignment baseline:\n"
            "Alignment Score: Unable to calculate - both Document A and Document B are required.\n"
        )

    resume_job_fit = build_resume_job_fit_analysis(document_a, document_b, provider)
    if resume_job_fit:
        return resume_job_fit

    return build_intelligent_comparison_framework(document_a, document_b, question)



def missing_second_source_response(*, answer_time_ms: int, document_mode: str) -> dict:
    return {
        "answer": (
            "To compare your document, I need a second source.\n\n"
            "**How to add one:**\n"
            "1. Stay in **Compare** mode\n"
            "2. Paste a public URL in the **\"Compare with a webpage\"** panel above and click **Fetch**\n"
            "3. Then ask your question - I will compare your document against that page\n\n"
            "Alternatively, switch **Source -> Website** and I will compare your document against the current browser page."
        ),
        "confidence": "low",
        "sources": [],
        "suggestions": ["Fetch a webpage to compare", "Compare with current page", "Summarize my document"],
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "retrieval_time_ms": 0,
            "document_mode": document_mode,
        },
    }


def incomplete_compare_pair_response(
    *,
    answer_time_ms: int,
    retrieval_time_ms: int,
    has_document: bool,
    has_webpage: bool,
    document_mode: str,
) -> dict:
    missing = []
    if not has_document:
        missing.append("Document A - uploaded document")
    if not has_webpage:
        missing.append("Document B - webpage/fetched page")
    missing_text = ", ".join(missing) or "required comparison source"
    return {
        "answer": (
            "I cannot run a reliable comparison because the current compare pair is incomplete.\n\n"
            f"Missing: **{missing_text}**.\n\n"
            "Compare mode must compare exactly **Document A (uploaded document)** against "
            "**Document B (webpage/fetched page)**. I will not compare webpage-to-webpage or document-to-document."
        ),
        "confidence": "low",
        "sources": [],
        "suggestions": ["Upload document", "Fetch webpage", "Compare current pair"],
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "document_mode": document_mode,
            "has_document_context": has_document,
            "has_webpage_context": has_webpage,
        },
    }


def empty_compare_response(
    *,
    answer_time_ms: int,
    retrieval_time_ms: int,
    requires_index: bool,
    document_mode: str,
) -> dict:
    return {
        "answer": "I couldn't find relevant information in either the website index or the uploaded document for that question.",
        "requires_index": requires_index,
        "confidence": "low",
        "sources": [],
        "suggestions": ["Summarize the document", "Summarize this page", "Compare key points"],
        "metrics": {
            "answer_time_ms": answer_time_ms,
            "retrieval_time_ms": retrieval_time_ms,
            "context_chars": 0,
            "selected_chunks": 0,
            "confidence": "low",
            "document_mode": document_mode,
        },
    }


# ---------------------------------------------------------------------------
# Dynamic JSON templates & Two-Pass Extraction helpers
# ---------------------------------------------------------------------------

def _get_schema_description(doc_type: str) -> str:
    if doc_type == "Resume / CV":
        return """{
  "seniority_level_inferred": "Entry, Mid, Senior, Lead, or Executive",
  "calculated_total_years_experience": 5,
  "skills": ["List technical and soft skills found"],
  "experience": {
    "summary": "Summary of work experience and scope"
  },
  "education": ["Degrees and fields of study"],
  "certifications": ["List certifications"],
  "projects": ["List projects with tools/tech used"]
}"""
    elif doc_type == "Job Description":
        return """{
  "seniority_level": "Entry, Mid, Senior, Lead, or Executive",
  "required_experience": {
    "years_number": 3,
    "summary": "Exact quote of experience requirements"
  },
  "critical_must_haves": ["List of non-negotiable requirements (clearance, degrees, specific domain)"],
  "required_skills": ["Comprehensive list of tech/soft skills"],
  "preferred_skills": ["List preferred/nice-to-have skills"],
  "leadership_management_responsibilities": ["Team management, resourcing, performance reviews"],
  "client_facing_responsibilities": ["Client interactions, stakeholder management"],
  "core_responsibilities": ["Other major job duties"],
  "required_education": ["Required degrees/studies"],
  "required_certifications": ["Required certifications"]
}"""
    elif doc_type in ("Contract", "Policy Document"):
        return """{
  "scope": "Scope statement of policy/agreement",
  "obligations": ["List of obligations and rules"],
  "deadlines": ["List of dates, deadlines, and milestones"],
  "payments": ["Cost, pricing, fees, payment/salary details"],
  "risks": ["Compliance risks, penalties, liabilities"],
  "exceptions": ["Exclusions, exemptions, or limits"]
}"""
    elif doc_type == "Technical Specification":
        return """{
  "features": ["List of features and capabilities"],
  "interfaces": ["APIs, endpoints, integration schemas"],
  "constraints": ["Technical limits, dependencies, assumptions"],
  "non_functional": ["Performance, scalability, security requirements"]
}"""
    else:
        return """{
  "objectives": ["Primary objectives and purposes"],
  "claims": ["Key claims and factual assertions"],
  "gaps": ["Limitations, gaps, or unknowns"],
  "references": ["Sources, references, or links cited"]
}"""


def _parse_json_from_text(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n", "", text)
        text = re.sub(r"\n```$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
    return None


def _fallback_extraction(text: str, doc_type: str) -> dict:
    lowered = (text or "").lower()
    if doc_type == "Resume / CV":
        skills = list(_extract_skill_terms(text))
        years = _extract_years(text)
        edu = [term for term in EDUCATION_TERMS if term in lowered]
        certs = [term for term in CERTIFICATION_TERMS if term in lowered]
        return {
            "seniority_level_inferred": "Mid",
            "calculated_total_years_experience": years,
            "skills": skills,
            "experience": {"summary": f"Estimated {years} years of experience from CV text."},
            "education": edu,
            "certifications": certs,
            "projects": ["Project details extracted lexical check."] if "project" in lowered else []
        }
    elif doc_type == "Job Description":
        skills = list(_extract_skill_terms(text))
        years = _extract_years(text)
        lines = _requirement_lines(text, preferred=False)
        return {
            "seniority_level": "Mid",
            "critical_must_haves": ["Basic fallback requirement"],
            "required_skills": skills,
            "preferred_skills": [],
            "required_experience": {"years_number": years, "summary": f"Required {years} years of experience."},
            "leadership_management_responsibilities": [],
            "client_facing_responsibilities": [],
            "core_responsibilities": lines[:6],
            "required_education": [term for term in EDUCATION_TERMS if term in lowered],
            "required_certifications": [term for term in CERTIFICATION_TERMS if term in lowered]
        }
    elif doc_type in ("Contract", "Policy Document"):
        lines = _comparison_units(text, limit=10)
        return {
            "scope": "General contract/policy scope.",
            "obligations": [l[:120] for l in lines if any(t in l.lower() for t in ("must", "shall", "agree", "responsible"))][:5],
            "deadlines": [l[:120] for l in lines if any(t in l.lower() for t in ("date", "deadline", "timeline", "day", "month"))][:5],
            "payments": [l[:120] for l in lines if any(t in l.lower() for t in ("pay", "fee", "cost", "salary", "amount"))][:5],
            "risks": [l[:120] for l in lines if any(t in l.lower() for t in ("risk", "liability", "breach", "penalty"))][:5],
            "exceptions": [l[:120] for l in lines if any(t in l.lower() for t in ("except", "exclude", "unless", "limit"))][:5]
        }
    elif doc_type == "Technical Specification":
        lines = _comparison_units(text, limit=10)
        return {
            "features": [l[:120] for l in lines if any(t in l.lower() for t in ("feature", "support", "capability", "allow"))][:5],
            "interfaces": [l[:120] for l in lines if any(t in l.lower() for t in ("api", "endpoint", "interface", "schema"))][:5],
            "constraints": [l[:120] for l in lines if any(t in l.lower() for t in ("limit", "depend", "assume", "constraint"))][:5],
            "non_functional": [l[:120] for l in lines if any(t in l.lower() for t in ("performance", "security", "scalability", "speed"))][:5]
        }
    else:
        lines = _comparison_units(text, limit=6)
        return {
            "objectives": ["General purpose document."],
            "claims": [l[:120] for l in lines][:4],
            "gaps": ["No major gaps found in fallback mode."],
            "references": []
        }


def _extract_structure_with_fallback(text: str, doc_type: str) -> dict:
    if not text or not text.strip():
        return _fallback_extraction("", doc_type)
        
    cached = compare_cache.get_cached_structure(text)
    if cached:
        return cached
        
    try:
        from llm import generate_answer
        prompt = f"""You are a precise JSON extractor. Analyze the following document text (classified as '{doc_type}') and extract key attributes.
Extract EXACT language comprehensively. Do not summarize or omit major sections. Ensure all skills, tools, responsibilities, and duration metrics are captured exactly as written.
Respond ONLY with a valid JSON object. Do not include any intro, markdown formatting, backticks, or explanation.

Expected JSON Schema for document type '{doc_type}':
{_get_schema_description(doc_type)}

Text:
{text[:32000]}
"""
        res = generate_answer(
            context="You are a JSON document parser. Extract key fields.",
            question=prompt,
            force_provider="",
            concise_answer=True
        )
        answer = res.get("answer", "").strip()
        parsed = _parse_json_from_text(answer)
        if parsed:
            compare_cache.store_cached_structure(text, parsed)
            return parsed
    except Exception as e:
        print(f"LLM extraction failed, using fallback: {e}")
        
    fallback_res = _fallback_extraction(text, doc_type)
    compare_cache.store_cached_structure(text, fallback_res)
    return fallback_res


def _extract_both_structures(doc_a: str, doc_b: str, type_a: str, type_b: str) -> tuple[dict, dict]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(_extract_structure_with_fallback, doc_a, type_a)
        future_b = executor.submit(_extract_structure_with_fallback, doc_b, type_b)
        return future_a.result(), future_b.result()


def _semantic_evidence_for_dimension(units: list[str], embeddings: list[list[float]], dimension: str) -> list[str]:
    if not units or not embeddings:
        return []
    
    # Embed the dimension target
    dim_emb = _embed_units([dimension])
    if not dim_emb:
        # Fallback to lexical keyword check
        terms = _dimension_terms(dimension)
        return [u for u in units if any(term in u.lower() for term in terms)][:2]
        
    ranked = []
    for idx, unit in enumerate(units):
        similarity = _cosine_similarity(dim_emb[0], embeddings[idx])
        if similarity >= 0.40:
            ranked.append((similarity, unit))
            
    ranked.sort(reverse=True, key=lambda item: item[0])
    return [item[1] for item in ranked[:2]]
