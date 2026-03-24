from collections import defaultdict
from datetime import datetime
import re

from flask import current_app, jsonify, request

from db import get_supabase_client


API_PREFIX = "/api"
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8

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

SEVERITY_SCORES = {
    "low": 1,
    "mild": 1,
    "medium": 2,
    "moderate": 2,
    "high": 3,
    "severe": 3,
    "critical": 4,
}

SEVERITY_LABELS = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Critical",
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


def _require_fields(payload, required_fields):
    missing = sorted(field for field in required_fields if field not in payload)
    if missing:
        return _failure("Missing required fields", 400, {"missing": missing})
    return None


def _require_non_empty_string(value, field_name):
    if not isinstance(value, str) or not value.strip():
        return None, _failure(f"{field_name} must be a non-empty string", 400)
    return value.strip(), None


def _validate_email(email):
    normalized_email, error_response = _require_non_empty_string(email, "email")
    if error_response:
        return None, error_response
    if not EMAIL_REGEX.match(normalized_email):
        return None, _failure("email must be a valid email address", 400)
    return normalized_email.lower(), None


def _validate_password(password):
    normalized_password, error_response = _require_non_empty_string(password, "password")
    if error_response:
        return None, error_response
    if len(normalized_password) < MIN_PASSWORD_LENGTH:
        return None, _failure(
            f"password must be at least {MIN_PASSWORD_LENGTH} characters long",
            400,
        )
    return normalized_password, None


def _serialize_auth_result(result):
    user = getattr(result, "user", None)
    session = getattr(result, "session", None)

    user_data = None
    if user is not None:
        user_metadata = getattr(user, "user_metadata", None) or {}
        user_data = {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "email_confirmed_at": getattr(user, "email_confirmed_at", None),
            "last_sign_in_at": getattr(user, "last_sign_in_at", None),
            "name": user_metadata.get("name"),
        }

    session_data = None
    if session is not None:
        session_data = {
            "access_token": getattr(session, "access_token", None),
            "refresh_token": getattr(session, "refresh_token", None),
            "token_type": getattr(session, "token_type", None),
            "expires_in": getattr(session, "expires_in", None),
            "expires_at": getattr(session, "expires_at", None),
        }

    return {
        "user": user_data,
        "session": session_data,
    }


def _upsert_user_profile(client, auth_user, full_name, update_last_login=False):
    if auth_user is None:
        return

    upsert_payload = {
        "user_id": getattr(auth_user, "id", None),
        "email": getattr(auth_user, "email", None),
        "role": "public",
    }

    if update_last_login:
        last_sign_in_at = getattr(auth_user, "last_sign_in_at", None)
        if last_sign_in_at:
            upsert_payload["last_login"] = last_sign_in_at

    user_metadata = getattr(auth_user, "user_metadata", None) or {}
    name_value = full_name or user_metadata.get("name")
    if name_value:
        upsert_payload["full_name"] = name_value

    client.table("users").upsert(upsert_payload, on_conflict="user_id").execute()


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


def _normalize_severity(raw_severity, case_count):
    if raw_severity:
        key = str(raw_severity).strip().lower()
        if key in SEVERITY_SCORES:
            return SEVERITY_LABELS[SEVERITY_SCORES[key]]

    if case_count >= 500:
        return "Critical"
    if case_count >= 200:
        return "High"
    if case_count >= 75:
        return "Medium"
    return "Low"


def _extract_nested_name(row, nested_field, fallback_field):
    nested = row.get(nested_field)
    if isinstance(nested, list) and nested:
        return nested[0].get("name")
    if isinstance(nested, dict):
        return nested.get("name")
    return row.get(fallback_field)


def _extract_nested_location(row):
    nested = row.get("locations")
    if isinstance(nested, list) and nested:
        nested = nested[0]
    if not isinstance(nested, dict):
        nested = {}

    city = nested.get("city") or row.get("city") or "Unknown"
    state = nested.get("state_province") or row.get("state_province")

    return f"{city}, {state}" if state else city


