from __future__ import annotations

from services.base_service import BaseService


class DiseaseService(BaseService):
    """Concrete service that encapsulates disease validation and queries.

    This subclass inherits from BaseService and keeps disease-specific rules
    together, demonstrating encapsulation of behavior for the diseases table.
    """

    def _table(self):
        return self.client.table("diseases")

    def _build_list_query(self, active_only=None):
        query = self._table().select("*").order("name")
        if active_only is not None:
            query = query.eq("is_active", active_only)
        return query

    def _validate_create_payload(self, payload):
        required_fields = {"name", "category", "severity_level"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        for field in required_fields:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")

        return {
            "name": payload["name"].strip(),
            "category": payload["category"].strip(),
            "severity_level": payload["severity_level"].strip(),
            "description": payload.get("description"),
            "is_active": bool(payload.get("is_active", True)),
        }

    def get_all(self, active_only=None):
        """Override BaseService.get_all with disease-specific filtering."""
        return self._build_list_query(active_only=active_only).execute().data or []

    def get_by_id(self, item_id):
        """Override BaseService.get_by_id for the diseases table."""
        result = self._table().select("*").eq("disease_id", item_id).limit(1).execute()
        return result.data[0] if result.data else None

    def create(self, payload):
        """Override BaseService.create with category and severity validation."""
        normalized = self._validate_create_payload(payload)
        return self._table().insert(normalized).execute().data or []

    def update(self, item_id, payload):
        """Override BaseService.update for disease records."""
        return self._table().update(payload).eq("disease_id", item_id).execute().data or []

    def delete(self, item_id):
        """Override BaseService.delete for disease records."""
        self._table().delete().eq("disease_id", item_id).execute()

    def find_id_by_name(self, disease_name):
        lookup = self._table().select("disease_id").ilike("name", disease_name).limit(1).execute()
        if not lookup.data:
            return None
        return lookup.data[0]["disease_id"]

    def get_active_names(self):
        result = self._table().select("name").eq("is_active", True).order("name").execute()
        return [row["name"] for row in (result.data or []) if row.get("name")]
