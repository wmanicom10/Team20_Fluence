from __future__ import annotations

from typing import Any, Dict, Optional

from ai_pipeline import score_risk_output, train_baseline_pipeline
from ai_validation import normalize_case_rows, parse_bool, parse_iso_date
from db import get_supabase_client


APP_MODEL_KEY = "fluence_ai_model"


def _build_cases_query(client, disease: Optional[str], start_date: Optional[str], end_date: Optional[str], verified_only: Optional[bool]):
    query = client.table("cases").select(
        "case_id,case_count,date_reported,severity,verified,data_source,source_api,"
        "diseases(name),"
        "locations(city,state_province,country)"
    )

    if disease and disease != "All Diseases":
        disease_lookup = (
            client.table("diseases")
            .select("disease_id")
            .ilike("name", disease)
            .limit(1)
            .execute()
        )
        if not disease_lookup.data:
            return None
        query = query.eq("disease_id", disease_lookup.data[0]["disease_id"])

    if start_date:
        query = query.gte("date_reported", start_date)
    if end_date:
        query = query.lte("date_reported", end_date)
    if verified_only is None:
        query = query.eq("verified", True)
    else:
        query = query.eq("verified", verified_only)
    return query


def train_ai_pipeline(app, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    filters = filters or {}
    disease = filters.get("disease")
    start_date = parse_iso_date(filters.get("startDate") or filters.get("start_date"))
    end_date = parse_iso_date(filters.get("endDate") or filters.get("end_date"))
    verified_only = parse_bool(filters.get("verified_only"), True)

    client = get_supabase_client(app)
    query = _build_cases_query(client, disease, start_date, end_date, verified_only)
    if query is None:
        model = train_baseline_pipeline([], model_version=app.config.get("AI_MODEL_VERSION", "baseline-v1"))
        app.extensions[APP_MODEL_KEY] = model
        return {
            "model": model,
            "validation": {"rows": [], "meta": {"input_rows": 0, "valid_rows": 0, "dropped_rows": 0, "dropped_examples": []}},
            "risk_output": [],
        }

    result = query.order("date_reported", desc=False).execute()
    normalized = normalize_case_rows(result.data or [])
    model = train_baseline_pipeline(normalized["rows"], model_version=app.config.get("AI_MODEL_VERSION", "baseline-v1"))
    app.extensions[APP_MODEL_KEY] = model
    return {
        "model": model,
        "validation": normalized,
        "risk_output": score_risk_output(model),
    }


def get_or_train_ai_pipeline(app, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if app.config.get("AI_AUTO_TRAIN_ON_READ", True):
        return train_ai_pipeline(app, filters=filters)

    cached = app.extensions.get(APP_MODEL_KEY)
    if cached is None:
        trained = train_ai_pipeline(app, filters=filters)
        return trained

    return {
        "model": cached,
        "validation": {"rows": [], "meta": {"input_rows": 0, "valid_rows": 0, "dropped_rows": 0, "dropped_examples": []}},
        "risk_output": score_risk_output(cached),
    }
