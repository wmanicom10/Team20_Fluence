from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any, Dict, Iterable, List, Tuple


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _safe_pct_change(current: int, previous: int) -> float:
    if previous <= 0:
        return 0.0 if current <= 0 else 100.0
    return round(((current - previous) / previous) * 100.0, 2)


def _risk_level(score: float) -> str:
    if score >= 0.8:
        return "Critical"
    if score >= 0.6:
        return "High"
    if score >= 0.35:
        return "Medium"
    return "Low"


def _action_for_level(level: str) -> str:
    return {
        "Critical": "Escalate immediately and highlight on dashboard.",
        "High": "Monitor closely and flag for review.",
        "Medium": "Track trend and re-check on next refresh.",
        "Low": "No immediate action required.",
    }[level]


def build_feature_rows(normalized_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in normalized_rows:
        buckets[(row["disease"], row["location"])].append(row)

    feature_rows: List[Dict[str, Any]] = []

    for (disease, location), rows in buckets.items():
        sorted_rows = sorted(rows, key=lambda item: item["date_reported"])
        counts = [int(item["case_count"]) for item in sorted_rows]
        latest = sorted_rows[-1]
        latest_count = counts[-1]
        previous_count = counts[-2] if len(counts) > 1 else latest_count
        avg_cases = round(mean(counts), 2)
        max_cases = max(counts) if counts else 0
        trend_pct = _safe_pct_change(latest_count, previous_count)
        verified_ratio = round(sum(1 for item in sorted_rows if item.get("verified")) / len(sorted_rows), 3)
        severity_score = max(int(item.get("severity_score") or 1) for item in sorted_rows)

        feature_rows.append({
            "disease": disease,
            "location": location,
            "date": latest["date_reported"],
            "current_cases": latest_count,
            "previous_cases": previous_count,
            "avg_cases": avg_cases,
            "max_cases": max_cases,
            "trend_pct": trend_pct,
            "severity_score": severity_score,
            "verified_ratio": verified_ratio,
            "history_points": len(sorted_rows),
        })

    return sorted(feature_rows, key=lambda item: item["current_cases"], reverse=True)


def train_baseline_pipeline(normalized_rows: Iterable[Dict[str, Any]], model_version: str = "baseline-v1") -> Dict[str, Any]:
    feature_rows = build_feature_rows(normalized_rows)
    if not feature_rows:
        return {
            "model_version": model_version,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "training_examples": 0,
            "features": [],
            "params": {
                "max_current_cases": 1,
                "max_avg_cases": 1,
                "max_trend_pct": 1,
            },
        }

    max_current_cases = max(1, max(item["current_cases"] for item in feature_rows))
    max_avg_cases = max(1, max(item["avg_cases"] for item in feature_rows))
    max_trend_pct = max(1.0, max(abs(item["trend_pct"]) for item in feature_rows))

    return {
        "model_version": model_version,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "training_examples": len(feature_rows),
        "features": feature_rows,
        "params": {
            "max_current_cases": max_current_cases,
            "max_avg_cases": max_avg_cases,
            "max_trend_pct": max_trend_pct,
        },
    }


def score_risk_output(model: Dict[str, Any]) -> List[Dict[str, Any]]:
    params = model.get("params") or {}
    max_current_cases = max(1, int(params.get("max_current_cases") or 1))
    max_avg_cases = max(1, float(params.get("max_avg_cases") or 1))
    max_trend_pct = max(1.0, float(params.get("max_trend_pct") or 1.0))

    outputs: List[Dict[str, Any]] = []
    for index, item in enumerate(model.get("features") or [], start=1):
        case_component = item["current_cases"] / max_current_cases
        avg_component = float(item["avg_cases"]) / max_avg_cases
        trend_component = abs(float(item["trend_pct"])) / max_trend_pct
        severity_component = int(item["severity_score"]) / 4.0
        verification_component = float(item["verified_ratio"])

        score = (
            0.40 * case_component
            + 0.20 * avg_component
            + 0.20 * trend_component
            + 0.15 * severity_component
            + 0.05 * verification_component
        )
        score = round(_clamp01(score), 4)
        level = _risk_level(score)

        outputs.append({
            "id": index,
            "disease": item["disease"],
            "location": item["location"],
            "date": item["date"],
            "riskScore": score,
            "riskLevel": level,
            "caseCount": item["current_cases"],
            "previousCaseCount": item["previous_cases"],
            "averageCases": item["avg_cases"],
            "trendPct": item["trend_pct"],
            "severityScore": item["severity_score"],
            "verifiedRatio": item["verified_ratio"],
            "historyPoints": item["history_points"],
            "recommendedAction": _action_for_level(level),
            "modelVersion": model.get("model_version"),
        })

    return sorted(outputs, key=lambda item: item["riskScore"], reverse=True)
