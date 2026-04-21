import hashlib
import json
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta
from urllib import parse as urllib_parse
from urllib.error import HTTPError, URLError

from flask import current_app, jsonify, request

import ai_dataset_export
from ai_integration import get_or_train_ai_pipeline, train_ai_pipeline
from services import CaseService, DiseaseService, LocationService


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


class ApiResponse:
    @staticmethod
    def success(data, status_code=200):
        return jsonify({"status": "success", "data": data}), status_code

    @staticmethod
    def failure(message, status_code=400, details=None):
        error = {"message": message}
        if details is not None:
            error["details"] = details
        return jsonify({"status": "error", "error": error}), status_code


class RequestParser:
    @staticmethod
    def require_json_body():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return None, ApiResponse.failure("Request body must be valid JSON", 400)
        return payload, None

    @staticmethod
    def require_fields(payload, required_fields):
        missing = sorted(set(required_fields) - set(payload.keys()))
        if missing:
            return ApiResponse.failure("Missing required fields", 400, {"missing": missing})
        return None

    @staticmethod
    def require_non_empty_strings(payload, field_names):
        for field in field_names:
            if not isinstance(payload[field], str) or not payload[field].strip():
                return ApiResponse.failure(f"{field} must be a non-empty string", 400)
        return None

    @staticmethod
    def parse_bool(value, field_name):
        if isinstance(value, bool):
            return value, None
        lowered = str(value).lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True, None
        if lowered in {"0", "false", "no", "n", "off"}:
            return False, None
        return None, ApiResponse.failure(f"{field_name} must be a boolean value", 400)

    @staticmethod
    def parse_int(value, field_name):
        try:
            return int(value), None
        except (TypeError, ValueError):
            return None, ApiResponse.failure(f"{field_name} must be an integer", 400)

    @staticmethod
    def validate_iso_date(value, field_name):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return None
        except ValueError:
            return ApiResponse.failure(f"{field_name} must use YYYY-MM-DD format", 400)


class TimedCache:
    def __init__(self, store, ttl_provider):
        self._store = store
        self._ttl_provider = ttl_provider

    def get(self, key, now=None):
        now = time.time() if now is None else now
        entry = self._store.get(key)
        if entry and entry["expires_at"] > now:
            return entry["payload"]
        return None

    def get_stale(self, key):
        entry = self._store.get(key)
        return entry["payload"] if entry else None

    def set(self, key, payload, now=None):
        now = time.time() if now is None else now
        self._store[key] = {
            "payload": payload,
            "expires_at": now + self.ttl_seconds(),
        }

    def ttl_seconds(self):
        return int(self._ttl_provider())


class BaseRepository(ABC):
    table_name = ""

    def __init__(self, client):
        self.client = client

    def table(self):
        return self.client.table(self.table_name)


class DiseaseRepository(BaseRepository):
    table_name = "diseases"

    def list(self, active_only=None):
        query = self.table().select("*").order("name")
        if active_only is not None:
            query = query.eq("is_active", active_only)
        return query.execute().data or []

    def create(self, payload):
        return self.table().insert(payload).execute().data or []

    def find_id_by_name(self, disease_name):
        lookup = self.table().select("disease_id").ilike("name", disease_name).limit(1).execute()
        if not lookup.data:
            return None
        return lookup.data[0]["disease_id"]

    def active_names(self):
        result = self.table().select("name").eq("is_active", True).order("name").execute()
        return [row["name"] for row in (result.data or []) if row.get("name")]


class LocationRepository(BaseRepository):
    table_name = "locations"

    def list(self, filters):
        query = self.table().select("*").order("city")
        for field in ("country", "state_province", "city", "region_type"):
            value = filters.get(field)
            if value:
                query = query.eq(field, value)
        return query.execute().data or []

    def create(self, payload):
        return self.table().insert(payload).execute().data or []


class CaseRepository(BaseRepository):
    table_name = "cases"
    base_select = (
        "case_id,case_count,date_reported,severity,verified,data_source,source_api,"
        "diseases(disease_id,name,category,severity_level),"
        "locations(location_id,city,state_province,country,latitude,longitude)"
    )

    def get_by_id(self, case_id):
        result = self.table().select(self.base_select).eq("case_id", case_id).limit(1).execute()
        return result.data[0] if result.data else None

    def exists(self, case_id):
        result = self.table().select("case_id").eq("case_id", case_id).limit(1).execute()
        return bool(result.data)

    def create(self, payload):
        return self.table().insert(payload).execute().data or []

    def update(self, case_id, payload):
        return self.table().update(payload).eq("case_id", case_id).execute().data or []

    def delete(self, case_id):
        self.table().delete().eq("case_id", case_id).execute()

    def list_for_ui(self, disease_id=None, start_date=None, end_date=None, verified_only=True):
        query = self.table().select(
            "case_count,date_reported,severity,diseases(name),locations(city,state_province)"
        )
        if disease_id is not None:
            query = query.eq("disease_id", disease_id)
        if start_date:
            query = query.gte("date_reported", start_date)
        if end_date:
            query = query.lte("date_reported", end_date)
        query = query.eq("verified", verified_only)
        return query.execute().data or []

    def list_for_metrics(self, verified_only):
        result = self.table().select("case_count,diseases(name)").eq("verified", verified_only).execute()
        return result.data or []

    def list_cases(self, filters, disease_repository):
        query = self.table().select(self.base_select)

        if filters.get("disease_id") is not None:
            query = query.eq("disease_id", filters["disease_id"])
        elif filters.get("disease_name"):
            disease_id = disease_repository.find_id_by_name(filters["disease_name"])
            if not disease_id:
                return []
            query = query.eq("disease_id", disease_id)

        if filters.get("date_from"):
            query = query.gte("date_reported", filters["date_from"])
        if filters.get("date_to"):
            query = query.lte("date_reported", filters["date_to"])
        if filters.get("verified_only") is not None:
            query = query.eq("verified", filters["verified_only"])

        return query.order("date_reported", desc=True).execute().data or []


