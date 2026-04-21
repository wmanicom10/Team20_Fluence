from __future__ import annotations

from services.base_service import BaseService


class LocationService(BaseService):
    def _table(self):
        return self.client.table("locations")

    def _build_list_query(self, filters):
        query = self._table().select("*").order("city")
        for field in ("country", "state_province", "city", "region_type"):
            value = filters.get(field)
            if value:
                query = query.eq(field, value)
        return query

    def _validate_create_payload(self, payload):
        required_fields = {"country", "city"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        for field in required_fields:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")

        return {
            "country": payload["country"].strip(),
            "state_province": payload.get("state_province"),
            "city": payload["city"].strip(),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "population": payload.get("population"),
            "region_type": payload.get("region_type"),
        }

    def get_all(self, filters=None):
        return self._build_list_query(filters or {}).execute().data or []

    def get_by_id(self, item_id):
        result = self._table().select("*").eq("location_id", item_id).limit(1).execute()
        return result.data[0] if result.data else None

    def create(self, payload):
        normalized = self._validate_create_payload(payload)
        return self._table().insert(normalized).execute().data or []

    def update(self, item_id, payload):
        return self._table().update(payload).eq("location_id", item_id).execute().data or []

    def delete(self, item_id):
        self._table().delete().eq("location_id", item_id).execute()
