import json
from urllib import request as urllib_request

from flask import request

from db import get_supabase_client
from oop_api import BackendAPI


API_PREFIX = "/api"

UI_DISEASE_DATA_CACHE_TTL = 30
_ui_disease_data_cache = {}
_external_api_cache = {}

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


def _fetch_json_from_url(url, timeout_seconds):
    request_obj = urllib_request.Request(
        url,
        headers={
            "User-Agent": "Fluence/1.0",
            "Accept": "application/json",
        },
    )
    with urllib_request.urlopen(request_obj, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def register_routes(app):
    api = BackendAPI(
        client_factory=lambda app_context: get_supabase_client(app_context),
        fetch_json=_fetch_json_from_url,
        ui_cache_store=_ui_disease_data_cache,
        external_cache_store=_external_api_cache,
        ui_cache_ttl=UI_DISEASE_DATA_CACHE_TTL,
    )

    @app.get(f"{API_PREFIX}/health")
    def health():
        return api.health()

    @app.post(f"{API_PREFIX}/auth/signup")
    def auth_signup():
        return api.auth_signup()

    @app.post(f"{API_PREFIX}/auth/login")
    def auth_login():
        return api.auth_login()

    @app.post(f"{API_PREFIX}/auth/verify-official")
    def verify_official():
        return api.verify_official()

    @app.get(f"{API_PREFIX}/auth/verify-official/status")
    def verify_official_status():
        return api.verify_official_status()

    @app.get(f"{API_PREFIX}/diseases")
    def get_diseases():
        return api.list_diseases()

    @app.post(f"{API_PREFIX}/diseases")
    def create_disease():
        return api.create_disease()

    @app.get(f"{API_PREFIX}/locations")
    def get_locations():
        return api.list_locations()

    @app.post(f"{API_PREFIX}/locations")
    def create_location():
        return api.create_location()

    @app.get(f"{API_PREFIX}/cases")
    def get_cases():
        return api.list_cases()

    @app.get(f"{API_PREFIX}/cases/<int:case_id>")
    def get_case_by_id(case_id):
        return api.get_case(case_id)

    @app.post(f"{API_PREFIX}/cases")
    def create_case():
        return api.create_case(REQUIRED_CASE_FIELDS)

    @app.patch(f"{API_PREFIX}/cases/<int:case_id>")
    def update_case(case_id):
        return api.update_case(case_id, ALLOWED_CASE_UPDATE_FIELDS)

    @app.delete(f"{API_PREFIX}/cases/<int:case_id>")
    def delete_case(case_id):
        return api.delete_case(case_id)

    @app.get(f"{API_PREFIX}/ui/disease-data")
    def ui_disease_data():
        return api.ui_disease_data()

    @app.get(f"{API_PREFIX}/ui/disease-types")
    def ui_disease_types():
        return api.ui_disease_types()

    @app.get(f"{API_PREFIX}/external/cdc/respiratory-daily")
    def external_cdc_respiratory_daily():
        return api.external_cdc_respiratory_daily()

    @app.get(f"{API_PREFIX}/external/covid/countries")
    def external_covid_countries():
        return api.external_covid_countries()

    @app.post(f"{API_PREFIX}/ai/train")
    def ai_train():
        return api.ai_train()

    @app.get(f"{API_PREFIX}/ai/risk-output")
    def ai_risk_output():
        return api.ai_risk_output()

    @app.get(f"{API_PREFIX}/ui/ai-risk")
    def ui_ai_risk():
        return api.ui_ai_risk()

    @app.get(f"{API_PREFIX}/ai/training-dataset")
    def training_dataset():
        return api.training_dataset()

    @app.get(f"{API_PREFIX}/metrics/cases-by-disease")
    def cases_by_disease_stats():
        return api.cases_by_disease_stats()