class BaseRowFormatter(ABC):
    @abstractmethod
    def format_rows(self, rows, limit=None):
        raise NotImplementedError


class FrontendDiseaseDataFormatter(BaseRowFormatter):
    @staticmethod
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

    def format_rows(self, rows, limit=None):
        buckets = defaultdict(lambda: defaultdict(lambda: {"caseCount": 0, "severity_raw": None}))
        for row in rows:
            disease_name = (row.get("diseases") or {}).get("name") or "Unknown"
            location = row.get("locations") or {}
            location_label = location.get("city") or "Unknown"
            if location.get("state_province"):
                location_label = f"{location_label}, {location['state_province']}"
            date_reported = row.get("date_reported")
            if not date_reported:
                continue
            try:
                date_obj = datetime.strptime(date_reported, "%Y-%m-%d").date()
            except ValueError:
                continue
            group = buckets[(disease_name, location_label)][date_obj]
            group["caseCount"] += int(row.get("case_count") or 0)
            if row.get("severity"):
                group["severity_raw"] = row["severity"]

        formatted = []
        next_id = 1
        for (disease_name, location_label), date_map in buckets.items():
            dates = sorted(date_map.keys(), reverse=True)
            latest_date = dates[0]
            latest_cases = date_map[latest_date]["caseCount"]
            previous_cases = date_map[dates[1]]["caseCount"] if len(dates) > 1 else latest_cases
            rate_of_change = 0.0 if previous_cases <= 0 else round(((latest_cases - previous_cases) / previous_cases) * 100, 1)
            formatted.append(
                {
                    "id": next_id,
                    "disease": disease_name,
                    "location": location_label,
                    "caseCount": latest_cases,
                    "date": latest_date.isoformat(),
                    "severity": self._normalize_severity(date_map[latest_date]["severity_raw"], latest_cases),
                    "newCases24h": latest_cases,
                    "rateOfChange": rate_of_change,
                }
            )
            next_id += 1

        formatted = sorted(formatted, key=lambda item: item["caseCount"], reverse=True)
        return formatted[:limit] if limit is not None else formatted


class CdcRespiratoryFormatter(BaseRowFormatter):
    @staticmethod
    def _display_name(pathogen):
        return "COVID-19" if pathogen == "COVID" else pathogen

    @staticmethod
    def _severity(percent_visits):
        if percent_visits >= 10:
            return "Critical"
        if percent_visits >= 5:
            return "High"
        if percent_visits >= 2:
            return "Medium"
        return "Low"

    def format_rows(self, rows, limit=None):
        grouped = {}
        for row in rows:
            pathogen = row.get("pathogen")
            geography = row.get("geography")
            date_value = row.get("date")
            if not pathogen or not geography or not date_value:
                continue
            try:
                percent_visits = round(float(row.get("percent_visits")), 2)
                parsed_date = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            except (TypeError, ValueError):
                continue
            snapshot = grouped.setdefault((pathogen, geography), {"latest": None, "previous": None})
            entry = {"date": parsed_date.date().isoformat(), "percent_visits": percent_visits}
            if snapshot["latest"] is None:
                snapshot["latest"] = entry
            elif snapshot["previous"] is None:
                snapshot["previous"] = entry

        formatted = []
        for index, ((pathogen, geography), snapshot) in enumerate(grouped.items(), start=1):
            latest = snapshot["latest"]
            previous = snapshot["previous"]
            if not latest:
                continue
            previous_percent = previous["percent_visits"] if previous else latest["percent_visits"]
            trend = 0.0 if previous_percent <= 0 else round(((latest["percent_visits"] - previous_percent) / previous_percent) * 100, 1)
            formatted.append(
                {
                    "id": f"cdc-{index}",
                    "disease": self._display_name(pathogen),
                    "location": geography,
                    "date": latest["date"],
                    "severity": self._severity(latest["percent_visits"]),
                    "percentVisits": latest["percent_visits"],
                    "previousPercentVisits": previous_percent,
                    "changePoints": round(latest["percent_visits"] - previous_percent, 2),
                    "rateOfChange": trend,
                    "source": "CDC NSSP",
                }
            )

        formatted.sort(key=lambda item: item["percentVisits"], reverse=True)
        return formatted[:limit] if limit is not None else formatted


class DiseaseDataService:
    def __init__(self, disease_repository, case_repository, formatter, cache):
        self.disease_repository = disease_repository
        self.case_repository = case_repository
        self.formatter = formatter
        self.cache = cache

    def get_ui_disease_data(self, disease, start_date, end_date, verified_only, limit):
        cache_key = hashlib.md5(f"{disease}|{start_date}|{end_date}|{verified_only}".encode()).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {"rows": cached[:limit] if limit is not None else cached, "cache_hit": True}

        disease_id = None
        if disease and disease != "All Diseases":
            disease_id = self.disease_repository.find_id_by_name(disease)
            if not disease_id:
                return {"rows": [], "cache_hit": False}

        rows = self.case_repository.get_dashboard_rows(disease_id, start_date, end_date, verified_only)
        formatted = self.formatter.format_rows(rows)
        self.cache.set(cache_key, formatted)
        return {"rows": formatted[:limit] if limit is not None else formatted, "cache_hit": False}


