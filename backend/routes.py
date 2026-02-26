from flask import current_app, jsonify, request

from db import get_supabase_client


def _as_bool(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y", "on"}


def register_routes(app):
    @app.get("/health")
    def health():
        try:
            client = get_supabase_client(current_app)
            result = client.table("diseases").select("disease_id").limit(1).execute()
            connected = result is not None
        except Exception:
            connected = False

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
            return jsonify({
                "message": "Diseases loaded from database",
                "data": result.data or [],
            }), 200
        except Exception as exc:
            return jsonify({
                "message": "Failed to load diseases from database",
                "error": str(exc),
            }), 500

    @app.get("/cases")
    def get_cases():
        try:
            client = get_supabase_client(current_app)
            query = client.table("cases").select(
                "case_id,case_count,date_reported,severity,verified,data_source,"
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
                disease_lookup = (
                    client.table("diseases")
                    .select("disease_id")
                    .ilike("name", disease_name)
                    .limit(1)
                    .execute()
                )
                if not disease_lookup.data:
                    return jsonify({"message": f'Disease "{disease_name}" not found', "data": []}), 200
                query = query.eq("disease_id", disease_lookup.data[0]["disease_id"])

            if date_from:
                query = query.gte("date_reported", date_from)
            if date_to:
                query = query.lte("date_reported", date_to)
            if verified_only is not None and _as_bool(verified_only):
                query = query.eq("verified", True)

            result = query.order("date_reported", desc=True).execute()

            return jsonify({
                "message": "Cases loaded from database",
                "data": result.data or [],
            }), 200
        except Exception as exc:
            return jsonify({
                "message": "Failed to load cases from database",
                "error": str(exc),
            }), 500
