"""
prediction.py - Defect Prediction Module.
Implements a transparent, explainable, multi-factor defect risk prediction algorithm.
Calculates module risk scores (0-100), risk tiers, factor contributions, and targeted mitigation actions.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd
from database import get_connection


# Weighted scoring constants (Weights sum to 1.0)
WEIGHT_VOLUME = 0.25
WEIGHT_SEVERITY = 0.30
WEIGHT_UNRESOLVED = 0.20
WEIGHT_REOPEN = 0.15
WEIGHT_RECENCY = 0.10


def calculate_risk_level(score: float) -> str:
    """Classify risk score into academic risk categories."""
    if score >= 80:
        return "Critical Risk"
    elif score >= 60:
        return "High Risk"
    elif score >= 30:
        return "Medium Risk"
    else:
        return "Low Risk"


def get_risk_badge_color(level: str) -> str:
    """Return UI color code associated with risk category."""
    mapping = {
        "Critical Risk": "#dc3545",  # Crimson Red
        "High Risk": "#fd7e14",      # Deep Orange
        "Medium Risk": "#ffc107",    # Amber Yellow
        "Low Risk": "#28a745"        # Forest Green
    }
    return mapping.get(level, "#6c757d")


def predict_module_defects(db_path: str = None) -> List[Dict[str, Any]]:
    """
    Transparent Risk-Scoring Prediction Algorithm.
    Evaluates historical defect metrics across all software modules:
    - Defect Volume (25%)
    - Defect Severity Impact (30%)
    - Unresolved Technical Debt (20%)
    - Code Fragility & Reopens (15%)
    - Recent Defect Velocity (10%)
    
    Returns explainable risk scores (0-100) and actionable mitigation steps.
    """
    conn = get_connection(db_path)
    df_defects = pd.read_sql_query("""
        SELECT id, defect_code, module, severity, priority, status, created_at
        FROM defects
    """, conn)
    df_history = pd.read_sql_query("""
        SELECT defect_id, new_status FROM defect_history WHERE new_status = 'REOPENED'
    """, conn)
    conn.close()

    if df_defects.empty:
        return []

    # Identify defects that were ever reopened
    reopened_defect_ids = set(df_history["defect_id"].tolist())

    # Date cutoff for recency (last 30 days)
    now = datetime.now()
    cutoff_date = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    modules_predictions = []

    for module_name, group in df_defects.groupby("module"):
        total_m = len(group)
        critical_m = len(group[group["severity"] == "Critical"])
        high_m = len(group[group["severity"] == "High"])
        medium_m = len(group[group["severity"] == "Medium"])
        low_m = len(group[group["severity"] == "Low"])

        # Unresolved defects: NEW, ASSIGNED, IN PROGRESS, REOPENED
        unresolved_m = len(group[group["status"].isin(["NEW", "ASSIGNED", "IN PROGRESS", "REOPENED"])])

        # Ever reopened defects in this module
        reopen_m = len(group[group["id"].isin(reopened_defect_ids) | (group["status"] == "REOPENED")])

        # Recent defects in last 30 days
        recent_m = len(group[group["created_at"] >= cutoff_date])

        # --- 1. Defect Volume Factor (Weight: 25%) ---
        # Saturated at 5 defects = 100%
        score_volume = min(100.0, (total_m / 5.0) * 100.0)

        # --- 2. Severity Factor (Weight: 30%) ---
        # Critical = 4.0, High = 2.5, Medium = 1.0, Low = 0.25
        # Saturated at raw severity sum of 10.0 = 100%
        raw_sev = (critical_m * 4.0) + (high_m * 2.5) + (medium_m * 1.0) + (low_m * 0.25)
        score_severity = min(100.0, (raw_sev / 10.0) * 100.0)

        # --- 3. Unresolved Technical Debt Factor (Weight: 20%) ---
        ratio_unresolved = (unresolved_m / total_m) if total_m > 0 else 0
        volume_scale = min(1.0, unresolved_m / 2.0)
        score_unresolved = ratio_unresolved * 100.0 * volume_scale

        # --- 4. Code Fragility & Reopen Factor (Weight: 15%) ---
        # 1 reopen = 50%, 2+ reopens = 100%
        score_reopen = min(100.0, reopen_m * 50.0)

        # --- 5. Recency Velocity Factor (Weight: 10%) ---
        # 3 recent bugs in 30 days = 100%
        score_recency = min(100.0, (recent_m / 3.0) * 100.0)

        # Composite Weighted Calculation
        composite_score = (
            (score_volume * WEIGHT_VOLUME) +
            (score_severity * WEIGHT_SEVERITY) +
            (score_unresolved * WEIGHT_UNRESOLVED) +
            (score_reopen * WEIGHT_REOPEN) +
            (score_recency * WEIGHT_RECENCY)
        )

        final_score = round(max(0.0, min(100.0, composite_score)), 1)
        risk_level = calculate_risk_level(final_score)
        badge_color = get_risk_badge_color(risk_level)

        # Recommendations based on contributing factors
        recommendations = []
        if critical_m > 0:
            recommendations.append(f"Execute immediate security/critical audits on {critical_m} critical failure points.")
        if unresolved_m > 1:
            recommendations.append(f"Clear active backlog of {unresolved_m} open defects before new feature development.")
        if reopen_m > 0:
            recommendations.append("Module exhibits defect regression (reopened bugs). Review root cause fixes and unit test suites.")
        if recent_m >= 2:
            recommendations.append(f"High velocity of {recent_m} recent defects logged within 30 days. Prioritize regression testing.")
        if not recommendations:
            recommendations.append("Module exhibits healthy stability metrics. Maintain standard test coverage.")

        modules_predictions.append({
            "module": module_name,
            "total_defects": total_m,
            "critical_defects": critical_m,
            "high_defects": high_m,
            "unresolved_defects": unresolved_m,
            "reopened_defects": reopen_m,
            "recent_defects": recent_m,
            "risk_score": final_score,
            "risk_level": risk_level,
            "badge_color": badge_color,
            "factors": {
                "volume": {"raw": total_m, "normalized": round(score_volume, 1), "contribution": round(score_volume * WEIGHT_VOLUME, 1)},
                "severity": {"raw": round(raw_sev, 2), "normalized": round(score_severity, 1), "contribution": round(score_severity * WEIGHT_SEVERITY, 1)},
                "unresolved": {"raw": unresolved_m, "normalized": round(score_unresolved, 1), "contribution": round(score_unresolved * WEIGHT_UNRESOLVED, 1)},
                "reopen": {"raw": reopen_m, "normalized": round(score_reopen, 1), "contribution": round(score_reopen * WEIGHT_REOPEN, 1)},
                "recency": {"raw": recent_m, "normalized": round(score_recency, 1), "contribution": round(score_recency * WEIGHT_RECENCY, 1)}
            },
            "recommendations": recommendations
        })

    # Sort descending by risk score
    modules_predictions = sorted(modules_predictions, key=lambda x: x["risk_score"], reverse=True)
    return modules_predictions