class BaseExternalFeedService(ABC):
    def __init__(self, formatter, cache, fetch_json):
        self.formatter = formatter
        self.cache = cache
        self.fetch_json = fetch_json

    @abstractmethod
    def fetch(self, **filters):
        raise NotImplementedError


class CdcRespiratoryService(BaseExternalFeedService):
    @staticmethod
    def normalize_pathogen(value):
        if not value:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"all", "all diseases"}:
            return None
        if normalized in {"covid", "covid-19"}:
            return "COVID"
        if normalized == "influenza":
            return "Influenza"
        if normalized == "rsv":
            return "RSV"
        if normalized == "ari":
            return "ARI"
        return str(value).strip()

    def fetch(self, pathogen=None, geography=None, limit=12):
        cache_key = hashlib.md5(
            json.dumps({"pathogen": pathogen, "geography": geography, "limit": limit}, sort_keys=True).encode()
        ).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {"payload": cached, "cache_hit": True, "ttl": self.cache.ttl_seconds()}

        requested_pathogens = [pathogen] if pathogen else ["COVID", "Influenza", "RSV"]
        query_params = {
            "$select": "date,pathogen,geography,percent_visits",
            "$order": "date DESC",
            "$limit": str(max(250, limit * 40)),
        }
        where_clauses = [f"pathogen in ({','.join([repr(item) for item in requested_pathogens])})"]
        if geography:
            escaped_geography = str(geography).replace("'", "\\'")
            where_clauses.append(f"geography = '{escaped_geography}'")
        query_params["$where"] = " AND ".join(where_clauses)
        upstream_url = f"https://data.cdc.gov/resource/vjzj-u7u8.json?{urllib_parse.urlencode(query_params)}"

        try:
            rows = self.fetch_json(upstream_url, int(current_app.config.get("EXTERNAL_API_TIMEOUT_SECONDS", 8)))
            payload = {
                "source": "CDC NSSP",
                "filters": {"pathogen": pathogen, "geography": geography, "limit": limit},
                "rows": self.formatter.format_rows(rows or [], limit=limit),
                "cache": {"hit": False, "ttl_seconds": self.cache.ttl_seconds(), "stale_fallback": False},
                "meta": {"upstream": upstream_url, "generated_at": datetime.utcnow().isoformat() + "Z"},
            }
            self.cache.set(cache_key, payload)
            return {"payload": payload, "cache_hit": False, "ttl": self.cache.ttl_seconds()}
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            stale_payload = self.cache.get_stale(cache_key)
            if stale_payload is None:
                raise
            stale_payload = dict(stale_payload)
            stale_payload["cache"] = dict(stale_payload.get("cache") or {})
            stale_payload["cache"]["hit"] = False
            stale_payload["cache"]["stale_fallback"] = True
            stale_payload["meta"] = dict(stale_payload.get("meta") or {})
            stale_payload["meta"]["warning"] = f"Upstream request failed; returned stale cache: {exc}"
            return {"payload": stale_payload, "cache_hit": False, "ttl": self.cache.ttl_seconds()}


class CovidCountriesService(BaseExternalFeedService):
    def fetch(self, countries=None, sort="cases", allow_null=True, yesterday=False, two_days_ago=False):
        filters = {
            "countries": countries or [],
            "sort": sort,
            "allowNull": allow_null,
            "yesterday": yesterday,
            "twoDaysAgo": two_days_ago,
        }
        cache_key = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
        cached = self.cache.get(cache_key)
        if cached is not None:
            payload = dict(cached)
            payload["cache"] = dict(payload.get("cache") or {})
            payload["cache"]["hit"] = True
            return {"payload": payload, "cache_hit": True, "ttl": self.cache.ttl_seconds()}

        country_path = ",".join(countries) if countries else ""
        upstream_url = f"https://disease.sh/v3/covid-19/countries/{urllib_parse.quote(country_path)}?{urllib_parse.urlencode({'allowNull': str(allow_null).lower(), 'sort': sort, 'yesterday': str(yesterday).lower(), 'twoDaysAgo': str(two_days_ago).lower()})}"
        try:
            rows = self.fetch_json(upstream_url, int(current_app.config.get("EXTERNAL_API_TIMEOUT_SECONDS", 8)))
            if isinstance(rows, dict):
                rows = [rows]
            payload = {
                "source": "disease.sh",
                "filters": filters,
                "rows": rows or [],
                "cache": {
                    "hit": False,
                    "stale_fallback": False,
                    "ttl_seconds": self.cache.ttl_seconds(),
                },
                "meta": {
                    "upstream": upstream_url,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                },
            }
            self.cache.set(cache_key, payload)
            return {"payload": payload, "cache_hit": False, "ttl": self.cache.ttl_seconds()}
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            stale_payload = self.cache.get_stale(cache_key)
            if stale_payload is None:
                raise
            stale_payload = dict(stale_payload)
            stale_payload["cache"] = dict(stale_payload.get("cache") or {})
            stale_payload["cache"]["hit"] = False
            stale_payload["cache"]["stale_fallback"] = True
            stale_payload["meta"] = dict(stale_payload.get("meta") or {})
            stale_payload["meta"]["warning"] = f"Upstream request failed; returned stale cache: {exc}"
            return {"payload": stale_payload, "cache_hit": False, "ttl": self.cache.ttl_seconds()}


