from __future__ import annotations

import json
import re
import time
from collections import defaultdict

from llm import generate_answer
from scraper import clean_html_content
from handlers import compare_chat


ALLOWED_ROW_STATUSES = {
    "Match",
    "Partial Match",
    "Missing From A",
    "Missing From B",
    "Conflict",
    "Extra In A",
    "Extra In B",
    "Not Comparable",
}

ALLOWED_MATCH_QUALITIES = {
    "Perfect",
    "Excellent",
    "Good",
    "Partial",
    "Missing",
    "Must Confirm",
}

ROLE_FIT_GOAL_TERMS = {
    "role fit",
    "job fit",
    "resume fit",
    "candidate fit",
    "hiring",
    "recruiter",
    "job description",
    "jd",
}

JOB_TEXT_SIGNALS = {
    "job description",
    "responsibilities",
    "requirements",
    "required qualifications",
    "preferred qualifications",
    "basic qualifications",
    "minimum qualifications",
    "must have",
    "nice to have",
    "apply now",
    "role",
    "candidate",
    "we are hiring",
    "shift",
    "rotational shift",
    "relocation",
    "work location",
    "customer support",
    "operations",
    "audit",
    "quality audit",
    "sla",
    "root cause analysis",
    "process improvement",
    "stakeholder",
}

RESUME_TEXT_SIGNALS = {
    "resume",
    "curriculum vitae",
    "professional summary",
    "work experience",
    "employment",
    "education",
    "skills",
    "projects",
    "certifications",
    "linkedin",
    "github",
    "portfolio",
}


def _clean_compare_text(text: str) -> str:
    source = text or ""
    if "<" in source and ">" in source:
        return clean_html_content(source)
    lines = [" ".join(line.split()) for line in source.splitlines()]
    return "\n".join(line for line in lines if line)


def _signal_score(text: str, signals: set[str]) -> int:
    lowered = f" {(text or '').lower()} "
    score = 0
    for signal in signals:
        if signal in lowered:
            score += 3 if " " in signal else 1
    return score


def _is_role_fit_goal(compare_goal: str) -> bool:
    lowered = (compare_goal or "").lower()
    return any(term in lowered for term in ROLE_FIT_GOAL_TERMS)


def _resolve_goal_aware_types(clean_a: str, clean_b: str, compare_goal: str) -> tuple[str, str, dict]:
    type_a = compare_chat._doc_type(clean_a)
    type_b = compare_chat._doc_type(clean_b)
    metadata = {
        "goal": compare_goal or "Compare the two sources",
        "goal_aware": False,
        "initial_types": {"a": type_a, "b": type_b},
        "reason": "Standard independent source classification.",
    }

    if not _is_role_fit_goal(compare_goal):
        return type_a, type_b, metadata

    a_resume_score = _signal_score(clean_a, RESUME_TEXT_SIGNALS)
    b_resume_score = _signal_score(clean_b, RESUME_TEXT_SIGNALS)
    a_job_score = _signal_score(clean_a, JOB_TEXT_SIGNALS)
    b_job_score = _signal_score(clean_b, JOB_TEXT_SIGNALS)

    a_is_resume = type_a in {"Resume / CV", "Resume/Profile"} or a_resume_score >= max(3, a_job_score + 2)
    b_is_resume = type_b in {"Resume / CV", "Resume/Profile"} or b_resume_score >= max(3, b_job_score + 2)
    a_is_job = type_a == "Job Description" or a_job_score >= max(3, a_resume_score + 2)
    b_is_job = type_b == "Job Description" or b_job_score >= max(3, b_resume_score + 2)

    if a_is_resume and b_is_job:
        metadata.update({
            "goal_aware": True,
            "reason": "Role-fit goal selected; Source A has resume signals and Source B has job/role signals.",
            "signal_scores": {
                "a_resume": a_resume_score,
                "a_job": a_job_score,
                "b_resume": b_resume_score,
                "b_job": b_job_score,
            },
        })
        return "Resume / CV", "Job Description", metadata

    if a_is_job and b_is_resume:
        metadata.update({
            "goal_aware": True,
            "reason": "Role-fit goal selected; Source A has job/role signals and Source B has resume signals.",
            "signal_scores": {
                "a_resume": a_resume_score,
                "a_job": a_job_score,
                "b_resume": b_resume_score,
                "b_job": b_job_score,
            },
        })
        return "Job Description", "Resume / CV", metadata

    if type_a in {"Resume / CV", "Resume/Profile"} and b_job_score >= 2:
        metadata.update({
            "goal_aware": True,
            "reason": "Role-fit goal selected; Source B contains enough role requirement signals to compare as a job description.",
            "signal_scores": {
                "a_resume": a_resume_score,
                "a_job": a_job_score,
                "b_resume": b_resume_score,
                "b_job": b_job_score,
            },
        })
        return "Resume / CV", "Job Description", metadata

    if type_b in {"Resume / CV", "Resume/Profile"} and a_job_score >= 2:
        metadata.update({
            "goal_aware": True,
            "reason": "Role-fit goal selected; Source A contains enough role requirement signals to compare as a job description.",
            "signal_scores": {
                "a_resume": a_resume_score,
                "a_job": a_job_score,
                "b_resume": b_resume_score,
                "b_job": b_job_score,
            },
        })
        return "Job Description", "Resume / CV", metadata

    metadata.update({
        "reason": "Role-fit goal selected, but the sources did not contain enough resume/job signals to safely force recruiter-style comparison.",
        "signal_scores": {
            "a_resume": a_resume_score,
            "a_job": a_job_score,
            "b_resume": b_resume_score,
            "b_job": b_job_score,
        },
    })
    return type_a, type_b, metadata


def _compact_value(value, max_chars: int = 260) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def _tokens(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", text.lower())
        if token not in compare_chat.STOPWORDS
    }


