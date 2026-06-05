from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Dict, Optional

from ai_validation import normalize_case_rows, parse_bool, parse_iso_date
from db import get_supabase_client


DATASET_SCHEMA_VERSION = "v1"


def _build_cases_query(client, disease: Optional[str], start_date: Optional[str], end_date: Optional[str], verified_only: Optional[bool]):
    query = client.table("cases").select(
        "case_id,case_count,date_reported,severity,verified,data_source,source_api,disease_id,location_id,"
        "diseases(disease_id,name,category),"
        "locations(location_id,city,state_province,country,latitude,longitude,region_type)"
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


def export_training_dataset(app, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    filters = filters or {}
    disease = filters.get("disease")
    start_date = parse_iso_date(filters.get("startDate") or filters.get("start_date"))
    end_date = parse_iso_date(filters.get("endDate") or filters.get("end_date"))
    verified_only = parse_bool(filters.get("verified_only"), True)

    client = get_supabase_client(app)
    query = _build_cases_query(client, disease, start_date, end_date, verified_only)
    rows = []
    if query is not None:
        result = query.order("date_reported", desc=False).execute()
        rows = result.data or []

    normalized = normalize_case_rows(rows)
    return {
        "schema_version": DATASET_SCHEMA_VERSION,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "filters": {
            "disease": disease,
            "start_date": start_date,
            "end_date": end_date,
            "verified_only": verified_only,
        },
        "meta": normalized["meta"],
        "rows": normalized["rows"],
    }


def dataset_to_csv(dataset: Dict[str, Any]) -> str:
    rows = dataset.get("rows") or []
    fieldnames = dataset.get("meta", {}).get("normalized_schema") or []
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