class MetricsService:
    def __init__(self, case_repository):
        self.case_repository = case_repository

    def cases_by_disease(self, verified_only):
        totals = {}
        for row in self.case_repository.get_metric_rows(verified_only):
            disease_name = (row.get("diseases") or {}).get("name")
            if disease_name:
                totals[disease_name] = totals.get(disease_name, 0) + int(row.get("case_count") or 0)
        return [
            {"disease_name": disease_name, "total_cases": total_cases}
            for disease_name, total_cases in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ]


class AuthService:
    def __init__(self, client):
        self.client = client

    @staticmethod
    def _serialize_user(user):
        if user is None:
            return None
        metadata = getattr(user, "user_metadata", None) or {}
        return {
            "id": getattr(user, "id", None),
            "email": getattr(user, "email", None),
            "email_confirmed_at": getattr(user, "email_confirmed_at", None),
            "last_sign_in_at": getattr(user, "last_sign_in_at", None),
            "name": metadata.get("name"),
        }

    @staticmethod
    def _serialize_session(session):
        if session is None:
            return None
        return {
            "access_token": getattr(session, "access_token", None),
            "refresh_token": getattr(session, "refresh_token", None),
            "token_type": getattr(session, "token_type", None),
            "expires_in": getattr(session, "expires_in", None),
            "expires_at": getattr(session, "expires_at", None),
        }

    def signup(self, name, email, password, email_redirect_to=None):
        options = {"data": {"name": name}}
        if email_redirect_to:
            options["email_redirect_to"] = email_redirect_to

        auth_result = self.client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": options,
            }
        )
        user = getattr(auth_result, "user", None)
        if user is not None:
            try:
                self.client.table("profiles").upsert(
                    {
                        "id": getattr(user, "id", None),
                        "email": email,
                        "name": name,
                    },
                    on_conflict="id",
                ).execute()
            except Exception:
                pass

        return {
            "user": self._serialize_user(user),
            "session": self._serialize_session(getattr(auth_result, "session", None)),
        }

    def login(self, email, password):
        auth_result = self.client.auth.sign_in_with_password({"email": email, "password": password})
        return {
            "user": self._serialize_user(getattr(auth_result, "user", None)),
            "session": self._serialize_session(getattr(auth_result, "session", None)),
        }

    def submit_official_verification(self, payload):
        insert_payload = {
            "full_name": payload["full_name"].strip(),
            "email": payload["email"].strip(),
            "license_number": payload["license_number"].strip(),
            "issuing_state": payload["issuing_state"].strip(),
            "organization": payload["organization"].strip(),
            "title": payload.get("title"),
            "verification_status": "pending",
            "role": "pending_official",
        }
        self.client.table("official_verifications").insert(insert_payload).execute()
        return {
            "message": "Verification request submitted successfully.",
            "verification_status": "pending",
            "role": "pending_official",
        }


