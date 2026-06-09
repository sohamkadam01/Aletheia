from __future__ import annotations

import json
import re
from typing import Optional


SUPPORTED_CHART_TYPES = {"bar", "horizontal_bar", "radar", "pie", "donut", "line"}

_CHART_TYPE_ALIASES: dict[str, str] = {
    "bar_chart":        "bar",
    "barchart":         "bar",
    "column":           "bar",
    "column_chart":     "bar",
    "vertical_bar":     "bar",
    "grouped_bar":      "bar",
    "stacked_bar":      "bar",
    "horizontalbar":    "horizontal_bar",
    "horizontal-bar":   "horizontal_bar",
    "hbar":             "horizontal_bar",
    "h_bar":            "horizontal_bar",
    "doughnut":         "donut",
    "donut_chart":      "donut",
    "pie_chart":        "pie",
    "line_chart":       "line",
    "linechart":        "line",
    "trend":            "line",
    "area":             "line",
    "radar_chart":      "radar",
    "spider":           "radar",
    "spiderweb":        "radar",
    "spider_chart":     "radar",
    "radarchart":       "radar",
}

_LABEL_ALIASES = ("categories", "keys", "xAxis", "x_axis", "x", "names", "items", "dimensions", "axes")
_DATASET_ALIASES = ("data", "series", "values", "dataset", "results", "scores", "metrics")


def _normalize_chart_type(raw_type: str) -> str:
    normalized = str(raw_type or "").strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in SUPPORTED_CHART_TYPES:
        return normalized
    return _CHART_TYPE_ALIASES.get(normalized, normalized)


def _normalize_chart_fields(data: dict) -> None:
    """Normalize alternative/missing fields to the canonical labels/datasets schema."""

    # 1. Normalize labels from common aliases
    if not data.get("labels"):
        for alias in _LABEL_ALIASES:
            if isinstance(data.get(alias), list) and data[alias]:
                data["labels"] = data[alias]
                break

    # 2. Normalize datasets from common aliases
    if not data.get("datasets"):
        for alias in _DATASET_ALIASES:
            val = data.get(alias)
            if isinstance(val, list) and val:
                if isinstance(val[0], dict) and "data" in val[0]:
                    data["datasets"] = val
                    break
                if all(isinstance(v, (int, float)) for v in val):
                    data["datasets"] = [{"label": "Value", "data": val}]
                    break

    # 3. Model returned flat key→value dict e.g. {"Skills": 80, "Experience": 70}
    if not data.get("labels") or not data.get("datasets"):
        numeric_keys = {
            k: v for k, v in data.items()
            if isinstance(v, (int, float))
            and k not in ("type",)
            and not k.startswith("_")
        }
        if len(numeric_keys) >= 2:
            data["labels"] = list(numeric_keys.keys())
            data["datasets"] = [{"label": "Value", "data": list(numeric_keys.values())}]

    # 4. Auto-generate generic labels from dataset length if still missing
    if not data.get("labels") and data.get("datasets"):
        first_ds = data["datasets"][0] if data["datasets"] else {}
        if isinstance(first_ds, dict) and isinstance(first_ds.get("data"), list):
            n = len(first_ds["data"])
            data["labels"] = [f"Item {i + 1}" for i in range(n)]

def is_chart_request(question: str) -> bool:
    text = f" {question or ''} ".lower()
    terms = (
        "chart", "graph", "bar chart", "horizontal bar", "radar chart", "pie chart",
        "donut chart", "line chart", "plot", "visualize", "visualise",
        "score breakdown", "comparison graph", "comparison chart", "show graph",
        "show chart", "analytics dashboard",
    )
    return any(term in text for term in terms)


def extract_chart_json(answer: str) -> Optional[dict]:
    raw = str(answer or "")
    # Try fenced ```chart or ```json block first
    match = re.search(r"```(?:chart|json)\s*([\s\S]*?)```", raw, re.IGNORECASE)
    json_text = match.group(1).strip() if match else ""
    if not json_text:
        # Bare JSON object
        match = re.search(r"\{[\s\S]*\}", raw)
        json_text = match.group(0).strip() if match else ""
    if not json_text:
        return None
    # Strip any trailing prose after the closing brace
    brace_end = json_text.rfind("}")
    if brace_end != -1:
        json_text = json_text[:brace_end + 1]
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        print(f"[chart_tool] JSON parse failed on: {json_text[:200]!r}")
        return None
    return data if isinstance(data, dict) else None