def _format_for_frontend(rows):
    buckets = defaultdict(lambda: defaultdict(lambda: {
        "caseCount": 0,
        "severity_score": 1,
        "severity_raw": None,
    }))

    for row in rows:
        disease_name = _extract_nested_name(row, "diseases", "disease_name") or "Unknown"
        location_label = _extract_nested_location(row)
        date_reported = row.get("date_reported")
        if not date_reported:
            continue

        try:
            date_obj = datetime.strptime(date_reported, "%Y-%m-%d").date()
        except ValueError:
            continue

        case_count = int(row.get("case_count") or 0)
        raw_severity = row.get("severity")
        severity_score = SEVERITY_SCORES.get(str(raw_severity).lower(), 1) if raw_severity else 1

        group = buckets[(disease_name, location_label)][date_obj]
        group["caseCount"] += case_count
        group["severity_score"] = max(group["severity_score"], severity_score)
        if raw_severity:
            group["severity_raw"] = raw_severity

    formatted = []
    next_id = 1

    for (disease_name, location_label), date_map in buckets.items():
        dates = sorted(date_map.keys(), reverse=True)
        if not dates:
            continue

        latest_date = dates[0]
        latest = date_map[latest_date]
        latest_cases = latest["caseCount"]

        prev_cases = date_map[dates[1]]["caseCount"] if len(dates) > 1 else latest_cases
        if prev_cases <= 0:
            rate_change = 0.0
        else:
            rate_change = round(((latest_cases - prev_cases) / prev_cases) * 100, 1)

        severity = _normalize_severity(latest["severity_raw"], latest_cases)

        formatted.append({
            "id": next_id,
            "disease": disease_name,
            "location": location_label,
            "caseCount": latest_cases,
            "date": latest_date.isoformat(),
            "severity": severity,
            "newCases24h": latest_cases,
            "rateOfChange": rate_change,
        })
        next_id += 1

    return sorted(formatted, key=lambda item: item["caseCount"], reverse=True)


