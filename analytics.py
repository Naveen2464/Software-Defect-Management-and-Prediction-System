"""
analytics.py - Analytics and visualization engine using Plotly and Pandas.
Generates KPI metrics, interactive charts, and exportable reports.
"""

from typing import Dict, Any, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_connection


SEVERITY_COLORS = {
    "Critical": "#dc3545",
    "High": "#fd7e14",
    "Medium": "#ffc107",
    "Low": "#28a745"
}

STATUS_COLORS = {
    "NEW": "#6c757d",
    "ASSIGNED": "#17a2b8",
    "IN PROGRESS": "#0d6efd",
    "FIXED": "#20c997",
    "RETESTING": "#6f42c1",
    "REOPENED": "#d63384",
    "CLOSED": "#198754"
}

PRIORITY_COLORS = {
    "P1 - Urgent": "#dc3545",
    "P2 - High": "#fd7e14",
    "P3 - Normal": "#0d6efd",
    "P4 - Low": "#20c997"
}


def get_dashboard_kpis(user_id: Any = None, role: str = "Admin", db_path: str = None) -> Dict[str, Any]:
    """Calculate core KPI metrics directly from SQLite database with role-based personalization."""
    conn = get_connection(db_path)
    if role == "Developer" and user_id is not None:
        df = pd.read_sql_query("SELECT id, status, severity FROM defects WHERE assigned_to_id = ?", conn, params=(user_id,))
        df_history = pd.read_sql_query("""
            SELECT COUNT(DISTINCT h.defect_id) as reopened_count 
            FROM defect_history h 
            JOIN defects d ON h.defect_id = d.id 
            WHERE h.new_status = 'REOPENED' AND d.assigned_to_id = ?
        """, conn, params=(user_id,))
    else:
        df = pd.read_sql_query("SELECT id, status, severity FROM defects", conn)
        df_history = pd.read_sql_query("SELECT COUNT(DISTINCT defect_id) as reopened_count FROM defect_history WHERE new_status = 'REOPENED'", conn)
    conn.close()

    if df.empty:
        return {
            "total": 0,
            "open": 0,
            "resolved": 0,
            "critical": 0,
            "reopened": 0,
            "resolution_rate": 0.0
        }

    total = len(df)
    open_count = len(df[df["status"].isin(["NEW", "ASSIGNED", "IN PROGRESS", "REOPENED"])])
    resolved_count = len(df[df["status"].isin(["FIXED", "RETESTING", "CLOSED"])])
    critical_count = len(df[df["severity"] == "Critical"])
    
    # Reopened count from historical status changes + current reopened
    reopened_history_count = df_history["reopened_count"].iloc[0] if not df_history.empty else 0
    current_reopened = len(df[df["status"] == "REOPENED"])
    reopened_total = max(int(reopened_history_count), int(current_reopened))

    # Resolution rate = (Closed + Fixed) / Total * 100
    closed_and_fixed = len(df[df["status"].isin(["CLOSED", "FIXED"])])
    resolution_rate = round((closed_and_fixed / total) * 100, 1) if total > 0 else 0.0

    return {
        "total": total,
        "open": open_count,
        "resolved": resolved_count,
        "critical": critical_count,
        "reopened": reopened_total,
        "resolution_rate": resolution_rate
    }


