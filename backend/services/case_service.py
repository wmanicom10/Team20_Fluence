from __future__ import annotations

from datetime import datetime

from services.base_service import BaseService


class CaseService(BaseService):
    _case_select = (
        "case_id,case_count,date_reported,severity,verified,data_source,source_api,"
        "diseases(disease_id,name,category,severity_level),"
        "locations(location_id,city,state_province,country,latitude,longitude)"
    )

    def _table(self):
        return self.client.table("cases")

    def _parse_int(self, value, field_name):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be an integer")

    def _validate_iso_date(self, value, field_name):
        try:
            datetime.strptime(str(value), "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"{field_name} must use YYYY-MM-DD format") from exc

    def _parse_bool(self, value, field_name):
        if isinstance(value, bool):
            return value
        lowered = str(value).lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
        raise ValueError(f"{field_name} must be a boolean value")

    def _validate_create_payload(self, payload):
        required_fields = {"disease_id", "location_id", "case_count", "date_reported"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        disease_id = self._parse_int(payload["disease_id"], "disease_id")
        location_id = self._parse_int(payload["location_id"], "location_id")
        case_count = self._parse_int(payload["case_count"], "case_count")
        if case_count < 0:
            raise ValueError("case_count must be >= 0")

        self._validate_iso_date(payload["date_reported"], "date_reported")

        verified = False
        if "verified" in payload:
            verified = self._parse_bool(payload["verified"], "verified")

        return {
            "disease_id": disease_id,
            "location_id": location_id,
            "case_count": case_count,
            "date_reported": payload["date_reported"],
            "data_source": payload.get("data_source", "manual_submission"),
            "source_api": payload.get("source_api"),
            "severity": payload.get("severity"),
            "verified": verified,
        }

    def _normalize_update_payload(self, payload):
        update_fields = dict(payload)
        if "disease_id" in update_fields:
            update_fields["disease_id"] = self._parse_int(update_fields["disease_id"], "disease_id")
        if "location_id" in update_fields:
            update_fields["location_id"] = self._parse_int(update_fields["location_id"], "location_id")
        if "case_count" in update_fields:
            update_fields["case_count"] = self._parse_int(update_fields["case_count"], "case_count")
            if update_fields["case_count"] < 0:
                raise ValueError("case_count must be >= 0")
        if "date_reported" in update_fields:
            self._validate_iso_date(update_fields["date_reported"], "date_reported")
        if "verified" in update_fields:
            update_fields["verified"] = self._parse_bool(update_fields["verified"], "verified")
        return update_fields

    def _build_list_query(self, filters, disease_service):
        query = self._table().select(self._case_select)
        if filters.get("disease_id") is not None:
            query = query.eq("disease_id", filters["disease_id"])
        elif filters.get("disease_name"):
            disease_id = disease_service.find_id_by_name(filters["disease_name"])
            if not disease_id:
                return None
            query = query.eq("disease_id", disease_id)
        if filters.get("date_from"):
            query = query.gte("date_reported", filters["date_from"])
        if filters.get("date_to"):
            query = query.lte("date_reported", filters["date_to"])
        if filters.get("verified_only") is not None:
            query = query.eq("verified", filters["verified_only"])
        return query

    def get_all(self, filters=None, disease_service=None):
        filters = filters or {}
        query = self._build_list_query(filters, disease_service)
        if query is None:
            return []
        return query.order("date_reported", desc=True).execute().data or []

    def get_by_id(self, item_id):
        result = self._table().select(self._case_select).eq("case_id", item_id).limit(1).execute()
        return result.data[0] if result.data else None

    def create(self, payload):
        normalized = self._validate_create_payload(payload)
        return self._table().insert(normalized).execute().data or []

    def update(self, item_id, payload):
        normalized = self._normalize_update_payload(payload)
        return self._table().update(normalized).eq("case_id", item_id).execute().data or []

    def delete(self, item_id):
        self._table().delete().eq("case_id", item_id).execute()

    def exists(self, item_id):
        result = self._table().select("case_id").eq("case_id", item_id).limit(1).execute()
        return bool(result.data)

    def get_dashboard_rows(self, disease_id=None, start_date=None, end_date=None, verified_only=True):
        query = self._table().select(
            "case_count,date_reported,severity,diseases(name),locations(city,state_province)"
        )
        if disease_id is not None:
            query = query.eq("disease_id", disease_id)
        if start_date:
            query = query.gte("date_reported", start_date)
        if end_date:
            query = query.lte("date_reported", end_date)
        query = query.eq("verified", verified_only)
        return query.execute().data or []

    def get_metric_rows(self, verified_only=True):
        result = self._table().select("case_count,diseases(name)").eq("verified", verified_only).execute()
        return result.data or []