def register_routes(app):
    @app.post(f"{API_PREFIX}/auth/signup")
    def auth_signup():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        required_error = _require_fields(payload, {"name", "email", "password"})
        if required_error:
            return required_error

        full_name, error_response = _require_non_empty_string(payload.get("name"), "name")
        if error_response:
            return error_response

        email, error_response = _validate_email(payload.get("email"))
        if error_response:
            return error_response

        password, error_response = _validate_password(payload.get("password"))
        if error_response:
            return error_response

        try:
            client = get_supabase_client(current_app)
            result = client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": full_name,
                    }
                },
            })

            try:
                _upsert_user_profile(client, getattr(result, "user", None), full_name)
            except Exception:
                pass

            return _success(_serialize_auth_result(result), 201)
        except Exception as exc:
            return _failure("Failed to create account", 500, str(exc))

    @app.post(f"{API_PREFIX}/auth/login")
    def auth_login():
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        required_error = _require_fields(payload, {"email", "password"})
        if required_error:
            return required_error

        email, error_response = _validate_email(payload.get("email"))
        if error_response:
            return error_response

        password, error_response = _require_non_empty_string(payload.get("password"), "password")
        if error_response:
            return error_response

        try:
            client = get_supabase_client(current_app)
            result = client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            try:
                _upsert_user_profile(
                    client,
                    getattr(result, "user", None),
                    None,
                    update_last_login=True,
                )
            except Exception:
                pass

            return _success(_serialize_auth_result(result), 200)
        except Exception as exc:
            message = str(exc)
            lowered = message.lower()
            if "invalid login credentials" in lowered or "email not confirmed" in lowered:
                return _failure("Invalid email or password", 401, message)
            return _failure("Failed to log in", 500, message)

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

    @app.get(f"{API_PREFIX}/ui/disease-data")
    def ui_disease_data():
        try:
            client = get_supabase_client(current_app)
            query = client.table("cases").select(
                "case_count,date_reported,severity,"
                "diseases(name),"
                "locations(city,state_province)"
            )

            disease = request.args.get("disease")
            start_date = request.args.get("startDate")
            end_date = request.args.get("endDate")
            verified_only = request.args.get("verified_only")

            if disease and disease != "All Diseases":
                disease_id = _get_disease_id_by_name(client, disease)
                if not disease_id:
                    return _success([], 200)
                query = query.eq("disease_id", disease_id)

            if start_date:
                date_error = _validate_iso_date(start_date, "startDate")
                if date_error:
                    return date_error
                query = query.gte("date_reported", start_date)

            if end_date:
                date_error = _validate_iso_date(end_date, "endDate")
                if date_error:
                    return date_error
                query = query.lte("date_reported", end_date)

            if verified_only is not None:
                parsed_verified, bool_error = _parse_bool(verified_only, "verified_only")
                if bool_error:
                    return bool_error
                query = query.eq("verified", parsed_verified)
            else:
                query = query.eq("verified", True)

            result = query.execute()
            formatted = _format_for_frontend(result.data or [])
            return _success(formatted, 200)
        except Exception as exc:
            return _failure("Failed to load UI disease data", 500, str(exc))

    @app.get(f"{API_PREFIX}/ui/disease-types")
    def ui_disease_types():
        try:
            client = get_supabase_client(current_app)
            result = client.table("diseases").select("name").eq("is_active", True).order("name").execute()
            names = [row["name"] for row in (result.data or []) if row.get("name")]
            return _success(["All Diseases", *names], 200)
        except Exception as exc:
            return _failure("Failed to load UI disease types", 500, str(exc))

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

    # ── Auth endpoints (TM20-87, TM20-88) ──────────────────────────────

    @app.post(f"{API_PREFIX}/auth/signup")
    def auth_signup():
        """TM20-87: Create a new user account via Supabase Auth."""
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        email = payload.get("email", "").strip()
        password = payload.get("password", "")

        if not email:
            return _failure("email is required", 400)
        if not password or len(password) < 6:
            return _failure("password must be at least 6 characters", 400)

        try:
            client = get_supabase_client(current_app)
            result = client.auth.sign_up({"email": email, "password": password})

            if hasattr(result, "user") and result.user:
                return _success({
                    "user_id": str(result.user.id),
                    "email": result.user.email,
                    "message": "Account created. Check your email for verification.",
                }, 201)

            return _failure("Signup failed — please try again", 400)
        except Exception as exc:
            msg = str(exc)
            if "already registered" in msg.lower():
                return _failure("An account with this email already exists", 409)
            return _failure("Signup failed", 500, msg)

    @app.post(f"{API_PREFIX}/auth/login")
    def auth_login():
        """TM20-87: Authenticate an existing user via Supabase Auth."""
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        email = payload.get("email", "").strip()
        password = payload.get("password", "")

        if not email:
            return _failure("email is required", 400)
        if not password:
            return _failure("password is required", 400)

        try:
            client = get_supabase_client(current_app)
            result = client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if hasattr(result, "session") and result.session:
                return _success({
                    "user_id": str(result.user.id),
                    "email": result.user.email,
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "role": "user",
                }, 200)

            return _failure("Invalid email or password", 401)
        except Exception as exc:
            msg = str(exc)
            if "invalid" in msg.lower() or "credentials" in msg.lower():
                return _failure("Invalid email or password", 401)
            return _failure("Login failed", 500, msg)

    REQUIRED_VERIFY_FIELDS = {"full_name", "email", "license_number",
                              "issuing_state", "organization"}

    @app.post(f"{API_PREFIX}/auth/verify-official")
    def auth_verify_official():
        """TM20-88: Submit health-official credentials for verification."""
        payload, error_response = _require_json_body()
        if error_response:
            return error_response

        missing = sorted(REQUIRED_VERIFY_FIELDS - set(payload.keys()))
        if missing:
            return _failure("Missing required fields", 400, {"missing": missing})

        for field in REQUIRED_VERIFY_FIELDS:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                return _failure(f"{field} must be a non-empty string", 400)

        try:
            client = get_supabase_client(current_app)
            record = {
                "full_name": payload["full_name"].strip(),
                "email": payload["email"].strip(),
                "license_number": payload["license_number"].strip(),
                "issuing_state": payload["issuing_state"].strip(),
                "organization": payload["organization"].strip(),
                "title": (payload.get("title") or "").strip() or None,
                "verified": False,
                "submitted_at": datetime.utcnow().isoformat(),
            }
            result = (
                client.table("official_verifications")
                .insert(record)
                .execute()
            )
            return _success({
                "message": "Verification request submitted successfully.",
                "verification_status": "pending",
                "role": "pending_official",
            }, 201)
        except Exception as exc:
            return _failure("Failed to submit verification request", 500, str(exc))

    @app.get(f"{API_PREFIX}/auth/verify-official/status")
    def auth_verify_official_status():
        """TM20-89: Check health-official verification status by email."""
        email = request.args.get("email", "").strip()
        if not email:
            return _failure("email query parameter is required", 400)

        try:
            client = get_supabase_client(current_app)
            result = (
                client.table("official_verifications")
                .select("verified")
                .eq("email", email)
                .order("submitted_at", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                return _success({
                    "verification_status": "none",
                    "role": "user",
                }, 200)

            is_verified = result.data[0].get("verified", False)
            return _success({
                "verification_status": "verified" if is_verified else "pending",
                "role": "health_official" if is_verified else "pending_official",
            }, 200)
        except Exception as exc:
            return _failure("Failed to check verification status", 500, str(exc))