def get_severity_chart(df: pd.DataFrame) -> go.Figure:
    """Generate interactive Donut Chart for Defect Severity distribution."""
    if df.empty or "severity" not in df.columns:
        return go.Figure()

    counts = df["severity"].value_counts().reset_index()
    counts.columns = ["Severity", "Count"]

    fig = px.pie(
        counts,
        names="Severity",
        values="Count",
        hole=0.45,
        color="Severity",
        color_discrete_map=SEVERITY_COLORS,
        title="Defects by Severity"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    return fig


def get_status_chart(df: pd.DataFrame) -> go.Figure:
    """Generate interactive Donut Chart for Defect Status distribution."""
    if df.empty or "status" not in df.columns:
        return go.Figure()

    counts = df["status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    fig = px.pie(
        counts,
        names="Status",
        values="Count",
        hole=0.45,
        color="Status",
        color_discrete_map=STATUS_COLORS,
        title="Defects by Lifecycle Status"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    return fig


def get_priority_chart(df: pd.DataFrame) -> go.Figure:
    """Generate interactive Bar Chart for Defect Priority distribution."""
    if df.empty or "priority" not in df.columns:
        return go.Figure()

    counts = df["priority"].value_counts().reset_index()
    counts.columns = ["Priority", "Count"]

    fig = px.bar(
        counts,
        x="Priority",
        y="Count",
        color="Priority",
        color_discrete_map=PRIORITY_COLORS,
        text="Count",
        title="Defects by Priority Level"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320, showlegend=False)
    return fig


def get_category_chart(df: pd.DataFrame) -> go.Figure:
    """Generate interactive Bar Chart for Defect Categories / Types."""
    if df.empty or "defect_type" not in df.columns:
        return go.Figure()

    counts = df["defect_type"].value_counts().reset_index()
    counts.columns = ["Defect Type", "Count"]

    fig = px.bar(
        counts,
        x="Defect Type",
        y="Count",
        color="Count",
        color_continuous_scale="Tealgrn",
        text="Count",
        title="Defects by Category / Type"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=340, xaxis_tickangle=-30, coloraxis_showscale=False)
    return fig


def get_module_chart(df: pd.DataFrame) -> go.Figure:
    """Generate interactive Horizontal Bar Chart for Defects per Module."""
    if df.empty or "module" not in df.columns:
        return go.Figure()

    counts = df["module"].value_counts().reset_index()
    counts.columns = ["Module", "Count"]

    fig = px.bar(
        counts.sort_values(by="Count", ascending=True),
        y="Module",
        x="Count",
        orientation='h',
        color="Count",
        color_continuous_scale="Blues",
        text="Count",
        title="Defect Distribution by Software Module"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=340, coloraxis_showscale=False)
    return fig


def get_timeline_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Generate Line Chart showing Monthly Defect Discovery Trend."""
    if df.empty or "created_at" not in df.columns:
        return go.Figure()

    df_copy = df.copy()
    df_copy["created_at"] = pd.to_datetime(df_copy["created_at"])
    df_copy["Month"] = df_copy["created_at"].dt.strftime("%Y-%m")

    monthly = df_copy.groupby("Month").size().reset_index(name="Defects Discovered")

    fig = px.line(
        monthly,
        x="Month",
        y="Defects Discovered",
        markers=True,
        title="Monthly Defect Discovery Trend",
        color_discrete_sequence=["#0d6efd"]
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320)
    return fig


def get_developer_resolution_chart(db_path: str = None) -> go.Figure:
    """Generate Grouped Bar Chart of Developer-wise Resolution."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT u.full_name as developer,
               COUNT(d.id) as total_assigned,
               SUM(CASE WHEN d.status IN ('FIXED', 'CLOSED') THEN 1 ELSE 0 END) as resolved_count,
               SUM(CASE WHEN d.status IN ('NEW', 'ASSIGNED', 'IN PROGRESS', 'REOPENED') THEN 1 ELSE 0 END) as active_count
        FROM users u
        LEFT JOIN defects d ON u.id = d.assigned_to_id
        WHERE u.role = 'Developer'
        GROUP BY u.id, u.full_name
    """, conn)
    conn.close()

    if df.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["developer"],
        y=df["total_assigned"],
        name="Assigned",
        marker_color="#0dcaf0"
    ))
    fig.add_trace(go.Bar(
        x=df["developer"],
        y=df["resolved_count"],
        name="Resolved / Fixed",
        marker_color="#198754"
    ))
    fig.add_trace(go.Bar(
        x=df["developer"],
        y=df["active_count"],
        name="In Progress",
        marker_color="#fd7e14"
    ))

    fig.update_layout(
        barmode='group',
        title="Developer Workload & Resolution Metrics",
        margin=dict(t=40, b=20, l=20, r=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25)
    )
    return fig


def get_risk_score_chart(predictions: List[Dict[str, Any]]) -> go.Figure:
    """Generate Horizontal Bar Chart ranking modules by Risk Score."""
    if not predictions:
        return go.Figure()

    df = pd.DataFrame(predictions)
    # Sort ascending for display
    df = df.sort_values(by="risk_score", ascending=True)

    fig = px.bar(
        df,
        y="module",
        x="risk_score",
        orientation='h',
        color="risk_level",
        color_discrete_map={
            "Critical Risk": "#dc3545",
            "High Risk": "#fd7e14",
            "Medium Risk": "#ffc107",
            "Low Risk": "#28a745"
        },
        text="risk_score",
        title="Software Module Defect Risk Score (0-100)"
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=340, xaxis=dict(range=[0, 105]))
    return fig


def export_defects_to_csv(df: pd.DataFrame) -> bytes:
    """Export filtered defects dataframe to UTF-8 CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')