class RiskSummaryService:
    def __init__(self, client):
        self.client = client

    @staticmethod
    def _severity_label(value):
        if value is None:
            return "Low"
        if isinstance(value, str):
            key = value.strip().lower()
            score = SEVERITY_SCORES.get(key, 1)
        else:
            score = int(value)
        return SEVERITY_LABELS.get(score, "Low")

    @staticmethod
    def _risk_level(total_cases, highest_severity_score):
        if total_cases >= 100 or highest_severity_score >= 4:
            return "High"
        if total_cases >= 40 or highest_severity_score >= 3:
            return "Medium"
        return "Low"

    @staticmethod
    def _risk_score(total_cases, highest_severity_score):
        case_score = 4 if total_cases >= 100 else 3 if total_cases >= 50 else 2 if total_cases >= 10 else 1
        return max(case_score, highest_severity_score or 1)

    def _find_location(self, location_id=None, city=None, state_province=None, country=None):
        query = self.client.table("locations").select("*")
        if location_id is not None:
            query = query.eq("location_id", location_id)
        else:
            if city:
                query = query.eq("city", city)
            if state_province:
                query = query.eq("state_province", state_province)
            if country:
                query = query.eq("country", country)
        result = query.limit(1).execute()
        return result.data[0] if result.data else None

    def build_summary(self, *, date, location_id=None, city=None, state_province=None, country=None, window_days=7, verified_only=True):
        location = self._find_location(location_id=location_id, city=city, state_province=state_province, country=country)
        if location is None:
            return {
                "summary": {"total_cases": 0, "risk_level": "Low"},
                "diseases": [],
            }

        end_date = datetime.strptime(date, "%Y-%m-%d").date()
        start_date = end_date - timedelta(days=max(window_days, 1) - 1)

        query = self.client.table("cases").select(
            "location_id,case_count,date_reported,severity,verified,diseases(name)"
        ).eq("location_id", location["location_id"]).gte("date_reported", start_date.isoformat()).lte("date_reported", end_date.isoformat())
        if verified_only is not None:
            query = query.eq("verified", verified_only)
        rows = query.execute().data or []

        if not rows:
            return {
                "location": location,
                "as_of_date": date,
                "window_days": window_days,
                "filters": {"verified_only": verified_only},
                "summary": {"total_cases": 0, "risk_level": "Low"},
                "diseases": [],
            }

        disease_totals = {}
        latest_date = None
        latest_day_cases = 0
        previous_window_cases = 0
        highest_severity_score = 1

        for row in rows:
            row_date = datetime.strptime(row["date_reported"], "%Y-%m-%d").date()
            case_count = int(row.get("case_count") or 0)
            disease_name = (row.get("diseases") or {}).get("name") or "Unknown"
            severity_score = SEVERITY_SCORES.get(str(row.get("severity") or "").lower(), 1)
            highest_severity_score = max(highest_severity_score, severity_score)

            entry = disease_totals.setdefault(
                disease_name,
                {"disease": disease_name, "total_cases": 0, "latest_reported_date": row["date_reported"], "severity_score": 1},
            )
            entry["total_cases"] += case_count
            if row["date_reported"] > entry["latest_reported_date"]:
                entry["latest_reported_date"] = row["date_reported"]
            entry["severity_score"] = max(entry["severity_score"], severity_score)

            if latest_date is None or row_date > latest_date:
                if latest_date is not None:
                    previous_window_cases += latest_day_cases
                latest_date = row_date
                latest_day_cases = case_count
            elif row_date == latest_date:
                latest_day_cases += case_count
            else:
                previous_window_cases += case_count

        total_cases = sum(item["total_cases"] for item in disease_totals.values())
        trend_percentage = 0.0 if previous_window_cases <= 0 else round(((latest_day_cases - previous_window_cases) / previous_window_cases) * 100, 1)
        risk_level = self._risk_level(total_cases, highest_severity_score)

        return {
            "location": location,
            "as_of_date": date,
            "window_days": window_days,
            "filters": {"verified_only": verified_only},
            "summary": {
                "total_cases": total_cases,
                "disease_count": len(disease_totals),
                "latest_reported_date": latest_date.isoformat() if latest_date else None,
                "latest_day_cases": latest_day_cases,
                "previous_window_cases": previous_window_cases,
                "trend_percentage": trend_percentage,
                "highest_severity": self._severity_label(highest_severity_score),
                "risk_score": self._risk_score(total_cases, highest_severity_score),
                "risk_level": risk_level,
            },
            "diseases": [
                {
                    "disease": item["disease"],
                    "total_cases": item["total_cases"],
                    "latest_reported_date": item["latest_reported_date"],
                    "severity": self._severity_label(item["severity_score"]),
                }
                for item in sorted(disease_totals.values(), key=lambda row: row["total_cases"], reverse=True)
            ],
        }


