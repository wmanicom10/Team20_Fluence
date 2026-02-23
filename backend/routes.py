from flask import jsonify


def register_routes(app):
    # Health check
    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "fluence-backend"
        }), 200

    # Stub endpoints (DB wiring will be done later by the DB/task owner)
    @app.get("/cases")
    def get_cases():
        return jsonify({
            "message": "Cases endpoint stub (DB not wired yet)",
            "data": []
        }), 200

    @app.get("/diseases")
    def get_diseases():
        return jsonify({
            "message": "Diseases endpoint stub (DB not wired yet)",
            "data": []
        }), 200
