from datetime import datetime

from flask import current_app, jsonify, request

from db import get_supabase_client


ALLOWED_CASE_UPDATE_FIELDS = {
    "case_count",
    "date_reported",
    "severity",
    "verified",
    "data_source",
    "source_api",
}


REQUIRED_CASE_FIELDS = {
    "disease_id",
    "location_id",
    "case_count",
    "date_reported",
}


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return str(value).lower() in {"1", "true", "yes", "y", "on"}


def _require_json_body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, (jsonify({"message": "Request body must be valid JSON"}), 400)
    return payload, None


def _validate_iso_date(value, field_name):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return None
    except ValueError:
        return jsonify({"message": f"{field_name} must use YYYY-MM-DD format"}), 400


def _get_disease_id_by_name(client, disease_name):
    lookup = (
        client.table("diseases")
        .select("disease_id")
        .ilike("name", disease_name)
        .limit(1)
        .execute()
    )
    if not lookup.data:
        return None
    return lookup.data[0]["disease_id"]


def register_routes(app):
    @app.get("/health")
    def health():
        try:
            client = get_supabase_client(current_app)
            result = client.table("diseases").select("disease_id").limit(1).execute()
            connected = result is not None
        except Exception as exc:
            return jsonify({
                "status": "error",
                "service": "fluence-backend",
                "database_connected": False,
                "error": str(exc),
            }), 500

        return jsonify({
            "status": "ok",
            "service": "fluence-backend",
            "database_connected": connected,
        }), 200

    @app.get("/diseases")
    def get_diseases():
        try:
            client = get_supabase_client(current_app)
            query = client.table("diseases").select("*").order("name")

            active_only = request.args.get("active_only")
            if active_only is not None:
                query = query.eq("is_active", _as_bool(active_only))

            result = query.execute()
            return jsonify({"data": result.data or []}), 200
        except Exception as exc:
            return jsonify({"message": "Failed to load diseases", "error": str(exc)}), 500

    @app.post("/diseases")
    def create_disease():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        required_fields = {"name", "category", "severity_level"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            return jsonify({"message": "Missing required fields", "missing": missing}), 400

        try:
            client = get_supabase_client(current_app)
            insert_payload = {
                "name": payload["name"],
                "category": payload["category"],
                "severity_level": payload["severity_level"],
                "description": payload.get("description"),
                "is_active": _as_bool(payload.get("is_active")) if payload.get("is_active") is not None else True,
            }
            result = client.table("diseases").insert(insert_payload).execute()
            return jsonify({"message": "Disease created", "data": result.data or []}), 201
        except Exception as exc:
            return jsonify({"message": "Failed to create disease", "error": str(exc)}), 500

    @app.get("/locations")
    def get_locations():
        try:
            client = get_supabase_client(current_app)
            query = client.table("locations").select("*").order("city")

            for field in ("country", "state_province", "city", "region_type"):
                value = request.args.get(field)
                if value:
                    query = query.eq(field, value)

            result = query.execute()
            return jsonify({"data": result.data or []}), 200
        except Exception as exc:
            return jsonify({"message": "Failed to load locations", "error": str(exc)}), 500

    @app.post("/locations")
    def create_location():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        required_fields = {"country", "city"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            return jsonify({"message": "Missing required fields", "missing": missing}), 400

        try:
            client = get_supabase_client(current_app)
            insert_payload = {
                "country": payload["country"],
                "state_province": payload.get("state_province"),
                "city": payload["city"],
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
                "population": payload.get("population"),
                "region_type": payload.get("region_type"),
            }
            result = client.table("locations").insert(insert_payload).execute()
            return jsonify({"message": "Location created", "data": result.data or []}), 201
        except Exception as exc:
            return jsonify({"message": "Failed to create location", "error": str(exc)}), 500

    @app.get("/cases")
    def get_cases():
        try:
            client = get_supabase_client(current_app)
            query = client.table("cases").select(
                "case_id,case_count,date_reported,severity,verified,data_source,source_api,"
                "diseases(disease_id,name,category,severity_level),"
                "locations(location_id,city,state_province,country,latitude,longitude)"
            )

            disease_id = request.args.get("disease_id")
            disease_name = request.args.get("disease_name")
            date_from = request.args.get("date_from")
            date_to = request.args.get("date_to")
            verified_only = request.args.get("verified_only")

            if disease_id:
                query = query.eq("disease_id", disease_id)
            elif disease_name:
                found_disease_id = _get_disease_id_by_name(client, disease_name)
                if not found_disease_id:
                    return jsonify({"data": [], "message": f'Disease "{disease_name}" not found'}), 200
                query = query.eq("disease_id", found_disease_id)

            if date_from:
                date_error = _validate_iso_date(date_from, "date_from")
                if date_error:
                    return date_error
                query = query.gte("date_reported", date_from)

            if date_to:
                date_error = _validate_iso_date(date_to, "date_to")
                if date_error:
                    return date_error
                query = query.lte("date_reported", date_to)

            if verified_only is not None and _as_bool(verified_only):
                query = query.eq("verified", True)

            result = query.order("date_reported", desc=True).execute()
            return jsonify({"data": result.data or []}), 200
        except Exception as exc:
            return jsonify({"message": "Failed to load cases", "error": str(exc)}), 500

    @app.post("/cases")
    def create_case():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        missing = sorted(REQUIRED_CASE_FIELDS - set(payload.keys()))
        if missing:
            return jsonify({"message": "Missing required fields", "missing": missing}), 400

        date_error = _validate_iso_date(str(payload["date_reported"]), "date_reported")
        if date_error:
            return date_error

        try:
            client = get_supabase_client(current_app)
            insert_payload = {
                "disease_id": payload["disease_id"],
                "location_id": payload["location_id"],
                "case_count": payload["case_count"],
                "date_reported": payload["date_reported"],
                "data_source": payload.get("data_source", "manual_submission"),
                "source_api": payload.get("source_api"),
                "severity": payload.get("severity"),
                "verified": _as_bool(payload.get("verified")) if payload.get("verified") is not None else False,
            }
            result = client.table("cases").insert(insert_payload).execute()
            return jsonify({"message": "Case created", "data": result.data or []}), 201
        except Exception as exc:
            return jsonify({"message": "Failed to create case", "error": str(exc)}), 500

    @app.patch("/cases/<int:case_id>")
    def update_case(case_id):
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        update_fields = {k: v for k, v in payload.items() if k in ALLOWED_CASE_UPDATE_FIELDS}
        if not update_fields:
            return jsonify({
                "message": "No valid fields provided",
                "allowed_fields": sorted(ALLOWED_CASE_UPDATE_FIELDS),
            }), 400

        if "date_reported" in update_fields:
            date_error = _validate_iso_date(str(update_fields["date_reported"]), "date_reported")
            if date_error:
                return date_error

        if "verified" in update_fields:
            update_fields["verified"] = _as_bool(update_fields["verified"])

        try:
            client = get_supabase_client(current_app)
            result = (
                client.table("cases")
                .update(update_fields)
                .eq("case_id", case_id)
                .execute()
            )
            return jsonify({"message": "Case updated", "data": result.data or []}), 200
        except Exception as exc:
            return jsonify({"message": "Failed to update case", "error": str(exc)}), 500

    @app.get("/stats/cases-by-disease")
    def cases_by_disease_stats():
        try:
            client = get_supabase_client(current_app)
            query = client.table("cases").select("case_count,diseases(name)")

            verified_only = request.args.get("verified_only")
            if verified_only is None or _as_bool(verified_only):
                query = query.eq("verified", True)

            result = query.execute()

            totals = {}
            for row in (result.data or []):
                disease_name = (row.get("diseases") or {}).get("name")
                if not disease_name:
                    continue
                totals[disease_name] = totals.get(disease_name, 0) + int(row.get("case_count") or 0)

            data = [
                {"disease_name": disease_name, "total_cases": total_cases}
                for disease_name, total_cases in sorted(totals.items(), key=lambda item: item[1], reverse=True)
            ]
            return jsonify({"data": data}), 200
        except Exception as exc:
            return jsonify({"message": "Failed to compute stats", "error": str(exc)}), 500
