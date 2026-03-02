from datetime import datetime

from flask import current_app, jsonify, request

from db import get_supabase_client


API_PREFIX = "/api"

ALLOWED_CASE_UPDATE_FIELDS = {
    "disease_id",
    "location_id",
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


def _success(data, status_code=200):
    return jsonify({"status": "success", "data": data}), status_code


def _failure(message, status_code=400, details=None):
    error = {"message": message}
    if details is not None:
        error["details"] = details
    return jsonify({"status": "error", "error": error}), status_code


def _require_json_body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, _failure("Request body must be valid JSON", 400)
    return payload, None


def _validate_iso_date(value, field_name):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return None
    except ValueError:
        return _failure(f"{field_name} must use YYYY-MM-DD format", 400)


def _parse_bool(value, field_name):
    if isinstance(value, bool):
        return value, None

    lowered = str(value).lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True, None
    if lowered in {"0", "false", "no", "n", "off"}:
        return False, None

    return None, _failure(f"{field_name} must be a boolean value", 400)


def _parse_int(value, field_name):
    try:
        return int(value), None
    except (TypeError, ValueError):
        return None, _failure(f"{field_name} must be an integer", 400)


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
    @app.get(f"{API_PREFIX}/health")
    def health():
        try:
            client = get_supabase_client(current_app)
            client.table("diseases").select("disease_id").limit(1).execute()
            return _success({
                "service": "fluence-backend",
                "database_connected": True,
            }, 200)
        except Exception as exc:
            return _failure("Database health check failed", 500, str(exc))

    @app.get(f"{API_PREFIX}/diseases")
    def get_diseases():
        try:
            client = get_supabase_client(current_app)
            query = client.table("diseases").select("*").order("name")

            active_only = request.args.get("active_only")
            if active_only is not None:
                parsed_active, bool_error = _parse_bool(active_only, "active_only")
                if bool_error:
                    return bool_error
                query = query.eq("is_active", parsed_active)

            result = query.execute()
            return _success(result.data or [], 200)
        except Exception as exc:
            return _failure("Failed to load diseases", 500, str(exc))

    @app.post(f"{API_PREFIX}/diseases")
    def create_disease():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        required_fields = {"name", "category", "severity_level"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            return _failure("Missing required fields", 400, {"missing": missing})

        for field in required_fields:
            if not isinstance(payload[field], str) or not payload[field].strip():
                return _failure(f"{field} must be a non-empty string", 400)

        try:
            client = get_supabase_client(current_app)
            insert_payload = {
                "name": payload["name"].strip(),
                "category": payload["category"].strip(),
                "severity_level": payload["severity_level"].strip(),
                "description": payload.get("description"),
                "is_active": True,
            }

            if "is_active" in payload:
                parsed_active, bool_error = _parse_bool(payload.get("is_active"), "is_active")
                if bool_error:
                    return bool_error
                insert_payload["is_active"] = parsed_active

            result = client.table("diseases").insert(insert_payload).execute()
            return _success(result.data or [], 201)
        except Exception as exc:
            return _failure("Failed to create disease", 500, str(exc))

    @app.get(f"{API_PREFIX}/locations")
    def get_locations():
        try:
            client = get_supabase_client(current_app)
            query = client.table("locations").select("*").order("city")

            for field in ("country", "state_province", "city", "region_type"):
                value = request.args.get(field)
                if value:
                    query = query.eq(field, value)

            result = query.execute()
            return _success(result.data or [], 200)
        except Exception as exc:
            return _failure("Failed to load locations", 500, str(exc))

    @app.post(f"{API_PREFIX}/locations")
    def create_location():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        required_fields = {"country", "city"}
        missing = sorted(required_fields - set(payload.keys()))
        if missing:
            return _failure("Missing required fields", 400, {"missing": missing})

        for field in required_fields:
            if not isinstance(payload[field], str) or not payload[field].strip():
                return _failure(f"{field} must be a non-empty string", 400)

        try:
            client = get_supabase_client(current_app)
            insert_payload = {
                "country": payload["country"].strip(),
                "state_province": payload.get("state_province"),
                "city": payload["city"].strip(),
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
                "population": payload.get("population"),
                "region_type": payload.get("region_type"),
            }
            result = client.table("locations").insert(insert_payload).execute()
            return _success(result.data or [], 201)
        except Exception as exc:
            return _failure("Failed to create location", 500, str(exc))

    @app.get(f"{API_PREFIX}/cases")
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
                parsed_disease_id, parse_error = _parse_int(disease_id, "disease_id")
                if parse_error:
                    return parse_error
                query = query.eq("disease_id", parsed_disease_id)
            elif disease_name:
                found_disease_id = _get_disease_id_by_name(client, disease_name)
                if not found_disease_id:
                    return _success([], 200)
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

            if verified_only is not None:
                parsed_verified, bool_error = _parse_bool(verified_only, "verified_only")
                if bool_error:
                    return bool_error
                query = query.eq("verified", parsed_verified)

            result = query.order("date_reported", desc=True).execute()
            return _success(result.data or [], 200)
        except Exception as exc:
            return _failure("Failed to load cases", 500, str(exc))

    @app.get(f"{API_PREFIX}/cases/<int:case_id>")
    def get_case_by_id(case_id):
        try:
            client = get_supabase_client(current_app)
            result = (
                client.table("cases")
                .select(
                    "case_id,case_count,date_reported,severity,verified,data_source,source_api,"
                    "diseases(disease_id,name,category,severity_level),"
                    "locations(location_id,city,state_province,country,latitude,longitude)"
                )
                .eq("case_id", case_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                return _failure("Case not found", 404)
            return _success(result.data[0], 200)
        except Exception as exc:
            return _failure("Failed to load case", 500, str(exc))

    @app.post(f"{API_PREFIX}/cases")
    def create_case():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        missing = sorted(REQUIRED_CASE_FIELDS - set(payload.keys()))
        if missing:
            return _failure("Missing required fields", 400, {"missing": missing})

        parsed_disease_id, parse_error = _parse_int(payload["disease_id"], "disease_id")
        if parse_error:
            return parse_error

        parsed_location_id, parse_error = _parse_int(payload["location_id"], "location_id")
        if parse_error:
            return parse_error

        parsed_case_count, parse_error = _parse_int(payload["case_count"], "case_count")
        if parse_error:
            return parse_error
        if parsed_case_count < 0:
            return _failure("case_count must be >= 0", 400)

        date_error = _validate_iso_date(str(payload["date_reported"]), "date_reported")
        if date_error:
            return date_error

        parsed_verified = False
        if "verified" in payload:
            parsed_verified, bool_error = _parse_bool(payload.get("verified"), "verified")
            if bool_error:
                return bool_error

        try:
            client = get_supabase_client(current_app)
            insert_payload = {
                "disease_id": parsed_disease_id,
                "location_id": parsed_location_id,
                "case_count": parsed_case_count,
                "date_reported": payload["date_reported"],
                "data_source": payload.get("data_source", "manual_submission"),
                "source_api": payload.get("source_api"),
                "severity": payload.get("severity"),
                "verified": parsed_verified,
            }
            result = client.table("cases").insert(insert_payload).execute()
            return _success(result.data or [], 201)
        except Exception as exc:
            return _failure("Failed to create case", 500, str(exc))

    @app.patch(f"{API_PREFIX}/cases/<int:case_id>")
    def update_case(case_id):
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        update_fields = {k: v for k, v in payload.items() if k in ALLOWED_CASE_UPDATE_FIELDS}
        if not update_fields:
            return _failure(
                "No valid fields provided",
                400,
                {"allowed_fields": sorted(ALLOWED_CASE_UPDATE_FIELDS)},
            )

        if "disease_id" in update_fields:
            parsed_disease_id, parse_error = _parse_int(update_fields["disease_id"], "disease_id")
            if parse_error:
                return parse_error
            update_fields["disease_id"] = parsed_disease_id

        if "location_id" in update_fields:
            parsed_location_id, parse_error = _parse_int(update_fields["location_id"], "location_id")
            if parse_error:
                return parse_error
            update_fields["location_id"] = parsed_location_id

        if "case_count" in update_fields:
            parsed_case_count, parse_error = _parse_int(update_fields["case_count"], "case_count")
            if parse_error:
                return parse_error
            if parsed_case_count < 0:
                return _failure("case_count must be >= 0", 400)
            update_fields["case_count"] = parsed_case_count

        if "date_reported" in update_fields:
            date_error = _validate_iso_date(str(update_fields["date_reported"]), "date_reported")
            if date_error:
                return date_error

        if "verified" in update_fields:
            parsed_verified, bool_error = _parse_bool(update_fields["verified"], "verified")
            if bool_error:
                return bool_error
            update_fields["verified"] = parsed_verified

        try:
            client = get_supabase_client(current_app)
            exists = client.table("cases").select("case_id").eq("case_id", case_id).limit(1).execute()
            if not exists.data:
                return _failure("Case not found", 404)

            result = (
                client.table("cases")
                .update(update_fields)
                .eq("case_id", case_id)
                .execute()
            )
            return _success(result.data or [], 200)
        except Exception as exc:
            return _failure("Failed to update case", 500, str(exc))

    @app.delete(f"{API_PREFIX}/cases/<int:case_id>")
    def delete_case(case_id):
        try:
            client = get_supabase_client(current_app)
            exists = client.table("cases").select("case_id").eq("case_id", case_id).limit(1).execute()
            if not exists.data:
                return _failure("Case not found", 404)

            client.table("cases").delete().eq("case_id", case_id).execute()
            return _success({"deleted": True, "case_id": case_id}, 200)
        except Exception as exc:
            return _failure("Failed to delete case", 500, str(exc))

    @app.get(f"{API_PREFIX}/metrics/cases-by-disease")
    def cases_by_disease_stats():
        try:
            client = get_supabase_client(current_app)
            query = client.table("cases").select("case_count,diseases(name)")

            verified_only = request.args.get("verified_only")
            if verified_only is not None:
                parsed_verified, bool_error = _parse_bool(verified_only, "verified_only")
                if bool_error:
                    return bool_error
                query = query.eq("verified", parsed_verified)
            else:
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
            return _success(data, 200)
        except Exception as exc:
            return _failure("Failed to compute case metrics", 500, str(exc))
