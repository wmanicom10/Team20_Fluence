from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


SEVERITY_SCORES = {
    "low": 1,
    "mild": 1,
    "medium": 2,
    "moderate": 2,
    "high": 3,
    "severe": 3,
    "critical": 4,
}


def parse_bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def parse_iso_date(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    datetime.strptime(text, "%Y-%m-%d")
    return text


def _extract_nested_name(row: Dict[str, Any], nested_field: str, fallback_field: str) -> Optional[str]:
    nested = row.get(nested_field)
    if isinstance(nested, list) and nested:
        first = nested[0]
        if isinstance(first, dict):
            return first.get("name")
    if isinstance(nested, dict):
        return nested.get("name")
    return row.get(fallback_field)


def _extract_nested_location(row: Dict[str, Any]) -> str:
    nested = row.get("locations")
    if isinstance(nested, list) and nested:
        nested = nested[0]
    if not isinstance(nested, dict):
        nested = {}

    city = nested.get("city") or row.get("city") or "Unknown"
    state = nested.get("state_province") or row.get("state_province")
    country = nested.get("country") or row.get("country")

    if state and country:
        return f"{city}, {state}, {country}"
    if state:
        return f"{city}, {state}"
    if country:
        return f"{city}, {country}"
    return city


def normalize_case_row(row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        date_reported = parse_iso_date(row.get("date_reported"))
    except ValueError:
        return None, "Invalid date_reported"

    if not date_reported:
        return None, "Missing date_reported"

    try:
        case_count = int(row.get("case_count") or 0)
    except (TypeError, ValueError):
        return None, "Invalid case_count"

    if case_count < 0:
        return None, "case_count must be >= 0"

    severity_raw = str(row.get("severity") or "").strip().lower()
    severity_score = SEVERITY_SCORES.get(severity_raw, 1)

    normalized = {
        "case_id": row.get("case_id"),
        "disease": _extract_nested_name(row, "diseases", "disease_name") or "Unknown",
        "location": _extract_nested_location(row),
        "case_count": case_count,
        "date_reported": date_reported,
        "severity": severity_raw or None,
        "severity_score": severity_score,
        "verified": bool(row.get("verified", False)),
        "data_source": row.get("data_source"),
        "source_api": row.get("source_api"),
    }
    return normalized, None


def normalize_case_rows(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    source_rows = list(rows)
    normalized: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []

    for index, row in enumerate(source_rows):
        item, error = normalize_case_row(row)
        if error:
            dropped.append({"index": index, "reason": error})
            continue
        normalized.append(item)

    return {
        "rows": normalized,
        "meta": {
            "input_rows": len(source_rows),
            "valid_rows": len(normalized),
            "dropped_rows": len(dropped),
            "dropped_examples": dropped[:10],
        },
    }
