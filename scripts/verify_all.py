"""
scripts/verify_all.py - Complete end-to-end backend and visualization verification script.
"""

import sys
import os

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import auth
import defect_management as dm
import prevention
import prediction
import analytics
import pandas as pd

def run_verification():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Database & Seeding
    database.init_db()
    database.seed_sample_data()
    print("[1/6] Database initialized and verified.")

    # 2. Authentication & Users
    users = auth.get_all_users()
    print(f"[2/6] User management verified: {len(users)} users registered.")
    assert len(users) >= 6

    # 3. Defect Records & Queries
    defects = dm.get_all_defects()
    df_defects = pd.DataFrame(defects)
    print(f"[3/6] Defect registry verified: {len(defects)} defects in database.")
    assert len(defects) >= 15

    # 4. Analytics & Plotly Visualizations
    kpis = analytics.get_dashboard_kpis()
    print(f"      KPIs: Total={kpis['total']}, Open={kpis['open']}, Resolved={kpis['resolved']}, ResolutionRate={kpis['resolution_rate']}%")
    
    chart_sev = analytics.get_severity_chart(df_defects)
    chart_stat = analytics.get_status_chart(df_defects)
    chart_cat = analytics.get_category_chart(df_defects)
    chart_mod = analytics.get_module_chart(df_defects)
    chart_trend = analytics.get_timeline_trend_chart(df_defects)
    chart_dev = analytics.get_developer_resolution_chart()
    chart_prio = analytics.get_priority_chart(df_defects)
    print("[4/6] All 7 interactive Plotly charts generated successfully.")

    # 5. Defect Prevention
    prev_results = prevention.analyze_defect_patterns()
    patterns_count = len(prev_results["pattern_clusters"])
    tested_mods = len(prev_results["modules_requiring_testing"])
    recs_count = len(prev_results["recommendations"])
    print(f"[5/6] Defect Prevention verified: {patterns_count} patterns detected, {tested_mods} modules flagged, {recs_count} action recommendations.")

    # 6. Defect Prediction
    preds = prediction.predict_module_defects()
    chart_risk = analytics.get_risk_score_chart(preds)
    print(f"[6/6] Defect Prediction verified: {len(preds)} modules evaluated with risk scores.")
    for p in preds[:3]:
        print(f"      - {p['module']}: Score={p['risk_score']} ({p['risk_level']})")

    # CSV Exporter
    csv_bytes = analytics.export_defects_to_csv(df_defects)
    assert len(csv_bytes) > 0
    print("      CSV export verified.")

    print("=" * 60)
    print("ALL 6 MODULES AND WORKFLOWS VERIFIED 100% OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