class BackendAPI:
    def __init__(self, client_factory, fetch_json, ui_cache_store, external_cache_store, ui_cache_ttl):
        self.client_factory = client_factory
        self.fetch_json = fetch_json
        self.ui_cache_store = ui_cache_store
        self.external_cache_store = external_cache_store
        self.ui_cache_ttl = ui_cache_ttl

    def _repositories(self):
        client = self.client_factory(current_app)
        return DiseaseService(client), LocationService(client), CaseService(client)

    def ui_service(self):
        diseases, _, cases = self._repositories()
        return DiseaseDataService(
            diseases,
            cases,
            FrontendDiseaseDataFormatter(),
            TimedCache(self.ui_cache_store, lambda: self.ui_cache_ttl),
        )

    def cdc_service(self):
        return CdcRespiratoryService(
            CdcRespiratoryFormatter(),
            TimedCache(self.external_cache_store, lambda: current_app.config.get("EXTERNAL_API_CACHE_TTL_SECONDS", 120)),
            self.fetch_json,
        )

    def covid_countries_service(self):
        return CovidCountriesService(
            CdcRespiratoryFormatter(),
            TimedCache(self.external_cache_store, lambda: current_app.config.get("EXTERNAL_API_CACHE_TTL_SECONDS", 120)),
            self.fetch_json,
        )

    def health(self):
        try:
            self.client_factory(current_app).table("diseases").select("disease_id").limit(1).execute()
            return ApiResponse.success({"service": "fluence-backend", "database_connected": True}, 200)
        except Exception as exc:
            return ApiResponse.failure("Database health check failed", 500, str(exc))

    def list_diseases(self):
        try:
            active_only = request.args.get("active_only")
            parsed_active = None
            if active_only is not None:
                parsed_active, error_response = RequestParser.parse_bool(active_only, "active_only")
                if error_response:
                    return error_response
            diseases, _, _ = self._repositories()
            return ApiResponse.success(diseases.get_all(parsed_active), 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to load diseases", 500, str(exc))

    def create_disease(self):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        required_fields = {"name", "category", "severity_level"}
        error_response = RequestParser.require_fields(payload, required_fields) or RequestParser.require_non_empty_strings(payload, required_fields)
        if error_response:
            return error_response
        try:
            diseases, _, _ = self._repositories()
            insert_payload = {
                "name": payload["name"].strip(),
                "category": payload["category"].strip(),
                "severity_level": payload["severity_level"].strip(),
                "description": payload.get("description"),
                "is_active": True,
            }
            if "is_active" in payload:
                insert_payload["is_active"], error_response = RequestParser.parse_bool(payload["is_active"], "is_active")
                if error_response:
                    return error_response
            return ApiResponse.success(diseases.create(insert_payload), 201)
        except Exception as exc:
            return ApiResponse.failure("Failed to create disease", 500, str(exc))

    def auth_signup(self):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        required_fields = {"name", "email", "password"}
        error_response = RequestParser.require_fields(payload, required_fields) or RequestParser.require_non_empty_strings(payload, required_fields)
        if error_response:
            return error_response
        if len(payload["password"]) < 8:
            return ApiResponse.failure("password must be at least 8 characters long", 400)
        try:
            service = AuthService(self.client_factory(current_app))
            return ApiResponse.success(
                service.signup(
                    payload["name"].strip(),
                    payload["email"].strip(),
                    payload["password"],
                    payload.get("emailRedirectTo") or payload.get("email_redirect_to"),
                ),
                201,
            )
        except Exception as exc:
            message = str(exc) or "Unexpected signup error"
            lowered = message.lower()
            if "already registered" in lowered:
                return ApiResponse.failure("User already registered", 409, message)
            if "rate limit" in lowered:
                return ApiResponse.failure("Email rate limit exceeded", 429, message)
            if "password" in lowered:
                return ApiResponse.failure("Invalid signup request", 400, message)
            if "email" in lowered and "invalid" in lowered:
                return ApiResponse.failure("Invalid signup request", 400, message)
            return ApiResponse.failure("Failed to sign up", 500, message)

    def auth_login(self):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        required_fields = {"email", "password"}
        error_response = RequestParser.require_fields(payload, required_fields) or RequestParser.require_non_empty_strings(payload, required_fields)
        if error_response:
            return error_response
        try:
            service = AuthService(self.client_factory(current_app))
            return ApiResponse.success(service.login(payload["email"].strip(), payload["password"]), 200)
        except Exception as exc:
            if "Invalid login credentials" in str(exc):
                return ApiResponse.failure("Invalid email or password", 401, str(exc))
            return ApiResponse.failure("Failed to log in", 500, str(exc))

    def verify_official(self):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        required_fields = {"full_name", "email", "license_number", "issuing_state", "organization"}
        error_response = RequestParser.require_fields(payload, required_fields) or RequestParser.require_non_empty_strings(payload, required_fields)
        if error_response:
            return error_response
        try:
            service = AuthService(self.client_factory(current_app))
            return ApiResponse.success(service.submit_official_verification(payload), 201)
        except Exception as exc:
            return ApiResponse.failure("Failed to submit verification request", 500, str(exc))

    def verify_official_status(self):
        email = request.args.get("email")
        if not email:
            return ApiResponse.failure("email query parameter is required", 400)
        try:
            client = self.client_factory(current_app)
            result = client.table("official_verifications").select("*").eq("email", email).limit(1).execute()
            if not result.data:
                return ApiResponse.success({"verification_status": "not_found", "role": "public"}, 200)
            row = result.data[0]
            return ApiResponse.success(
                {
                    "verification_status": row.get("verification_status", "pending"),
                    "role": row.get("role", "pending_official"),
                },
                200,
            )
        except Exception as exc:
            return ApiResponse.failure("Failed to load verification status", 500, str(exc))

    def list_locations(self):
        try:
            _, locations, _ = self._repositories()
            return ApiResponse.success(locations.get_all(request.args), 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to load locations", 500, str(exc))

    def create_location(self):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        required_fields = {"country", "city"}
        error_response = RequestParser.require_fields(payload, required_fields) or RequestParser.require_non_empty_strings(payload, required_fields)
        if error_response:
            return error_response
        try:
            _, locations, _ = self._repositories()
            return ApiResponse.success(
                locations.create(
                    {
                        "country": payload["country"].strip(),
                        "state_province": payload.get("state_province"),
                        "city": payload["city"].strip(),
                        "latitude": payload.get("latitude"),
                        "longitude": payload.get("longitude"),
                        "population": payload.get("population"),
                        "region_type": payload.get("region_type"),
                    }
                ),
                201,
            )
        except Exception as exc:
            return ApiResponse.failure("Failed to create location", 500, str(exc))

    def list_cases(self):
        try:
            filters = {
                "disease_id": None,
                "disease_name": request.args.get("disease_name"),
                "date_from": request.args.get("date_from"),
                "date_to": request.args.get("date_to"),
                "verified_only": None,
            }
            if request.args.get("disease_id"):
                filters["disease_id"], error_response = RequestParser.parse_int(request.args.get("disease_id"), "disease_id")
                if error_response:
                    return error_response
            if filters["date_from"]:
                error_response = RequestParser.validate_iso_date(filters["date_from"], "date_from")
                if error_response:
                    return error_response
            if filters["date_to"]:
                error_response = RequestParser.validate_iso_date(filters["date_to"], "date_to")
                if error_response:
                    return error_response
            if request.args.get("verified_only") is not None:
                filters["verified_only"], error_response = RequestParser.parse_bool(request.args.get("verified_only"), "verified_only")
                if error_response:
                    return error_response
            diseases, _, cases = self._repositories()
            return ApiResponse.success(cases.get_all(filters, diseases), 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to load cases", 500, str(exc))

    def get_case(self, case_id):
        try:
            _, _, cases = self._repositories()
            case = cases.get_by_id(case_id)
            if case is None:
                return ApiResponse.failure("Case not found", 404)
            return ApiResponse.success(case, 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to load case", 500, str(exc))

    def create_case(self, required_case_fields):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        error_response = RequestParser.require_fields(payload, required_case_fields)
        if error_response:
            return error_response

        parsed_disease_id, error_response = RequestParser.parse_int(payload["disease_id"], "disease_id")
        if error_response:
            return error_response
        parsed_location_id, error_response = RequestParser.parse_int(payload["location_id"], "location_id")
        if error_response:
            return error_response
        parsed_case_count, error_response = RequestParser.parse_int(payload["case_count"], "case_count")
        if error_response:
            return error_response
        if parsed_case_count < 0:
            return ApiResponse.failure("case_count must be >= 0", 400)
        error_response = RequestParser.validate_iso_date(str(payload["date_reported"]), "date_reported")
        if error_response:
            return error_response

        parsed_verified = False
        if "verified" in payload:
            parsed_verified, error_response = RequestParser.parse_bool(payload["verified"], "verified")
            if error_response:
                return error_response

        try:
            _, _, cases = self._repositories()
            return ApiResponse.success(
                cases.create(
                    {
                        "disease_id": parsed_disease_id,
                        "location_id": parsed_location_id,
                        "case_count": parsed_case_count,
                        "date_reported": payload["date_reported"],
                        "data_source": payload.get("data_source", "manual_submission"),
                        "source_api": payload.get("source_api"),
                        "severity": payload.get("severity"),
                        "verified": parsed_verified,
                    }
                ),
                201,
            )
        except Exception as exc:
            return ApiResponse.failure("Failed to create case", 500, str(exc))

    def update_case(self, case_id, allowed_case_update_fields):
        payload, error_response = RequestParser.require_json_body()
        if error_response:
            return error_response
        update_fields = {key: value for key, value in payload.items() if key in allowed_case_update_fields}
        if not update_fields:
            return ApiResponse.failure("No valid fields provided", 400, {"allowed_fields": sorted(allowed_case_update_fields)})

        for field in ("disease_id", "location_id", "case_count"):
            if field in update_fields:
                update_fields[field], error_response = RequestParser.parse_int(update_fields[field], field)
                if error_response:
                    return error_response
        if "case_count" in update_fields and update_fields["case_count"] < 0:
            return ApiResponse.failure("case_count must be >= 0", 400)
        if "date_reported" in update_fields:
            error_response = RequestParser.validate_iso_date(str(update_fields["date_reported"]), "date_reported")
            if error_response:
                return error_response
        if "verified" in update_fields:
            update_fields["verified"], error_response = RequestParser.parse_bool(update_fields["verified"], "verified")
            if error_response:
                return error_response

        try:
            _, _, cases = self._repositories()
            if not cases.exists(case_id):
                return ApiResponse.failure("Case not found", 404)
            return ApiResponse.success(cases.update(case_id, update_fields), 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to update case", 500, str(exc))

    def delete_case(self, case_id):
        try:
            _, _, cases = self._repositories()
            if not cases.exists(case_id):
                return ApiResponse.failure("Case not found", 404)
            cases.delete(case_id)
            return ApiResponse.success({"deleted": True, "case_id": case_id}, 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to delete case", 500, str(exc))

    def ui_disease_data(self):
        try:
            disease = request.args.get("disease")
            start_date = request.args.get("startDate")
            end_date = request.args.get("endDate")
            verified_only = request.args.get("verified_only")
            limit = request.args.get("limit")
            if start_date:
                error_response = RequestParser.validate_iso_date(start_date, "startDate")
                if error_response:
                    return error_response
            if end_date:
                error_response = RequestParser.validate_iso_date(end_date, "endDate")
                if error_response:
                    return error_response
            parsed_verified = True
            if verified_only is not None:
                parsed_verified, error_response = RequestParser.parse_bool(verified_only, "verified_only")
                if error_response:
                    return error_response
            parsed_limit = None
            if limit is not None:
                parsed_limit, error_response = RequestParser.parse_int(limit, "limit")
                if error_response:
                    return error_response
                if parsed_limit < 1:
                    return ApiResponse.failure("limit must be >= 1", 400)
            result = self.ui_service().get_ui_disease_data(disease, start_date, end_date, parsed_verified, parsed_limit)
            response = ApiResponse.success(result["rows"], 200)
            response[0].headers["Cache-Control"] = f"public, max-age={self.ui_cache_ttl}"
            response[0].headers["X-Cache"] = "HIT" if result["cache_hit"] else "MISS"
            return response
        except Exception as exc:
            return ApiResponse.failure("Failed to load UI disease data", 500, str(exc))

    def ui_disease_types(self):
        try:
            diseases, _, _ = self._repositories()
            return ApiResponse.success(["All Diseases", *diseases.get_active_names()], 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to load UI disease types", 500, str(exc))

    def external_cdc_respiratory_daily(self):
        pathogen = CdcRespiratoryService.normalize_pathogen(request.args.get("pathogen"))
        geography = request.args.get("geography")
        parsed_limit, error_response = RequestParser.parse_int(request.args.get("limit", "12"), "limit")
        if error_response:
            return error_response
        if parsed_limit < 1:
            return ApiResponse.failure("limit must be >= 1", 400)
        if pathogen and pathogen not in {"COVID", "Influenza", "RSV", "ARI"}:
            return ApiResponse.failure("Unsupported CDC pathogen filter", 400, {"pathogen": pathogen})
        try:
            result = self.cdc_service().fetch(pathogen=pathogen, geography=geography, limit=parsed_limit)
            response = ApiResponse.success(result["payload"], 200)
            response[0].headers["Cache-Control"] = f"public, max-age={result['ttl']}"
            response[0].headers["X-Cache"] = "HIT" if result["cache_hit"] else "MISS"
            return response
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            return ApiResponse.failure("Failed to load external CDC respiratory data", 502, str(exc))

    def external_covid_countries(self):
        countries_param = request.args.get("countries")
        countries = [item.strip() for item in (countries_param or "").split(",") if item.strip()]
        sort = request.args.get("sort", "cases")
        allow_null, error_response = RequestParser.parse_bool(request.args.get("allowNull", "true"), "allowNull")
        if error_response:
            return error_response
        yesterday, error_response = RequestParser.parse_bool(request.args.get("yesterday", "false"), "yesterday")
        if error_response:
            return error_response
        two_days_ago, error_response = RequestParser.parse_bool(request.args.get("twoDaysAgo", "false"), "twoDaysAgo")
        if error_response:
            return error_response
        try:
            result = self.covid_countries_service().fetch(
                countries=countries,
                sort=sort,
                allow_null=allow_null,
                yesterday=yesterday,
                two_days_ago=two_days_ago,
            )
            response = ApiResponse.success(result["payload"], 200)
            response[0].headers["Cache-Control"] = f"public, max-age={result['ttl']}"
            response[0].headers["X-Cache"] = "HIT" if result["cache_hit"] else "MISS"
            return response
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            return ApiResponse.failure("Failed to load external disease data", 502, str(exc))

    def ai_train(self):
        try:
            trained = train_ai_pipeline(current_app, filters=request.get_json(silent=True) or {}, client_factory=self.client_factory)
            return ApiResponse.success({"model": {"model_version": trained["model"].get("model_version"), "generated_at": trained["model"].get("generated_at"), "training_examples": trained["model"].get("training_examples")}, "validation": trained["validation"].get("meta"), "risk_output_count": len(trained["risk_output"])}, 200)
        except ValueError as exc:
            return ApiResponse.failure("Invalid AI training request", 400, str(exc))
        except Exception as exc:
            return ApiResponse.failure("Failed to train AI pipeline", 500, str(exc))

    def ai_risk_output(self):
        try:
            date_value = request.args.get("date")
            if not date_value:
                return ApiResponse.failure("date query parameter is required", 400)
            error_response = RequestParser.validate_iso_date(date_value, "date")
            if error_response:
                return error_response

            parsed_location_id = None
            if request.args.get("location_id"):
                parsed_location_id, error_response = RequestParser.parse_int(request.args.get("location_id"), "location_id")
                if error_response:
                    return error_response

            parsed_window_days = 7
            if request.args.get("window_days"):
                parsed_window_days, error_response = RequestParser.parse_int(request.args.get("window_days"), "window_days")
                if error_response:
                    return error_response

            parsed_verified = True
            if request.args.get("verified_only") is not None:
                parsed_verified, error_response = RequestParser.parse_bool(request.args.get("verified_only"), "verified_only")
                if error_response:
                    return error_response

            service = RiskSummaryService(self.client_factory(current_app))
            summary = service.build_summary(
                date=date_value,
                location_id=parsed_location_id,
                city=request.args.get("city"),
                state_province=request.args.get("state_province"),
                country=request.args.get("country"),
                window_days=parsed_window_days,
                verified_only=parsed_verified,
            )
            return ApiResponse.success(summary, 200)
        except ValueError as exc:
            return ApiResponse.failure("Invalid AI risk request", 400, str(exc))
        except Exception as exc:
            return ApiResponse.failure("Failed to build AI risk output", 500, str(exc))

    def ui_ai_risk(self):
        try:
            filters = {"disease": request.args.get("disease"), "startDate": request.args.get("startDate"), "endDate": request.args.get("endDate"), "verified_only": request.args.get("verified_only")}
            trained = get_or_train_ai_pipeline(current_app, filters=filters, client_factory=self.client_factory)
            return ApiResponse.success(trained["risk_output"], 200)
        except ValueError as exc:
            return ApiResponse.failure("Invalid AI dashboard request", 400, str(exc))
        except Exception as exc:
            return ApiResponse.failure("Failed to load dashboard AI risk output", 500, str(exc))

    def cases_by_disease_stats(self):
        try:
            parsed_verified = True
            if request.args.get("verified_only") is not None:
                parsed_verified, error_response = RequestParser.parse_bool(request.args.get("verified_only"), "verified_only")
                if error_response:
                    return error_response
            _, _, cases = self._repositories()
            return ApiResponse.success(MetricsService(cases).cases_by_disease(parsed_verified), 200)
        except Exception as exc:
            return ApiResponse.failure("Failed to compute case metrics", 500, str(exc))

    def training_dataset(self):
        try:
            filters = {
                "disease": request.args.get("disease"),
                "start_date": request.args.get("start_date"),
                "end_date": request.args.get("end_date"),
                "verified_only": request.args.get("verified_only"),
            }
            dataset = ai_dataset_export.export_training_dataset(current_app, filters)
            response_format = (request.args.get("format") or "json").lower()
            if response_format == "csv":
                csv_text = ai_dataset_export.dataset_to_csv(dataset)
                return current_app.response_class(csv_text, mimetype="text/csv", status=200)
            return ApiResponse.success(dataset, 200)
        except ValueError as exc:
            return ApiResponse.failure("Invalid training dataset request", 400, str(exc))
        except Exception as exc:
            return ApiResponse.failure("Failed to export training dataset", 500, str(exc))
