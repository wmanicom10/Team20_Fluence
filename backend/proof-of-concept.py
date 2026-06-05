from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# In-memory storage (stand-in for database owned by someone else)
CASES: List[Dict[str, Any]] = []

# Simple auth stub: require a shared token for protected routes
API_TOKEN = os.environ.get("API_TOKEN", "dev-token")


def require_auth() -> None:
    auth = request.headers.get("Authorization", "")
    # Expect: Authorization: Bearer <token>
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != API_TOKEN:
        abort(401, description="Unauthorized")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health():
    return jsonify(status="ok", time=now_iso())


@app.get("/api/cases")
def list_cases():
    require_auth()
    return jsonify(items=CASES, count=len(CASES))


@app.post("/api/cases")
def create_case():
    require_auth()
    data = request.get_json(silent=True) or {}

    # Minimal validation
    required_fields = ["patient_id", "diagnosis", "reported_at"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        abort(400, description=f"Missing required fields: {', '.join(missing)}")

    new_case = {
        "id": str(uuid.uuid4()),
        "patient_id": str(data["patient_id"]),
        "diagnosis": str(data["diagnosis"]),
        "reported_at": str(data["reported_at"]),
        "notes": str(data.get("notes", "")),
        "created_at": now_iso(),
    }
    CASES.append(new_case)
    return jsonify(new_case), 201


@app.get("/api/cases/<case_id>")
def get_case(case_id: str):
    require_auth()
    for c in CASES:
        if c["id"] == case_id:
            return jsonify(c)
    abort(404, description="Case not found")


@app.put("/api/cases/<case_id>")
def update_case(case_id: str):
    require_auth()
    data = request.get_json(silent=True) or {}

    for c in CASES:
        if c["id"] == case_id:
            # Only allow updating a few fields in this POC
            for field in ["diagnosis", "reported_at", "notes"]:
                if field in data:
                    c[field] = str(data[field])
            c["updated_at"] = now_iso()
            return jsonify(c)
    abort(404, description="Case not found")


@app.post("/api/poll")
def poll_external_sources():
    """
    POC stub to represent polling CDC/state sources on a schedule.
    In a real version, this would call external APIs, normalize data,
    then write to the database via the DB layer.
    """
    require_auth()

    simulated_new_items = [
        {
            "id": str(uuid.uuid4()),
            "patient_id": "external-123",
            "diagnosis": "influenza_like_illness",
            "reported_at": now_iso(),
            "notes": "Simulated import from external source",
            "created_at": now_iso(),
            "source": "external_stub",
        }
    ]

    CASES.extend(simulated_new_items)
    return jsonify(added=len(simulated_new_items), items=simulated_new_items)


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
def handle_error(err):
    return jsonify(error=str(err), message=getattr(err, "description", "Error")), err.code


if __name__ == "__main__":
    # Development server only
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