def validate_chart_payload(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Chart payload must be an object."

    # Normalize alternative/missing fields before validation
    _normalize_chart_fields(data)

    # Normalize type — default to bar if missing
    raw_type = str(data.get("type") or "").strip().lower()
    if not raw_type:
        raw_type = "bar"
    chart_type = _normalize_chart_type(raw_type)
    if chart_type not in SUPPORTED_CHART_TYPES:
        return False, f"Unsupported chart type '{raw_type}'. Supported: {', '.join(sorted(SUPPORTED_CHART_TYPES))}."
    data["type"] = chart_type

    labels = data.get("labels")
    datasets = data.get("datasets")
    if not isinstance(labels, list) or not labels:
        return False, "Chart must include labels."
    if not isinstance(datasets, list) or not datasets:
        return False, "Chart must include at least one dataset."
    if len(labels) > 12:
        return False, "Chart has too many labels for the compact widget."

    cleaned_labels = [str(label).strip()[:36] for label in labels if str(label).strip()]
    if not cleaned_labels:
        return False, "Chart labels are empty."
    data["labels"] = cleaned_labels

    cleaned_datasets = []
    for dataset in datasets[:3]:
        if not isinstance(dataset, dict):
            continue
        values = dataset.get("data")
        if not isinstance(values, list):
            continue
        numeric_values = []
        for value in values[: len(cleaned_labels)]:
            try:
                numeric_values.append(float(value))
            except (TypeError, ValueError):
                numeric_values.append(0.0)
        if len(numeric_values) != len(cleaned_labels):
            return False, "Dataset values must match label count."
        cleaned_datasets.append({
            "label": str(dataset.get("label") or "Series").strip()[:36],
            "data": numeric_values,
        })
    if not cleaned_datasets:
        return False, "Chart datasets are empty."
    data["datasets"] = cleaned_datasets
    data["title"] = str(data.get("title") or "Chart").strip()[:80]
    data["summary"] = str(data.get("summary") or "").strip()[:500]
    return True, ""


def chart_answer_from_data(data: dict) -> str:
    return "```chart\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"


def fallback_chart(question: str, document_mode: str) -> dict:
    title = "Comparison Breakdown" if document_mode == "compare" else "Information Breakdown"
    return {
        "type": "bar",
        "title": title,
        "labels": ["Available evidence", "Missing details", "Needs review"],
        "datasets": [{"label": "Relative score", "data": [70, 20, 10]}],
        "summary": (
            "The chart uses a fallback structure because precise numeric chart data "
            "was not available in the extracted context."
        ),
    }


def build_chart_prompt(context: str, question: str, document_mode: str) -> str:
    return f"""
Create an information chart for the user's request.

Active mode: {document_mode}

User request:
{question}

Context:
---------------------
{context[:12000]}
---------------------

Output ONLY one fenced ```chart block containing valid JSON. No prose outside the block.

Supported chart types: bar, horizontal_bar, radar, pie, donut, line

Required schema — copy this exactly and fill in your values:
```chart
{{
  "type": "bar",
  "title": "Your chart title here",
  "labels": ["Label A", "Label B", "Label C"],
  "datasets": [
    {{
      "label": "Series name",
      "data": [80, 55, 70]
    }}
  ],
  "summary": "One sentence describing what this chart shows."
}}
```

STRICT RULES:
- Output ONLY the ```chart block. No text before or after it.
- "type" REQUIRED: must be one of bar, horizontal_bar, radar, pie, donut, line
- "labels" REQUIRED: JSON array of strings, 3-8 items
- "datasets" REQUIRED: JSON array, each item must have "label" (string) and "data" (array of numbers)
- "data" array must have exactly the same number of values as "labels"
- All values in "data" must be numbers (not strings)
- Use only facts and numbers from the context. Estimate percentages if exact numbers unavailable.
- Do NOT output markdown tables, prose, Mermaid, SVG, or any text outside the chart block.
"""
