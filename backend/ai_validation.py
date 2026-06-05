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


def _extract_nested_field(row: Dict[str, Any], nested_field: str, key: str, fallback_field: Optional[str] = None) -> Any:
    nested = row.get(nested_field)
    if isinstance(nested, list) and nested:
        nested = nested[0]
    if isinstance(nested, dict) and key in nested:
        return nested.get(key)
    if fallback_field:
        return row.get(fallback_field)
    return row.get(key)


def _extract_location_parts(row: Dict[str, Any]) -> Dict[str, Any]:
    city = _extract_nested_field(row, "locations", "city") or row.get("city") or "Unknown"
    state = _extract_nested_field(row, "locations", "state_province", "state_province")
    country = _extract_nested_field(row, "locations", "country", "country")
    latitude = _extract_nested_field(row, "locations", "latitude", "latitude")
    longitude = _extract_nested_field(row, "locations", "longitude", "longitude")
    region_type = _extract_nested_field(row, "locations", "region_type", "region_type")
    location_id = _extract_nested_field(row, "locations", "location_id", "location_id")

    parts = [city]
    if state:
        parts.append(state)
    if country:
        parts.append(country)

    return {
        "location_id": location_id,
        "city": city,
        "state_province": state,
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "region_type": region_type,
        "location": ", ".join(parts),
    }


def _parse_optional_float(value: Any, field_name: str) -> Tuple[Optional[float], Optional[str]]:
    if value in (None, ""):
        return None, None
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, f"Invalid {field_name}"


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

    disease_name = _extract_nested_name(row, "diseases", "disease_name") or row.get("disease")
    if not disease_name:
        return None, "Missing disease name"

    location_parts = _extract_location_parts(row)
    if not location_parts["location"] or location_parts["location"] == "Unknown":
        return None, "Missing location data"

    latitude, lat_error = _parse_optional_float(location_parts["latitude"], "latitude")
    if lat_error:
        return None, lat_error
    longitude, lon_error = _parse_optional_float(location_parts["longitude"], "longitude")
    if lon_error:
        return None, lon_error

    verified = parse_bool(row.get("verified"), None)
    if row.get("verified") is not None and verified is None:
        return None, "Invalid verified flag"

    severity_raw = str(row.get("severity") or "").strip().lower()
    severity_score = SEVERITY_SCORES.get(severity_raw, 1)
    date_obj = datetime.strptime(date_reported, "%Y-%m-%d")

    normalized = {
        "case_id": row.get("case_id"),
        "disease_id": _extract_nested_field(row, "diseases", "disease_id", "disease_id"),
        "disease": disease_name,
        "disease_category": _extract_nested_field(row, "diseases", "category", "category"),
        "location_id": location_parts["location_id"],
        "location": location_parts["location"],
        "city": location_parts["city"],
        "state_province": location_parts["state_province"],
        "country": location_parts["country"],
        "region_type": location_parts["region_type"],
        "latitude": latitude,
        "longitude": longitude,
        "case_count": case_count,
        "date_reported": date_reported,
        "report_year": date_obj.year,
        "report_month": date_obj.month,
        "report_day": date_obj.day,
        "severity": severity_raw or None,
        "severity_score": severity_score,
        "verified": verified if verified is not None else False,
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
            dropped.append({
                "index": index,
                "case_id": row.get("case_id"),
                "reason": error,
            })
            continue
        normalized.append(item)

    return {
        "rows": normalized,
        "meta": {
            "input_rows": len(source_rows),
            "valid_rows": len(normalized),
            "dropped_rows": len(dropped),
            "dropped_examples": dropped[:10],
            "normalized_schema": [
                "case_id", "disease_id", "disease", "disease_category", "location_id", "location",
                "city", "state_province", "country", "region_type", "latitude", "longitude",
                "case_count", "date_reported", "report_year", "report_month", "report_day",
                "severity", "severity_score", "verified", "data_source", "source_api",
            ],
        },
    }