def _numeric_markers(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    lowered = text.lower()
    markers = set(re.findall(r"(?:\$|rs\.?|inr|usd|eur|gbp)?\s?\b\d+(?:,\d{3})*(?:\.\d+)?\b\s?(?:%|k|lpa|days?|months?|years?|yrs?|per user|/month|monthly)?", lowered))
    markers.update(re.findall(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}\s+\d{4}\b", lowered))
    markers.update(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", lowered))
    return {" ".join(marker.split()) for marker in markers if marker.strip()}


def _row_status(value_a, value_b) -> tuple[str, float, str]:
    has_a = bool(_compact_value(value_a))
    has_b = bool(_compact_value(value_b))
    if not has_a and not has_b:
        return "Not Comparable", 0.0, "No evidence found in either source."
    if has_a and not has_b:
        return "Missing From B", 0.0, "This item appears only in Document A."
    if has_b and not has_a:
        return "Missing From A", 0.0, "This item appears only in Document B."

    numeric_a = _numeric_markers(value_a)
    numeric_b = _numeric_markers(value_b)
    if numeric_a and numeric_b and numeric_a != numeric_b:
        return "Conflict", 0.15, "Both sources contain numeric/date evidence, but the extracted values differ."

    terms_a = _tokens(value_a)
    terms_b = _tokens(value_b)
    if not terms_a and not terms_b:
        return "Partial Match", 0.5, "Both sources contain this field, but evidence is too sparse to score strongly."

    overlap = terms_a & terms_b
    overlap_ratio = len(overlap) / max(1, min(len(terms_a), len(terms_b)))
    if overlap_ratio >= 0.65:
        return "Match", 1.0, "Both sources contain strongly overlapping evidence."
    if overlap_ratio >= 0.25:
        return "Partial Match", 0.5, "Both sources discuss this area, but the evidence only partially overlaps."
    return "Conflict", 0.15, "Both sources contain this field, but the extracted evidence differs substantially."


def _as_list(value) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return [value]


def _norm_item(value) -> str:
    return " ".join(str(value or "").lower().split())


def _list_text(values) -> str:
    items = [str(item) for item in _as_list(values) if _compact_value(item)]
    return ", ".join(items)


def _matching_display(values, normalized_terms: set[str]) -> str:
    return _list_text([item for item in _as_list(values) if _norm_item(item) in normalized_terms])


def _years_required(value) -> int:
    if isinstance(value, dict):
        try:
            return int(value.get("years_number") or 0)
        except (TypeError, ValueError):
            return 0
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            import re
            m = re.search(r'\b(\d+)\+?\s*(?:years?|yrs?)\b', value.lower())
            if m: return int(m.group(1))
            if value.isdigit(): return int(value)
    except (TypeError, ValueError):
        pass
    return 0


def _display_requirement(value) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return ""
    if text.lower() in {"sql", "sla", "api", "aws", "gcp"}:
        return text.upper()
    return text[:1].upper() + text[1:]


def _status_impact(status: str, points: float = 0.0) -> str:
    if status == "Match":
        return "positive"
    if status == "Partial Match":
        return "partial"
    if status in {"Missing From A", "Missing From B"}:
        return "negative"
    if status == "Conflict":
        return "risk"
    if status in {"Extra In A", "Extra In B"}:
        return "positive" if points > 0 else "neutral"
    return "neutral"


def _match_quality(status: str, points: float = 0.0, impact: str = "") -> str:
    if status == "Match":
        if points >= 0.98:
            return "Perfect"
        if points >= 0.75:
            return "Excellent"
        return "Good"
    if status == "Partial Match":
        return "Partial"
    if status in {"Missing From A", "Missing From B"}:
        return "Missing"
    if status in {"Extra In A", "Extra In B"}:
        return "Good" if impact == "positive" or points > 0 else "Must Confirm"
    if status in {"Conflict", "Not Comparable"}:
        return "Must Confirm"
    return "Must Confirm"


def _make_row(
    *,
    dimension: str,
    key_a: str,
    key_b: str,
    evidence_a: str,
    evidence_b: str,
    status: str,
    points: float,
    reason: str,
    impact: str | None = None,
    match_quality: str | None = None,
) -> dict:
    if status not in ALLOWED_ROW_STATUSES:
        status = "Not Comparable"
        points = 0.0
        reason = "The comparison status was normalized to the allowed status vocabulary."
    resolved_impact = impact or _status_impact(status, points)
    resolved_quality = match_quality or _match_quality(status, points, resolved_impact)
    if resolved_quality not in ALLOWED_MATCH_QUALITIES:
        resolved_quality = _match_quality(status, points, resolved_impact)
    return {
        "dimension": dimension,
        "document_a_field": key_a,
        "document_b_field": key_b,
        "source_a_evidence": evidence_a or "Not found in Source A",
        "source_b_evidence": evidence_b or "Not found in Source B",
        "status": status,
        "impact": resolved_impact,
        "match_quality": resolved_quality,
        "score_contribution": points,
        "reason": reason,
    }


def _looks_like_resume_facts(struct: dict) -> bool:
    return any(key in struct for key in ("skills", "experience_years", "projects", "education", "certifications"))


def _looks_like_job_facts(struct: dict) -> bool:
    return any(key in struct for key in ("required_skills", "preferred_skills", "required_experience", "responsibilities", "required_education", "required_certifications"))


def _job_responsibilities(struct: dict) -> list:
    responsibilities = []
    for key in (
        "responsibilities",
        "core_responsibilities",
        "leadership_management_responsibilities",
        "client_facing_responsibilities",
    ):
        responsibilities.extend(_as_list(struct.get(key)))
    return responsibilities


def _normalize_resume_facts(struct: dict) -> dict:
    return {
        "skills": _as_list(struct.get("skills")),
        "experience_years": struct.get("calculated_total_years_experience", 0) or 0,
        "experience": struct.get("experience", {}),
        "projects": _as_list(struct.get("projects")),
        "education": _as_list(struct.get("education")),
        "certifications": _as_list(struct.get("certifications")),
    }


def _normalize_job_facts(struct: dict) -> dict:
    return {
        "required_skills": _as_list(struct.get("required_skills")),
        "preferred_skills": _as_list(struct.get("preferred_skills")),
        "required_experience": struct.get("required_experience", {}) or {},
        "responsibilities": _job_responsibilities(struct),
        "required_education": _as_list(struct.get("required_education")),
        "required_certifications": _as_list(struct.get("required_certifications")),
        "critical_must_haves": _as_list(struct.get("critical_must_haves")),
    }


def _normalize_structured_facts(struct: dict, doc_type: str) -> dict:
    if doc_type in {"Resume / CV", "Resume/Profile"}:
        return _normalize_resume_facts(struct)
    if doc_type == "Job Description":
        return _normalize_job_facts(struct)
    return struct


def pass_1_extract_structured_facts(clean_a: str, clean_b: str, type_a: str, type_b: str) -> dict:
    raw_a, raw_b = compare_chat._extract_both_structures(clean_a, clean_b, type_a, type_b)
    facts_a = _normalize_structured_facts(raw_a, type_a)
    facts_b = _normalize_structured_facts(raw_b, type_b)
    return {
        "raw": {"document_a": raw_a, "document_b": raw_b},
        "normalized": {"document_a": facts_a, "document_b": facts_b},
    }


def _role_fit_matrix(struct_a: dict, struct_b: dict, resume_is_a: bool = True) -> tuple[list[dict], dict]:
    resume = struct_a if resume_is_a else struct_b
    job = struct_b if resume_is_a else struct_a
    missing_resume_status = "Missing From A" if resume_is_a else "Missing From B"
    extra_resume_status = "Extra In A" if resume_is_a else "Extra In B"

    def evidence(resume_value, job_value) -> tuple[str, str]:
        resume_text = _compact_value(resume_value) or "Not found in resume"
        job_text = _compact_value(job_value) or "Not specified in job description"
        return (resume_text, job_text) if resume_is_a else (job_text, resume_text)

    def row(dimension, resume_key, job_key, resume_value, job_value, status, points, reason, impact=None, match_quality=None):
        evidence_a, evidence_b = evidence(resume_value, job_value)
        key_a, key_b = (resume_key, job_key) if resume_is_a else (job_key, resume_key)
        return _make_row(
            dimension=dimension,
            key_a=key_a,
            key_b=key_b,
            evidence_a=evidence_a,
            evidence_b=evidence_b,
            status=status,
            points=points,
            reason=reason,
            impact=impact,
            match_quality=match_quality,
        )

    def extra_resume_info(value, *, generally_useful: bool = False) -> tuple[str, str, str]:
        job_context = {
            "required_skills": job.get("required_skills"),
            "preferred_skills": job.get("preferred_skills"),
            "responsibilities": job.get("responsibilities"),
            "critical_must_haves": job.get("critical_must_haves"),
            "required_education": job.get("required_education"),
            "required_certifications": job.get("required_certifications"),
        }
        overlaps_role = bool(_tokens(value) & _tokens(job_context))
        if overlaps_role:
            return (
                "positive",
                "Good",
                "It is not listed as a direct requirement, but it supports role responsibilities or role keywords.",
            )
        if generally_useful:
            return (
                "positive",
                "Good",
                "It is not listed as a direct requirement, but it can strengthen the candidate profile for this role.",
            )
        return (
            "neutral",
            "Must Confirm",
            "It is additional resume information, but the job description does not show enough evidence to treat it as a role advantage.",
        )

    rows = []

    resume_skills = {_norm_item(skill) for skill in _as_list(resume.get("skills")) if _norm_item(skill)}
    required_skills = {_norm_item(skill) for skill in _as_list(job.get("required_skills")) if _norm_item(skill)}
    preferred_skills = {_norm_item(skill) for skill in _as_list(job.get("preferred_skills")) if _norm_item(skill)}
    matched_required = sorted(required_skills & resume_skills)
    missing_required = sorted(required_skills - resume_skills)
    matched_preferred = sorted(preferred_skills & resume_skills)
    missing_preferred = sorted(preferred_skills - resume_skills)
    extra_skills = sorted(resume_skills - required_skills - preferred_skills)

    for required_skill in sorted(required_skills):
        display = _display_requirement(required_skill)
        matched = required_skill in resume_skills
        rows.append(row(
            f"Required Skill: {display}",
            "skills",
            "required_skills",
            _matching_display(resume.get("skills"), {required_skill}) if matched else "",
            f"{display} required in job description",
            "Match" if matched else missing_resume_status,
            1.0 if matched else 0.0,
            "The required skill appears in the resume." if matched else "The job description requires this skill, but the resume does not show it.",
            "positive" if matched else "negative",
            "Perfect" if matched else "Missing",
        ))

    for preferred_skill in sorted(preferred_skills):
        display = _display_requirement(preferred_skill)
        matched = preferred_skill in resume_skills
        rows.append(row(
            f"Preferred Skill: {display}",
            "skills",
            "preferred_skills",
            _matching_display(resume.get("skills"), {preferred_skill}) if matched else "",
            f"{display} preferred in job description",
            "Match" if matched else "Partial Match",
            0.75 if matched else 0.25,
            "The preferred skill appears in the resume." if matched else "This is preferred rather than mandatory, but it is not visible in the resume.",
            "positive" if matched else "partial",
            "Excellent" if matched else "Partial",
        ))

    if required_skills:
        ratio = len(matched_required) / max(1, len(required_skills))
        if ratio >= 0.85:
            status, impact = "Match", "positive"
            quality = "Perfect" if ratio >= 0.98 else "Excellent"
            reason = "Most required job skills are present in the resume."
        elif matched_required:
            status, impact = "Partial Match", "partial"
            quality = "Partial"
            reason = "Some required job skills are present, but required skills are missing."
        else:
            status, impact = missing_resume_status, "negative"
            quality = "Missing"
            reason = "The job description requires these skills, but the resume does not show them."
        rows.append(row(
            "Skills vs Required Skills",
            "skills",
            "required_skills",
            _matching_display(resume.get("skills"), set(matched_required)) or _list_text(resume.get("skills")),
            _list_text(job.get("required_skills")),
            status,
            ratio,
            f"{reason} Missing required skills: {_list_text(missing_required) or 'none'}.",
            impact,
            quality,
        ))
    elif resume_skills:
        extra_impact, extra_quality, extra_reason = extra_resume_info(resume.get("skills"))
        rows.append(row(
            "Skills vs Required Skills",
            "skills",
            "required_skills",
            _list_text(resume.get("skills")),
            "",
            extra_resume_status,
            0.0,
            f"The resume lists skills, but the job description does not state required skills. {extra_reason} This is not a conflict.",
            extra_impact,
            extra_quality,
        ))

    if preferred_skills:
        ratio = len(matched_preferred) / max(1, len(preferred_skills))
        if ratio >= 0.75:
            status, impact = "Match", "positive"
            quality = "Excellent"
            reason = "Preferred skills are strongly represented in the resume."
        elif matched_preferred:
            status, impact = "Partial Match", "partial"
            quality = "Good"
            reason = "Some preferred skills are present in the resume."
        else:
            status, impact = "Partial Match", "partial"
            quality = "Partial"
            reason = "Preferred skills are not hard requirements, but they are not visible in the resume."
        rows.append(row(
            "Skills vs Preferred Skills",
            "skills",
            "preferred_skills",
            _matching_display(resume.get("skills"), set(matched_preferred)) or _list_text(resume.get("skills")),
            _list_text(job.get("preferred_skills")),
            status,
            ratio * 0.75,
            f"{reason} Missing preferred skills: {_list_text(missing_preferred) or 'none'}.",
            impact,
            quality,
        ))

    if extra_skills:
        extra_impact, extra_quality, extra_reason = extra_resume_info(extra_skills)
        rows.append(row(
            "Extra Resume Skills",
            "skills",
            "required_skills",
            _matching_display(resume.get("skills"), set(extra_skills)),
            "No matching requirement stated",
            extra_resume_status,
            0.0,
            f"These resume skills are not requested explicitly. {extra_reason}",
            extra_impact,
            extra_quality,
        ))

    resume_years = int(resume.get("experience_years") or 0)
    job_years = _years_required(job.get("required_experience"))
    if job_years:
        rows.append(row(
            f"Experience Requirement: {job_years}+ year(s)",
            "experience_years",
            "required_experience",
            f"{resume_years} year(s) experience" if resume_years else "",
            _compact_value(job.get("required_experience")),
            "Match" if resume_years >= job_years else ("Partial Match" if resume_years > 0 else missing_resume_status),
            1.0 if resume_years >= job_years else (min(1.0, resume_years / max(1, job_years)) if resume_years > 0 else 0.0),
            "The resume meets or exceeds the stated experience requirement." if resume_years >= job_years else ("The resume shows some experience, but below the stated minimum." if resume_years > 0 else "The job states a years-of-experience requirement that is not visible in the resume."),
            "positive" if resume_years >= job_years else ("partial" if resume_years > 0 else "negative"),
            "Perfect" if resume_years >= job_years else ("Partial" if resume_years > 0 else "Missing"),
        ))
    if job_years:
        ratio = min(1.0, resume_years / max(1, job_years))
        if ratio >= 1.0:
            status, impact = "Match", "positive"
            quality = "Perfect"
            reason = "The resume meets or exceeds the job's stated experience requirement."
        elif resume_years > 0:
            status, impact = "Partial Match", "partial"
            quality = "Partial"
            reason = "The resume has relevant experience but below the job's stated minimum."
        else:
            status, impact = missing_resume_status, "negative"
            quality = "Missing"
            reason = "The job states an experience requirement, but the resume does not show years of experience."
        rows.append(row(
            "Experience Years vs Required Experience",
            "experience_years",
            "required_experience",
            f"{resume_years} year(s) experience" if resume_years else "",
            _compact_value(job.get("required_experience")),
            status,
            ratio,
            reason,
            impact,
            quality,
        ))
    elif resume_years:
        extra_impact, extra_quality, extra_reason = extra_resume_info(resume.get("experience"), generally_useful=True)
        rows.append(row(
            "Experience Years vs Required Experience",
            "experience_years",
            "required_experience",
            f"{resume_years} year(s) experience",
            "No explicit years requirement",
            extra_resume_status,
            0.0,
            f"The job description does not specify a minimum experience requirement. {extra_reason} This is not a conflict.",
            extra_impact,
            extra_quality,
        ))

    responsibilities = _as_list(job.get("responsibilities"))
    resume_project_text = " ".join(_list_text(resume.get(key)) for key in ("projects", "experience", "skills"))
    confirmation_terms = {"shift", "rotational", "relocation", "location", "travel", "willing", "onsite", "night", "weekend", "hybrid"}
    for idx, responsibility in enumerate(responsibilities[:10], start=1):
        resp_text = _compact_value(responsibility, 180)
        resp_tokens = _tokens(resp_text)
        resume_terms = _tokens(resume_project_text)
        overlap = resp_tokens & resume_terms
        requires_confirmation = bool(resp_tokens & confirmation_terms)
        if requires_confirmation:
            status, points, impact, quality = "Not Comparable", 0.0, "neutral", "Must Confirm"
            reason = "This is a role condition or preference that the user should confirm directly; it should not be treated as a resume conflict."
            resume_evidence = ""
        elif overlap:
            status, points, impact, quality = "Partial Match", 0.5, "partial", "Partial"
            reason = "The resume has related evidence, but the responsibility should be backed with a clearer example."
            resume_evidence = _compact_value(resume_project_text, 180)
        else:
            status, points, impact, quality = missing_resume_status, 0.0, "negative", "Missing"
            reason = "The job description lists this requirement/responsibility, but clear resume evidence was not found."
            resume_evidence = ""
        rows.append(row(
            f"Requirement: {resp_text[:70]}",
            "projects",
            "responsibilities",
            resume_evidence,
            resp_text,
            status,
            points,
            reason,
            impact,
            quality,
        ))
    if responsibilities:
        resp_terms = _tokens(responsibilities)
        resume_terms = _tokens(resume_project_text)
        overlap_ratio = len(resp_terms & resume_terms) / max(1, min(len(resp_terms), len(resume_terms) or 1))
        if overlap_ratio >= 0.45:
            status, impact, points = "Match", "positive", 1.0
            quality = "Excellent"
            reason = "Resume projects or experience align with job responsibilities."
        elif overlap_ratio > 0:
            status, impact, points = "Partial Match", "partial", 0.5
            quality = "Partial"
            reason = "Resume evidence partially overlaps with job responsibilities."
        else:
            status, impact, points = missing_resume_status, "negative", 0.0
            quality = "Missing"
            reason = "Job responsibilities are stated, but the resume does not show clear matching project or experience evidence."
        rows.append(row(
            "Projects vs Responsibilities",
            "projects",
            "responsibilities",
            _list_text(resume.get("projects")) or _compact_value(resume.get("experience")),
            _list_text(responsibilities),
            status,
            points,
            reason,
            impact,
            quality,
        ))
    elif _as_list(resume.get("projects")):
        extra_impact, extra_quality, extra_reason = extra_resume_info(resume.get("projects"), generally_useful=True)
        rows.append(row(
            "Projects vs Responsibilities",
            "projects",
            "responsibilities",
            _list_text(resume.get("projects")),
            "No explicit responsibilities stated",
            extra_resume_status,
            0.0,
            f"The job description does not state matching responsibilities. {extra_reason} This is not a conflict.",
            extra_impact,
            extra_quality,
        ))

    EDUCATION_LEVELS = {
        "high school": 1, "high school diploma": 1, "ged": 1,
        "diploma": 2, "associate": 3, "associates": 3,
        "bachelor": 4, "bachelors": 4, "b.tech": 4, "btech": 4, "b.e": 4, "be": 4,
        "b.sc": 4, "bsc": 4, "b.a": 4, "ba": 4, "degree": 4, "engineering": 4, "computer science": 4,
        "master": 5, "masters": 5, "m.tech": 5, "mtech": 5, "m.e": 5, "me": 5,
        "m.sc": 5, "msc": 5, "m.a": 5, "ma": 5, "mba": 5,
        "phd": 6, "doctorate": 6
    }

    for dimension, resume_key, job_key in (
        ("Education vs Required Education", "education", "required_education"),
        ("Certifications vs Required Certifications", "certifications", "required_certifications"),
    ):
        resume_values = {_norm_item(item) for item in _as_list(resume.get(resume_key)) if _norm_item(item)}
        job_values = {_norm_item(item) for item in _as_list(job.get(job_key)) if _norm_item(item)}
        matched = sorted(resume_values & job_values)
        missing = sorted(job_values - resume_values)
        singular = "Education" if resume_key == "education" else "Certification"
        for requirement in sorted(job_values):
            display = _display_requirement(requirement)
            is_match = requirement in resume_values
            exceeds = False
            
            if resume_key == "education" and not is_match:
                req_level = EDUCATION_LEVELS.get(requirement, 0)
                if req_level > 0:
                    for res_edu in resume_values:
                        res_level = EDUCATION_LEVELS.get(res_edu, 0)
                        if res_level > req_level:
                            exceeds = True
                            break
                    if exceeds:
                        is_match = True

            if exceeds:
                if requirement not in matched:
                    matched.append(requirement)
                if requirement in missing:
                    missing.remove(requirement)
                rows.append(row(
                    f"{singular} Requirement: {display}",
                    resume_key,
                    job_key,
                    _list_text(resume.get(resume_key)),
                    f"{display} required in job description",
                    "Match",
                    1.0,
                    f"The candidate's education exceeds the {display} requirement.",
                    "positive",
                    "Perfect",
                ))
            else:
                rows.append(row(
                    f"{singular} Requirement: {display}",
                    resume_key,
                    job_key,
                    _matching_display(resume.get(resume_key), {requirement}) if is_match else "",
                    f"{display} required in job description",
                    "Match" if is_match else missing_resume_status,
                    1.0 if is_match else 0.0,
                    f"The resume satisfies this {singular.lower()} requirement." if is_match else f"The job description requires this {singular.lower()} item, but it is not visible in the resume.",
                    "positive" if is_match else "negative",
                    "Perfect" if is_match else "Missing",
                ))
        if job_values:
            ratio = len(matched) / max(1, len(job_values))
            if ratio >= 0.75:
                status, impact = "Match", "positive"
                quality = "Perfect" if ratio >= 0.98 else "Excellent"
                reason = f"The resume satisfies the stated {dimension.lower()} requirement."
            elif matched:
                status, impact = "Partial Match", "partial"
                quality = "Partial"
                reason = f"The resume partially satisfies the stated {dimension.lower()} requirement."
            else:
                status, impact = missing_resume_status, "negative"
                quality = "Missing"
                reason = f"The job description states a {dimension.lower()} requirement that is not visible in the resume."
            rows.append(row(
                dimension,
                resume_key,
                job_key,
                _list_text(resume.get(resume_key)),
                _list_text(job.get(job_key)),
                status,
                ratio,
                f"{reason} Missing: {_list_text(missing) or 'none'}.",
                impact,
                quality,
            ))
        elif resume_values:
            extra_impact, extra_quality, extra_reason = extra_resume_info(resume.get(resume_key))
            rows.append(row(
                dimension,
                resume_key,
                job_key,
                _list_text(resume.get(resume_key)),
                f"No explicit {dimension.lower()} requirement",
                extra_resume_status,
                0.0,
                f"The resume includes {dimension.lower()} evidence, but the job description does not require it. {extra_reason} This is not a gap or conflict.",
                extra_impact,
                extra_quality,
            ))

    if not rows:
        rows.append(row(
            "Role Fit",
            "resume",
            "job_description",
            "No structured resume evidence found",
            "No structured job requirements found",
            "Not Comparable",
            0.0,
            "Could not extract enough role-fit fields to score the resume against the job description.",
            "neutral",
            "Must Confirm",
        ))

    weights = {
        "Skills vs Required Skills": 35,
        "Skills vs Preferred Skills": 10,
        "Experience Years vs Required Experience": 25,
        "Projects vs Responsibilities": 15,
        "Education vs Required Education": 10,
        "Certifications vs Required Certifications": 5,
    }
    score_components = []
    for role_row in rows:
        dimension = role_row["dimension"]
        weight = weights.get(dimension, 0)
        applicable = weight > 0 and role_row["status"] not in {extra_resume_status, "Not Comparable"}
        score_components.append({
            "name": dimension,
            "weight": weight,
            "ratio": role_row["score_contribution"],
            "evidence": role_row["reason"],
            "applicable": applicable,
        })
    score_result = compare_chat.calculate_weighted_percentage(score_components)
    score = score_result["percentage"]
    if score >= 85:
        verdict = "Strong role fit"
    elif score >= 70:
        verdict = "Good role fit"
    elif score >= 50:
        verdict = "Partial role fit"
    elif score >= 30:
        verdict = "Weak role fit"
    else:
        verdict = "Low role fit"

    status_counts: dict[str, int] = defaultdict(int)
    impact_counts: dict[str, int] = defaultdict(int)
    quality_counts: dict[str, int] = defaultdict(int)
    for role_row in rows:
        status_counts[role_row["status"]] += 1
        impact_counts[role_row.get("impact", "neutral")] += 1
        quality_counts[role_row.get("match_quality", "Must Confirm")] += 1

    return rows, {
        "score": score,
        "verdict": verdict,
        "applicable_rows": len([component for component in score_result["components"] if component.get("applicable", True)]),
        "status_counts": dict(status_counts),
        "impact_counts": dict(impact_counts),
        "quality_counts": dict(quality_counts),
        "allowed_statuses": sorted(ALLOWED_ROW_STATUSES),
        "allowed_match_qualities": sorted(ALLOWED_MATCH_QUALITIES),
        "components": score_result["components"],
        "calculation": "Role-fit score penalizes missing job requirements only. Extra resume evidence is treated as positive or neutral, not as a conflict.",
        "comparison_strategy": "role_fit_asymmetric",
    }


def _comparison_matrix(struct_a: dict, struct_b: dict) -> tuple[list[dict], dict]:
    if _looks_like_resume_facts(struct_a) and _looks_like_job_facts(struct_b):
        return _role_fit_matrix(struct_a, struct_b, resume_is_a=True)
    if _looks_like_job_facts(struct_a) and _looks_like_resume_facts(struct_b):
        return _role_fit_matrix(struct_a, struct_b, resume_is_a=False)

    comparable_pairs = [
        ("skills", "required_skills", "Skills vs Required Skills", "if_b_exists"),
        ("skills", "preferred_skills", "Skills vs Preferred Skills", "if_b_exists"),
        ("experience_years", "required_experience", "Experience Years vs Required Experience", "if_b_exists"),
        ("experience", "required_experience", "Experience Summary vs Required Experience", "if_b_exists"),
        ("experience", "responsibilities", "Experience vs Responsibilities", "if_b_exists"),
        ("projects", "responsibilities", "Projects vs Responsibilities", "if_b_exists"),
        ("education", "required_education", "Education vs Required Education", "if_b_exists"),
        ("certifications", "required_certifications", "Certifications vs Required Certifications", "if_b_exists"),
        ("skills", "critical_must_haves", "Skills vs Critical Must-Haves", "if_b_exists"),
        ("features", "features", "Features", "if_either_exists"),
        ("obligations", "obligations", "Obligations", "if_either_exists"),
        ("deadlines", "deadlines", "Deadlines", "if_either_exists"),
        ("payments", "payments", "Payments", "if_either_exists"),
        ("risks", "risks", "Risks", "if_either_exists"),
        ("objectives", "objectives", "Objectives", "if_either_exists"),
        ("claims", "claims", "Claims", "if_either_exists"),
    ]
    rows = []
    status_counts: dict[str, int] = defaultdict(int)
    consumed_a = set()
    consumed_b = set()

    def add_row(dimension: str, key_a: str, key_b: str, unmatched_extra: bool = False) -> None:
        value_a = struct_a.get(key_a)
        value_b = struct_b.get(key_b)
        status, points, reason = _row_status(value_a, value_b)
        if unmatched_extra and status == "Missing From B":
            status = "Extra In A"
            reason = "This field appears as additional information in Source A."
        elif unmatched_extra and status == "Missing From A":
            status = "Extra In B"
            reason = "This field appears as additional information in Source B."
        if status not in ALLOWED_ROW_STATUSES:
            status = "Not Comparable"
            points = 0.0
            reason = "The comparison status was normalized to the allowed status vocabulary."
        status_counts[status] += 1
        impact = _status_impact(status, points)
        rows.append({
            "dimension": dimension,
            "document_a_field": key_a,
            "document_b_field": key_b,
            "source_a_evidence": _compact_value(value_a) or "Not found in Source A",
            "source_b_evidence": _compact_value(value_b) or "Not found in Source B",
            "status": status,
            "impact": impact,
            "match_quality": _match_quality(status, points, impact),
            "score_contribution": points,
            "reason": reason,
        })

    for key_a, key_b, dimension, mode in comparable_pairs:
        should_add = key_b in struct_b if mode == "if_b_exists" else (key_a in struct_a or key_b in struct_b)
        if should_add:
            add_row(dimension, key_a, key_b)
            consumed_a.add(key_a)
            consumed_b.add(key_b)

    remaining_keys = sorted((set(struct_a.keys()) - consumed_a) | (set(struct_b.keys()) - consumed_b))
    for key in remaining_keys:
        add_row(key.replace("_", " ").title(), key, key, unmatched_extra=True)

    score_components = [
        {
            "name": row["dimension"],
            "weight": 1,
            "ratio": row["score_contribution"],
            "evidence": row["reason"],
            "applicable": row["status"] != "Not Comparable",
        }
        for row in rows
    ]
    score_result = compare_chat.calculate_weighted_percentage(score_components)
    score = score_result["percentage"]
    applicable_rows = len([component for component in score_result["components"] if component.get("applicable", True)])
    if score >= 85:
        verdict = "Strong alignment"
    elif score >= 70:
        verdict = "Good alignment"
    elif score >= 50:
        verdict = "Partial alignment"
    elif score >= 30:
        verdict = "Weak alignment"
    else:
        verdict = "Low alignment"

    return rows, {
        "score": score,
        "verdict": verdict,
        "applicable_rows": applicable_rows,
        "status_counts": dict(status_counts),
        "allowed_statuses": sorted(ALLOWED_ROW_STATUSES),
        "allowed_match_qualities": sorted(ALLOWED_MATCH_QUALITIES),
        "quality_counts": dict(defaultdict(int, {quality: sum(1 for row in rows if row.get("match_quality") == quality) for quality in ALLOWED_MATCH_QUALITIES})),
        "components": score_result["components"],
        "calculation": score_result["calculation_note"],
    }


def pass_2_compare_extracted_facts(facts_a: dict, facts_b: dict) -> dict:
    table, score_details = _comparison_matrix(facts_a, facts_b)
    return {
        "comparison_table": table,
        "score_details": score_details,
        "score": score_details["score"],
        "verdict": score_details["verdict"],
    }


def _rows_with_status(rows: list[dict], statuses: set[str]) -> list[dict]:
    return [row for row in rows if row.get("status") in statuses]


def _recommendation(score: int, rows: list[dict]) -> str:
    missing_a = len(_rows_with_status(rows, {"Missing From A"}))
    conflicts = len(_rows_with_status(rows, {"Conflict"}))
    if score >= 85:
        return "Proceed with confidence; only minor clarification may be needed."
    if score >= 70:
        return "Proceed, but review partial matches and confirm any important edge cases."
    if score >= 50:
        return "Use with caution; address the missing and partial areas before relying on the alignment."
    if missing_a or conflicts:
        return "Do not treat this as a strong match until missing requirements and conflicts are resolved."
    return "The sources have low alignment; review whether these are the right documents to compare."


def _final_decision(score: int, rows: list[dict], score_details: dict) -> dict:
    conflicts = len(_rows_with_status(rows, {"Conflict"}))
    missing = len(_rows_with_status(rows, {"Missing From A", "Missing From B"}))
    partial = len(_rows_with_status(rows, {"Partial Match"}))
    must_confirm = sum(1 for row in rows if row.get("match_quality") == "Must Confirm")
    strategy = score_details.get("comparison_strategy", "generic")

    if strategy == "role_fit_asymmetric":
        if score >= 75 and conflicts == 0 and missing <= 1:
            decision = "Apply"
            reason = "The resume aligns well with the role, and there are no major blocking conflicts."
        elif score >= 45 and conflicts <= 1:
            decision = "Apply with caution"
            reason = "There is usable alignment, but missing, partial, or must-confirm items should be addressed before applying."
        else:
            decision = "Skip"
            reason = "The role-fit score is low or the comparison shows too many missing/conflicting requirements."
    else:
        if score >= 80 and conflicts == 0:
            decision = "Apply"
            reason = "The sources show strong alignment with no major conflicts."
        elif score >= 50 or partial or must_confirm:
            decision = "Apply with caution"
            reason = "The sources have partial alignment or unresolved items that should be reviewed first."
        else:
            decision = "Skip"
            reason = "The sources do not align enough to treat this as a good match."

    return {
        "decision": decision,
        "reason": reason,
        "signals": {
            "score": score,
            "conflicts": conflicts,
            "missing": missing,
            "partial": partial,
            "must_confirm": must_confirm,
        },
    }


def _dedupe_preserve_order(items: list[str], limit: int = 12) -> list[str]:
    seen = set()
    cleaned = []
    for item in items:
        text = " ".join(str(item or "").strip().split())
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _resume_improvement_suggestions(rows: list[dict], score_details: dict) -> dict:
    if score_details.get("comparison_strategy") != "role_fit_asymmetric":
        return {}

    missing_or_partial = [
        row for row in rows
        if row.get("status") in {"Missing From A", "Missing From B", "Partial Match"}
        or row.get("match_quality") in {"Missing", "Partial", "Must Confirm"}
    ]
    keyword_candidates = []
    for row in missing_or_partial:
        if row.get("status") in {"Missing From A", "Missing From B", "Partial Match"}:
            keyword_candidates.extend(
                token.upper() if token in {"sql", "sla"} else token.title()
                for token in sorted(_tokens(row.get("source_b_evidence")))
                if len(token) > 2 and token not in compare_chat.STOPWORDS
            )
    missing_keywords = _dedupe_preserve_order(keyword_candidates, limit=14)

    what_to_add = []
    cover_line_parts = []
    for row in missing_or_partial:
        dimension = row.get("dimension", "Role requirement")
        source_b = row.get("source_b_evidence", "the job description")
        if row.get("match_quality") == "Must Confirm" or "shift" in source_b.lower() or "relocation" in source_b.lower():
            what_to_add.append(f"Confirm clearly for {dimension}: {source_b}")
            continue
        if row.get("status") in {"Missing From A", "Missing From B"}:
            what_to_add.append(f"Add resume evidence for {dimension}: {source_b}")
        elif row.get("status") == "Partial Match":
            what_to_add.append(f"Strengthen {dimension} with measurable examples tied to: {source_b}")

    positive_rows = [
        row for row in rows
        if row.get("impact") == "positive" and row.get("status") in {"Match", "Partial Match", "Extra In A", "Extra In B"}
    ]
    for row in positive_rows[:3]:
        cover_line_parts.append(row.get("dimension", "relevant experience"))

    cover_letter_line = ""
    if cover_line_parts:
        cover_letter_line = (
            "I can bring relevant experience across "
            f"{', '.join(_dedupe_preserve_order(cover_line_parts, limit=3))} "
            "and I am ready to align my work with the role's stated priorities."
        )
    elif missing_keywords:
        cover_letter_line = (
            "I am interested in this role because it aligns with my ability to learn quickly, "
            f"communicate clearly, and contribute to {', '.join(missing_keywords[:3])}."
        )

    return {
        "missing_keywords": missing_keywords,
        "what_to_add": _dedupe_preserve_order(what_to_add, limit=8),
        "cover_letter_line": cover_letter_line,
    }


def _source_boundary_package(label_a: str, label_b: str, type_a: str, type_b: str, struct_a: dict, struct_b: dict) -> str:
    source_a = {
        "label": label_a,
        "type": type_a,
        "allowed_facts": struct_a,
    }
    source_b = {
        "label": label_b,
        "type": type_b,
        "allowed_facts": struct_b,
    }
    return (
        "SOURCE A ONLY:\n"
        f"```json\n{json.dumps(source_a, ensure_ascii=False, indent=2)}\n```\n\n"
        "SOURCE B ONLY:\n"
        f"```json\n{json.dumps(source_b, ensure_ascii=False, indent=2)}\n```"
    )


def build_compare_tool_payload(
    document_a: str,
    document_b: str,
    compare_goal: str = "Compare the two sources",
    labels: dict | None = None,
) -> dict:
    started_at = time.perf_counter()
    labels = labels or {}
    label_a = (labels.get("a") or "Document A").strip() or "Document A"
    label_b = (labels.get("b") or "Document B").strip() or "Document B"
    goal = (compare_goal or "Compare the two sources").strip()

    clean_a = _clean_compare_text(document_a)
    clean_b = _clean_compare_text(document_b)
    if len(clean_a.strip()) < 20:
        raise ValueError("Document A does not contain enough readable text to compare.")
    if len(clean_b.strip()) < 20:
        raise ValueError("Document B does not contain enough readable text to compare.")

    type_a, type_b, type_resolution = _resolve_goal_aware_types(clean_a, clean_b, goal)
    pass_1 = pass_1_extract_structured_facts(clean_a, clean_b, type_a, type_b)
    raw_struct_a = pass_1["raw"]["document_a"]
    raw_struct_b = pass_1["raw"]["document_b"]
    facts_a = pass_1["normalized"]["document_a"]
    facts_b = pass_1["normalized"]["document_b"]
    pass_2 = pass_2_compare_extracted_facts(facts_a, facts_b)
    table = pass_2["comparison_table"]
    score_details = pass_2["score_details"]
    score = pass_2["score"]
    verdict = pass_2["verdict"]
    resume_improvements = _resume_improvement_suggestions(table, score_details)
    final_decision = _final_decision(score, table, score_details)

    result = {
        "ok": True,
        "tool": "compare",
        "reused_building_blocks": {
            "compare_chat.py": "kept",
            "_doc_type": "used for independent source classification",
            "_extract_both_structures": "used for pass 1 extraction",
            "_extract_structure_with_fallback": "used through _extract_both_structures",
            "compare_cache.py": "kept for chat-era compatibility; not used by the dedicated Compare Tool hot path",
            "calculate_weighted_percentage": "used for deterministic score calculation",
            "build_resume_job_fit_analysis": "kept for specialist resume/JD baseline support",
            "build_intelligent_comparison_framework": "kept for broad comparison framework support",
            "/webpage-content": "reused by frontend Source B URL fetch",
            "/document/upload": "reused by frontend Source A/Source B document extraction",
        },
        "source_boundary_rules": [
            "Never copy facts from Document A into Document B.",
            "Never copy facts from Document B into Document A.",
            "Every claim must identify whether the evidence came from Document A, Document B, or both.",
            "If a fact is absent from one source, mark it Missing From A or Missing From B.",
        ],
        "labels": {"a": label_a, "b": label_b},
        "document_types": {"a": type_a, "b": type_b},
        "type_resolution": type_resolution,
        "compare_goal": goal,
        "score": score,
        "verdict": verdict,
        "final_decision": final_decision["decision"],
        "decision_reason": final_decision["reason"],
        "decision_signals": final_decision["signals"],
        "allowed_statuses": sorted(ALLOWED_ROW_STATUSES),
        "matches": _rows_with_status(table, {"Match"}),
        "partial_matches": _rows_with_status(table, {"Partial Match"}),
        "missing_from_a": _rows_with_status(table, {"Missing From A"}),
        "missing_from_b": _rows_with_status(table, {"Missing From B"}),
        "conflicts": _rows_with_status(table, {"Conflict"}),
        "extra_strengths": _rows_with_status(table, {"Extra In A", "Extra In B"}),
        "comparison_table": table,
        "two_pass_pipeline": {
            "pass_1": "Extract structured facts independently for Document A and Document B.",
            "pass_2": "Compare only the extracted facts using the selected comparison goal, never raw mixed text.",
        },
        "structured_extraction": {
            "raw": {"document_a": raw_struct_a, "document_b": raw_struct_b},
            "normalized": {"document_a": facts_a, "document_b": facts_b},
        },
        "score_details": score_details,
        "resume_improvements": resume_improvements,
        "recommendation": _recommendation(score, table),
        "sources": [
            {"title": label_a, "source_type": "document_a", "chars": len(clean_a)},
            {"title": label_b, "source_type": "document_b", "chars": len(clean_b)},
        ],
        "suggestions": ["Show only gaps", "Show matched points", "Give improvement recommendations"],
        "answer_time_ms": round((time.perf_counter() - started_at) * 1000),
    }

    context = (
        "ACTIVE TOOL: Compare Tool\n"
        "This is not chat mode. The two sources are separated below and must remain separated.\n\n"
        "HARD SOURCE BOUNDARY RULES:\n"
        "- Never copy facts from SOURCE A into SOURCE B.\n"
        "- Never copy facts from SOURCE B into SOURCE A.\n"
        "- Every claim must say whether the evidence came from SOURCE A, SOURCE B, or both.\n"
        "- If a fact is absent from one source, mark it Missing From A or Missing From B.\n"
        "- Do not infer that one source contains a fact just because the other source contains it.\n"
        "- Do not add facts that are absent from the extracted structures or comparison table.\n"
        "- Treat Missing From A, Missing From B, and Conflict as real comparison outcomes.\n"
        f"- Use only these row statuses; do not invent new statuses: {', '.join(sorted(ALLOWED_ROW_STATUSES))}.\n\n"
        f"{_source_boundary_package(label_a, label_b, type_a, type_b, facts_a, facts_b)}\n\n"
        "DETERMINISTIC COMPARISON RESULT:\n"
        f"```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
    )
    question = (
        "Return a structured comparison answer with these sections: Quick Verdict, "
        "Document Types, Comparison Table, Matches, Missing Items, Conflicts/Risks, "
        "Final Decision, Final Fit/Alignment, Resume Improvements when present, Recommendation. Do not summarize the sources separately. "
        "In the table and key bullets, explicitly identify Source A evidence and Source B evidence."
    )
    return {
        "result": result,
        "context": context,
        "question": question,
        "started_at": started_at,
    }


def run_compare_tool(
    document_a: str,
    document_b: str,
    compare_goal: str = "Compare the two sources",
    labels: dict | None = None,
    model_options: dict | None = None,
) -> dict:
    model_options = model_options or {}
    payload = build_compare_tool_payload(
        document_a=document_a,
        document_b=document_b,
        compare_goal=compare_goal,
        labels=labels,
    )
    result = payload["result"]
    llm_result = generate_answer(
        context=payload["context"],
        question=payload["question"],
        ollama_model=model_options.get("ollama_model") or None,
        openrouter_model=model_options.get("openrouter_model") or None,
        confidence="high",
        force_provider=model_options.get("force_provider") or "",
    )
    result["answer"] = (llm_result.get("answer") or "").strip() or json.dumps(result, ensure_ascii=False, indent=2)
    result["provider"] = llm_result.get("provider", "")
    result["model"] = llm_result.get("model", "")
    result["confidence"] = "compare tool"
    result["answer_time_ms"] = round((time.perf_counter() - payload["started_at"]) * 1000)
    return result
