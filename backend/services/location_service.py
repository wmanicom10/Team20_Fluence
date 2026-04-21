from __future__ import annotations

from services.base_service import BaseService


class LocationService(BaseService):
    """Concrete service that encapsulates location validation and queries.

    This subclass inherits from BaseService and groups all location-specific
    logic behind one interface for the locations table.
    """

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
        """Override BaseService.get_all with location filter behavior."""
        return self._build_list_query(filters or {}).execute().data or []

    def get_by_id(self, item_id):
        """Override BaseService.get_by_id for the locations table."""
        result = self._table().select("*").eq("location_id", item_id).limit(1).execute()
        return result.data[0] if result.data else None

    def create(self, payload):
        """Override BaseService.create with location-specific validation."""
        normalized = self._validate_create_payload(payload)
        return self._table().insert(normalized).execute().data or []

    def update(self, item_id, payload):
        """Override BaseService.update for location records."""
        return self._table().update(payload).eq("location_id", item_id).execute().data or []

    def delete(self, item_id):
        """Override BaseService.delete for location records."""
        self._table().delete().eq("location_id", item_id).execute()
