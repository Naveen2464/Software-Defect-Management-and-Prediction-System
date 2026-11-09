"""
app.py - Main Streamlit Application for Software Defect Management and Prediction System.
Complete, functional, and ready-to-submit academic software testing project.
"""

import os
import html
from PIL import Image
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Initialize and import modules
import database
import auth
import defect_management as dm
import prevention
import prediction
import analytics

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Software Defect Management & Prediction System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on startup
database.init_db()
database.seed_sample_data()

# Inject Custom CSS
css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Session State Management ---
if "user" not in st.session_state:
    st.session_state["user"] = None

def render_login_page():
    """Render a dedicated, professional full-page login screen."""
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
        <div style="text-align: center; margin-top: 25px; margin-bottom: 20px;">
            <div style="font-size: 3.2rem;">🛡️</div>
            <h1 style="font-size: 1.85rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;">
                Software Defect Management & Prediction System
            </h1>
            <p style="font-size: 0.95rem; color: #64748b;">
                Enterprise Quality Engineering, Defect Lifecycle Governance & Explainable Risk Forecasting
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 User Login")
        st.caption("Sign in with your role-based credentials. User accounts are provisioned by the Administrator.")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. admin, tester, or dev1")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_login = st.form_submit_button("Sign In", use_container_width=True)

            if submit_login:
                user = auth.verify_user(username, password)
                if user:
                    st.session_state["user"] = user
                    st.success(f"Login successful! Welcome, {user['full_name']}.")
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid username or password.")

        st.markdown("---")
        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #475569; margin-bottom: 8px;'>⚡ 1-Click Demo Login (For Evaluation / Presentation):</p>", unsafe_allow_html=True)

        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            if st.button("👑 Admin", use_container_width=True, help="Login as Sarah Jenkins (Admin)"):
                st.session_state["user"] = auth.get_user_by_username("admin")
                st.rerun()
        with qc2:
            if st.button("🧪 Tester", use_container_width=True, help="Login as Alex Rivera (Lead QA)"):
                st.session_state["user"] = auth.get_user_by_username("tester")
                st.rerun()
        with qc3:
            if st.button("👨‍💻 Developer", use_container_width=True, help="Login as David Kim (Developer)"):
                st.session_state["user"] = auth.get_user_by_username("dev1")
                st.rerun()

        st.markdown("""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 15px; font-size: 0.8rem; color: #64748b;">
            <b>Default Pre-seeded Credentials:</b><br>
            • <b>Admin:</b> <code>admin</code> / <code>admin123</code> (Full system oversight, assignment & user provisioning)<br>
            • <b>Tester:</b> <code>tester</code> / <code>tester123</code> (Defect discovery, retesting & closing)<br>
            • <b>Developer:</b> <code>dev1</code> / <code>dev123</code> (Defect resolution & fix documentation)<br>
            <div style="margin-top: 6px; color: #2563eb; font-weight: 500;">
                ℹ️ Note: Only Administrator accounts can create and provision new users (Page 10).
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get("user") is None:
    render_login_page()
    st.stop()

current_user = st.session_state["user"]

# --- Helper Badges ---
def get_severity_badge(sev: str) -> str:
    css_class = f"badge-{sev.lower()}"
    return f'<span class="badge {css_class}">{sev}</span>'

def get_status_badge(status: str) -> str:
    clean = status.lower().replace(" ", "")
    return f'<span class="badge badge-{clean}">{status}</span>'

def get_risk_badge(level: str, score: float) -> str:
    color = prediction.get_risk_badge_color(level)
    return f'<span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.8rem;">{level} ({score})</span>'


# ==========================================
# SIDEBAR NAVIGATION & DEMO ROLE SWITCHER
# ==========================================
with st.sidebar:
    st.markdown("## 🛡️ DefectHub")
    st.markdown("<p style='font-size: 0.82rem; color: #64748b; margin-top: -12px;'>Defect Management & Prediction System</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Current User Profile Card
    role_config = auth.ROLE_BADGE_CONFIG.get(current_user["role"], {
        "label": current_user["role"],
        "class": "role-badge-admin"
    })
    avatar_emoji = "👑" if current_user["role"] == "Admin" else ("🧪" if current_user["role"] == "Tester" else "👨‍💻")

    st.markdown(f"""
    <div class="sidebar-profile-card">
        <div class="sidebar-profile-header">
            <div class="sidebar-avatar">{avatar_emoji}</div>
            <div class="sidebar-user-info">
                <div class="sidebar-fullname">{html.escape(current_user['full_name'])}</div>
                <div class="sidebar-username">@{html.escape(current_user['username'])}</div>
                <span class="{role_config['class']}">{role_config['label']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out", use_container_width=True, help="Log out and return to the login screen"):
        st.session_state["user"] = None
        st.session_state["selected_page"] = "Dashboard"
        st.rerun()

    # Quick Role Switcher for Academic Evaluation
    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
    with st.expander("🔄 Quick Switch Demo Role", expanded=False):
        demo_usernames = auth.DEMO_ACCOUNTS
        demo_users = [auth.get_user_by_username(u) for u in demo_usernames]
        demo_users = [u for u in demo_users if u]
        
        options_map = {
            f"{u['username']} ({u['role']} - {u['full_name'].split()[0]})": u
            for u in demo_users
        }
        
        curr_key = next((k for k, v in options_map.items() if v["id"] == current_user["id"]), list(options_map.keys())[0])
        selected_user_str = st.selectbox(
            "Switch Active Role / User:",
            list(options_map.keys()),
            index=list(options_map.keys()).index(curr_key) if curr_key in options_map else 0
        )
        if st.button("Apply Switch", use_container_width=True):
            switched = options_map[selected_user_str]
            # 1. Update the active authenticated user
            st.session_state["user"] = switched
            
            # 7. Reset navigation to an accessible page
            allowed_for_switched = auth.get_allowed_pages(switched)
            if st.session_state.get("selected_page") not in allowed_for_switched:
                st.session_state["selected_page"] = "Dashboard"
                
            st.success(f"Identity updated to {switched['full_name']} ({switched['role']})")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📌 Navigation")

    # Display ONLY navigation options permitted for current role
    allowed_pages = auth.get_allowed_pages(current_user)
    display_options = [f"{auth.PAGE_ICONS.get(p, '📌')} {p}" for p in allowed_pages]

    # Ensure current selected page is valid for current role
    curr_selected = st.session_state.get("selected_page", "Dashboard")
    if curr_selected not in allowed_pages:
        curr_selected = allowed_pages[0] if allowed_pages else "Dashboard"
        st.session_state["selected_page"] = curr_selected

    # Find index in current role's allowed pages
    default_idx = 0
    for idx, p in enumerate(allowed_pages):
        if p == curr_selected:
            default_idx = idx
            break

    selected_display = st.radio(
        "Role Navigation Menu",
        display_options,
        index=default_idx,
        label_visibility="collapsed"
    )
    # Extract clean page name (without icon)
    selected_page = selected_display.split(" ", 1)[1] if " " in selected_display else selected_display
    st.session_state["selected_page"] = selected_page

    st.markdown("---")
    # Quick DB actions
    with st.expander("⚙️ System / DB Options", expanded=False):
        if st.button("Reload Sample Data", help="Resets and re-populates realistic academic sample defects."):
            database.seed_sample_data(force=True)
            st.success("Sample data reset successfully!")
            st.rerun()
        st.caption("SQLite DB: `database/defects.db`")

# Centralized Page Authorization Guard
if not auth.can_view_page(current_user, selected_page):
    st.error(f"⛔ Access Denied: Your active role '{current_user['role']}' does not have permission to view '{selected_page}'.")
    st.info("Please use the navigation menu on the left to access permitted sections.")
    st.stop()


# ==========================================
# PAGE 1: MAIN DASHBOARD
# ==========================================
if selected_page == "Dashboard":
    is_dev = current_user["role"] == "Developer"
    is_tester = current_user["role"] == "Tester"

    if is_dev:
        st.title("👨‍💻 Developer Workload Dashboard")
        st.markdown(f"Personal defect workload, assigned resolution progress, and code fix metrics for **{current_user['full_name']}**.")
    elif is_tester:
        st.title("🧪 QA Testing Quality Dashboard")
        st.markdown(f"Defect discovery statistics, verification backlog, and staging defect trends for **{current_user['full_name']}**.")
    else:
        st.title("📊 Executive Defect Management Dashboard")
        st.markdown("Real-time software defect intelligence, team throughput, lifecycle tracking, and risk analysis.")

    # Calculate personalized or global KPIs
    kpis = analytics.get_dashboard_kpis(
        user_id=current_user["id"] if is_dev else None,
        role=current_user["role"]
    )
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    sub_tot = "Assigned to you" if is_dev else "Logged in database"
    sub_open = "Your active backlog" if is_dev else "Active backlog"
    sub_res = "Fixed / resolved by you" if is_dev else "Fixed & Closed"
    sub_crit = "Critical assigned to you" if is_dev else "Urgent blockers"
    sub_reop = "Reopened on you" if is_dev else "Failed retesting"
    sub_rate = "Your resolution rate" if is_dev else "Closed vs Total"

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Defects</div>
            <div class="kpi-value">{kpis['total']}</div>
            <div class="kpi-sub">{sub_tot}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Open Defects</div>
            <div class="kpi-value" style="color: #0d6efd;">{kpis['open']}</div>
            <div class="kpi-sub">{sub_open}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Resolved</div>
            <div class="kpi-value" style="color: #198754;">{kpis['resolved']}</div>
            <div class="kpi-sub">{sub_res}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Critical Defects</div>
            <div class="kpi-value" style="color: #dc3545;">{kpis['critical']}</div>
            <div class="kpi-sub">{sub_crit}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Reopened</div>
            <div class="kpi-value" style="color: #d63384;">{kpis['reopened']}</div>
            <div class="kpi-sub">{sub_reop}</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Resolution Rate</div>
            <div class="kpi-value" style="color: #0dcaf0;">{kpis['resolution_rate']}%</div>
            <div class="kpi-sub">{sub_rate}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # Load Defects DataFrame
    all_defects = dm.get_all_defects()
    df_all = pd.DataFrame(all_defects)

    if is_dev:
        df_dev = df_all[df_all["assigned_to_id"] == current_user["id"]] if not df_all.empty else df_all
        row1_c1, row1_c2 = st.columns(2)
        with row1_c1:
            st.plotly_chart(analytics.get_severity_chart(df_dev), use_container_width=True)
        with row1_c2:
            st.plotly_chart(analytics.get_status_chart(df_dev), use_container_width=True)

        row2_c1, row2_c2 = st.columns(2)
        with row2_c1:
            st.plotly_chart(analytics.get_category_chart(df_dev), use_container_width=True)
        with row2_c2:
            st.plotly_chart(analytics.get_module_chart(df_dev), use_container_width=True)

        # High-Risk Modules Chart
        st.markdown("### ⚠️ Predicted High-Risk Software Modules")
        preds = prediction.predict_module_defects()
        st.plotly_chart(analytics.get_risk_score_chart(preds), use_container_width=True)

        # Developer's Assigned Defects Feed
        st.markdown("### 📋 Your Assigned Defects")
        if not df_dev.empty:
            display_cols = ["defect_code", "title", "module", "severity", "priority", "status", "created_at"]
            df_recent = df_dev[display_cols].head(6)
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
        else:
            st.info("No active defects currently assigned to you.")
    else:
        # Charts Row 1: Severity and Status
        row1_c1, row1_c2 = st.columns(2)
        with row1_c1:
            st.plotly_chart(analytics.get_severity_chart(df_all), use_container_width=True)
        with row1_c2:
            st.plotly_chart(analytics.get_status_chart(df_all), use_container_width=True)

        # Charts Row 2: Category and Module
        row2_c1, row2_c2 = st.columns(2)
        with row2_c1:
            st.plotly_chart(analytics.get_category_chart(df_all), use_container_width=True)
        with row2_c2:
            st.plotly_chart(analytics.get_module_chart(df_all), use_container_width=True)

        # Charts Row 3: Trends & Developer Resolution
        row3_c1, row3_c2 = st.columns(2)
        with row3_c1:
            st.plotly_chart(analytics.get_timeline_trend_chart(df_all), use_container_width=True)
        with row3_c2:
            st.plotly_chart(analytics.get_developer_resolution_chart(), use_container_width=True)

        # High-Risk Modules Chart
        st.markdown("### ⚠️ Predicted High-Risk Software Modules")
        preds = prediction.predict_module_defects()
        st.plotly_chart(analytics.get_risk_score_chart(preds), use_container_width=True)

        # Recent Defects Feed
        st.markdown("### 📋 Recent Defect Activity")
        if not df_all.empty:
            display_cols = ["defect_code", "title", "module", "severity", "priority", "status", "assignee_name", "created_at"]
            df_recent = df_all[display_cols].head(6)
            st.dataframe(df_recent, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 2: REPORT NEW DEFECT (DEFECT DISCOVERY)
# ==========================================
elif selected_page == "Report New Defect":
    if not auth.can_report_defects(current_user):
        st.error("⛔ Access Denied: Only QA Testers and Administrators are authorized to report new defects.")
        st.stop()

    st.title("🐞 Defect Discovery: Report New Defect")
    st.markdown("Capture and register defect details with validation, classification, and screenshot attachment.")

    projects = dm.get_unique_projects()
    modules = dm.get_unique_modules()

    with st.form("new_defect_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.selectbox("Project Name *", projects)
            title = st.text_input("Defect Title *", placeholder="e.g. Memory leak during concurrent report generation")
            module = st.selectbox("Software Module *", modules)
            defect_type = st.selectbox("Defect Type *", dm.VALID_DEFECT_TYPES)
            environment = st.selectbox("Test Environment *", dm.VALID_ENVIRONMENTS)

        with c2:
            severity = st.selectbox("Severity *", dm.VALID_SEVERITIES, index=1)
            priority = st.selectbox("Priority *", dm.VALID_PRIORITIES, index=1)
            reporter_display = f"{current_user['full_name']} ({current_user['role']})"
            st.text_input("Reporter Name", value=reporter_display, disabled=True)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.text_input("Reporting Date & Time", value=current_time, disabled=True)

        st.markdown("#### Defect Details & Reproduction Steps")
        description = st.text_area("Defect Description *", placeholder="Detailed explanation of the failure behavior...")
        steps = st.text_area("Steps to Reproduce", placeholder="1. Navigate to...\n2. Enter value...\n3. Click Submit...")

        col_exp, col_act = st.columns(2)
        with col_exp:
            expected = st.text_area("Expected Result", placeholder="System should validate input and return 200 OK...")
        with col_act:
            actual = st.text_area("Actual Result", placeholder="System crashed with 500 Internal Server Error...")

        # Screenshot Upload
        st.markdown("#### Attachment")
        uploaded_file = st.file_uploader("Upload Defect Screenshot / Log (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

        # Optional initial assignment for Admins
        assigned_to_id = None
        if auth.can_assign_defects(current_user):
            devs = auth.get_all_users(role="Developer")
            dev_options = ["-- Unassigned (NEW) --"] + [f"{d['id']}: {d['full_name']}" for d in devs]
            chosen_dev = st.selectbox("Assign to Developer (Optional for Admin)", dev_options)
            if chosen_dev != "-- Unassigned (NEW) --":
                assigned_to_id = int(chosen_dev.split(":")[0])

        submitted = st.form_submit_button("🚀 Submit Defect", use_container_width=True)

        if submitted:
            if not title or not title.strip():
                st.error("Validation Error: Defect Title is required.")
            elif not description or not description.strip():
                st.error("Validation Error: Defect Description is required.")
            else:
                screenshot_path = None
                upload_error = False
                if uploaded_file is not None:
                    try:
                        img = Image.open(uploaded_file)
                        img.verify()
                        uploaded_file.seek(0)

                        os.makedirs("uploads", exist_ok=True)
                        safe_base = os.path.basename(uploaded_file.name).replace(" ", "_")
                        clean_name = f"{int(datetime.now().timestamp())}_{safe_base}"
                        screenshot_path = os.path.join("uploads", clean_name)
                        with open(screenshot_path, "wb") as f_out:
                            f_out.write(uploaded_file.getbuffer())
                    except Exception as img_err:
                        st.error(f"Upload Error: Invalid image file ({str(img_err)}). Please upload a valid PNG, JPG, or JPEG image.")
                        upload_error = True

                if not upload_error:
                    try:
                        defect_id, defect_code = dm.create_defect(
                            project_name=project_name,
                            module=module,
                            title=title,
                            description=description,
                            steps_to_reproduce=steps,
                            expected_result=expected,
                            actual_result=actual,
                            defect_type=defect_type,
                            severity=severity,
                            priority=priority,
                            environment=environment,
                            reporter_id=current_user["id"],
                            reporter_role=current_user["role"],
                            screenshot_path=screenshot_path,
                            assigned_to_id=assigned_to_id
                        )
                        st.success(f"✅ Defect successfully submitted and registered with ID: **{defect_code}**!")
                        st.balloons()
                        
                        esc_code = html.escape(defect_code)
                        esc_title = html.escape(title)
                        esc_mod = html.escape(module)
                        esc_sev = html.escape(severity)
                        st.markdown(f"""
                        <div class="success-box">
                            <b>Defect Recorded:</b> {esc_code} - {esc_title}<br>
                            <b>Status:</b> {'ASSIGNED' if assigned_to_id else 'NEW'} | <b>Module:</b> {esc_mod} | <b>Severity:</b> {esc_sev}
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error saving defect to database: {str(e)}")


# ==========================================
# PAGE 3: ALL DEFECTS (RECORDING & REPORTING)
# ==========================================
elif selected_page == "All Defects":
    st.title("🗂️ Defect Records & Inventory")
    st.markdown("Comprehensive defect registry with multi-criteria filtering, search, and CSV export.")

    dev_scope_id = current_user["id"] if current_user["role"] == "Developer" else None
    if current_user["role"] == "Developer":
        st.info(f"👨‍💻 **Developer Scope:** Displaying defects assigned to you (**{current_user['full_name']}**).")

    # Filter Bar
    with st.expander("🔍 Search and Filter Options", expanded=True):
        fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
        with fcol1:
            f_search = st.text_input("Search (ID, Title, Module)", placeholder="e.g. BUG-0001 or login")
        with fcol2:
            projects = ["All"] + dm.get_unique_projects()
            f_project = st.selectbox("Filter Project", projects)
        with fcol3:
            modules = ["All"] + dm.get_unique_modules()
            f_module = st.selectbox("Filter Module", modules)
        with fcol4:
            severities = ["All"] + dm.VALID_SEVERITIES
            f_severity = st.selectbox("Filter Severity", severities)
        with fcol5:
            statuses = ["All", "NEW", "ASSIGNED", "IN PROGRESS", "FIXED", "RETESTING", "REOPENED", "CLOSED"]
            f_status = st.selectbox("Filter Status", statuses)

    defects_list = dm.get_all_defects(
        project_name=f_project,
        module=f_module,
        severity=f_severity,
        status=f_status,
        search_query=f_search,
        assigned_to_id=dev_scope_id
    )
    df_defects = pd.DataFrame(defects_list)

    st.markdown(f"**Found {len(df_defects)} defect record(s) matching criteria.**")

    # CSV Export Button
    if not df_defects.empty:
        csv_bytes = analytics.export_defects_to_csv(df_defects)
        st.download_button(
            label="📥 Export Defect Records (CSV)",
            data=csv_bytes,
            file_name=f"defects_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # Main Table Display
        display_df = df_defects[[
            "defect_code", "title", "module", "severity", "priority",
            "defect_type", "status", "assignee_name", "reporter_name", "created_at"
        ]].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Defect Details Inspector
        st.markdown("---")
        st.markdown("### 🔎 Defect Detail Inspector")
        chosen_code = st.selectbox("Select Defect to Inspect Details & Audit Trail:", df_defects["defect_code"].tolist())
        selected_defect = dm.get_defect_by_code(chosen_code)

        if selected_defect:
            d_c1, d_c2 = st.columns([2, 1])
            with d_c1:
                st.markdown(f"### {selected_defect['defect_code']}: {selected_defect['title']}")
                st.markdown(f"**Description:** {selected_defect['description']}")
                if selected_defect['steps_to_reproduce']:
                    st.markdown(f"**Steps to Reproduce:**\n```\n{selected_defect['steps_to_reproduce']}\n```")
                
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.markdown(f"**Expected Result:** {selected_defect['expected_result'] or 'N/A'}")
                with res_col2:
                    st.markdown(f"**Actual Result:** {selected_defect['actual_result'] or 'N/A'}")

                if selected_defect['resolution_notes']:
                    esc_res_notes = html.escape(selected_defect['resolution_notes'])
                    st.markdown(f"""
                    <div class="info-box">
                        <b>Resolution Notes:</b><br>{esc_res_notes}
                    </div>
                    """, unsafe_allow_html=True)

                if selected_defect['screenshot_path'] and os.path.exists(selected_defect['screenshot_path']):
                    st.markdown("**Screenshot Attachment:**")
                    st.image(selected_defect['screenshot_path'], caption=f"Screenshot for {selected_defect['defect_code']}", width=450)

            with d_c2:
                st.markdown("#### Metadata")
                st.markdown(f"**Project:** {selected_defect['project_name']}")
                st.markdown(f"**Module:** {selected_defect['module']}")
                st.markdown(f"**Severity:** {get_severity_badge(selected_defect['severity'])}", unsafe_allow_html=True)
                st.markdown(f"**Priority:** {selected_defect['priority']}")
                st.markdown(f"**Status:** {get_status_badge(selected_defect['status'])}", unsafe_allow_html=True)
                st.markdown(f"**Type:** {selected_defect['defect_type']}")
                st.markdown(f"**Environment:** {selected_defect['environment']}")
                st.markdown(f"**Reporter:** {selected_defect['reporter_name'] or 'N/A'}")
                st.markdown(f"**Assignee:** {selected_defect['assignee_name'] or 'Unassigned'}")
                st.markdown(f"**Created:** {selected_defect['created_at']}")
                st.markdown(f"**Last Updated:** {selected_defect['updated_at']}")

            # Defect History Audit Trail
            st.markdown("#### 📜 Defect History Audit Trail")
            history_records = dm.get_defect_history(selected_defect["id"])
            if history_records:
                for h in history_records:
                    esc_comm = html.escape(h['comments'] or '')
                    esc_name = html.escape(h['changed_by_name'] or 'Unknown')
                    st.markdown(f"""
                    <div class="timeline-item">
                        <b>{h['timestamp']}</b> &mdash; 
                        <span style="color: #64748b;">{h['previous_status']}</span> ➔ 
                        <b>{h['new_status']}</b> by <b>{esc_name}</b> ({h['changed_by_role']})<br>
                        <span style="font-size: 0.88rem; color: #334155;">{esc_comm}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No history records available.")
    else:
        st.info("No defects match your current filter parameters.")


# ==========================================
# PAGE 4: DEFECT CLASSIFICATION
# ==========================================
elif selected_page == "Defect Classification":
    st.title("🏷️ Defect Classification & Taxonomy")
    st.markdown("Multi-dimensional defect taxonomy: Severity, Priority, and Technical Defect Type with analytics.")

    # Academic Classification Concepts Callout
    st.markdown("""
    <div class="info-box">
        <b>Academic Classification Taxonomy:</b><br>
        • <b>Severity:</b> Degree of operational impact on the software product (Critical, High, Medium, Low).<br>
        • <b>Priority:</b> Urgency of fixing the defect from a business and project schedule perspective (P1 - Urgent to P4 - Low).<br>
        • <b>Defect Type:</b> Technical failure root taxonomy (Functional, Performance, Security, UI/UX, Compatibility, Database, Integration).
    </div>
    """, unsafe_allow_html=True)

    all_defects = dm.get_all_defects()
    df_all = pd.DataFrame(all_defects)

    if not df_all.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.plotly_chart(analytics.get_severity_chart(df_all), use_container_width=True)
        with c2:
            st.plotly_chart(analytics.get_priority_chart(df_all), use_container_width=True)
        with c3:
            st.plotly_chart(analytics.get_category_chart(df_all), use_container_width=True)

        st.markdown("---")
        st.markdown("### ✏️ Defect Reclassification Tool")
        if not auth.can_change_priority_severity(current_user):
            st.info("ℹ️ **Defect Reclassification Restricted:** Changing defect severity, priority, or technical classification is permitted for **QA Testers** and **Administrators**. Developers have read-only visibility into taxonomy metrics.")
        else:
            st.caption("Authorized users (Admin, Tester) can adjust defect classification parameters with mandatory audit notes.")

            col_sel, col_form = st.columns([1, 2])
            with col_sel:
                defect_options = [f"{d['defect_code']}: {d['title'][:35]}..." for d in all_defects]
                selected_def_str = st.selectbox("Select Defect to Classify:", defect_options)
                chosen_code = selected_def_str.split(":")[0]
                target_defect = dm.get_defect_by_code(chosen_code)

            with col_form:
                if target_defect:
                    st.markdown(f"#### Updating: {target_defect['defect_code']}")
                    st.markdown(f"**Current:** {get_severity_badge(target_defect['severity'])} | **Priority:** {target_defect['priority']} | **Type:** {target_defect['defect_type']}", unsafe_allow_html=True)
                    
                    with st.form("reclassification_form"):
                        rc1, rc2, rc3 = st.columns(3)
                        with rc1:
                            new_sev = st.selectbox("New Severity", dm.VALID_SEVERITIES, index=dm.VALID_SEVERITIES.index(target_defect["severity"]))
                        with rc2:
                            new_prio = st.selectbox("New Priority", dm.VALID_PRIORITIES, index=dm.VALID_PRIORITIES.index(target_defect["priority"]))
                        with rc3:
                            new_type = st.selectbox("New Defect Type", dm.VALID_DEFECT_TYPES, index=dm.VALID_DEFECT_TYPES.index(target_defect["defect_type"]))

                        audit_comment = st.text_input("Reclassification Rationale *", placeholder="e.g. Escalated due to discovery of critical auth bypass...")
                        apply_btn = st.form_submit_button("💾 Save Classification Updates")

                        if apply_btn:
                            if not auth.can_change_priority_severity(current_user):
                                st.error("Permission Denied: Only Admins and Testers can reclassify defects.")
                            elif not audit_comment or not audit_comment.strip():
                                st.error("Audit comment is required explaining the reclassification rationale.")
                            else:
                                dm.update_defect_classification(
                                    defect_id=target_defect["id"],
                                    severity=new_sev,
                                    priority=new_prio,
                                    defect_type=new_type,
                                    changed_by_id=current_user["id"],
                                    user_role=current_user["role"],
                                    comments=audit_comment
                                )
                                st.success(f"Successfully reclassified {target_defect['defect_code']}!")
                                st.rerun()


# ==========================================
# PAGE 5: ASSIGN DEFECTS
# ==========================================
elif selected_page == "Assign Defects":
    if not auth.can_assign_defects(current_user):
        st.error("⛔ Access Denied: Defect assignment is restricted to Administrators.")
        st.info("Please use the sidebar 'Quick Switch Demo Role' to switch to Admin to test assignment operations.")
        st.stop()

    st.title("👥 Defect Assignment & Triage")
    st.markdown("Assign reported defects to development team members and balance engineering workload.")

    # Show Developer Workload
    st.markdown("### 📊 Engineering Workload Distribution")
    st.plotly_chart(analytics.get_developer_resolution_chart(), use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 Assign Defect to Developer")

    all_defects = dm.get_all_defects()
    # Prioritize NEW or open defects
    open_defects = [d for d in all_defects if d["status"] in ["NEW", "ASSIGNED", "IN PROGRESS", "REOPENED"]]

    if open_defects:
        assign_c1, assign_c2 = st.columns([1, 1])
        with assign_c1:
            def_labels = [f"{d['defect_code']} [{d['status']}]: {d['title']}" for d in open_defects]
            chosen_def_label = st.selectbox("Select Defect to Assign:", def_labels)
            chosen_code = chosen_def_label.split(" ")[0]
            selected_def = dm.get_defect_by_code(chosen_code)

            if selected_def:
                esc_t_title = html.escape(selected_def['title'])
                esc_t_mod = html.escape(selected_def['module'])
                esc_t_sev = html.escape(selected_def['severity'])
                esc_t_ass = html.escape(selected_def['assignee_name'] or 'None (Unassigned)')
                st.markdown(f"""
                <div class="info-box">
                    <b>Title:</b> {esc_t_title}<br>
                    <b>Module:</b> {esc_t_mod} | <b>Severity:</b> {esc_t_sev}<br>
                    <b>Current Assignee:</b> {esc_t_ass}<br>
                    <b>Current Status:</b> {selected_def['status']}
                </div>
                """, unsafe_allow_html=True)

        with assign_c2:
            developers = auth.get_all_users(role="Developer")
            dev_choices = [f"{dev['id']}: {dev['full_name']} ({dev['email']})" for dev in developers]
            target_dev = st.selectbox("Select Developer:", dev_choices)
            assignment_notes = st.text_area("Assignment Instructions / Notes", placeholder="e.g. Prioritize investigation for the upcoming sprint release...")

            if st.button("📌 Confirm Assignment", use_container_width=True, disabled=not auth.can_assign_defects(current_user)):
                dev_id = int(target_dev.split(":")[0])
                try:
                    dm.assign_defect(
                        defect_id=selected_def["id"],
                        assigned_to_id=dev_id,
                        assigned_by_id=current_user["id"],
                        assigned_by_role=current_user["role"],
                        notes=assignment_notes
                    )
                    st.success(f"Defect {selected_def['defect_code']} assigned to {target_dev}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to assign defect: {str(e)}")
    else:
        st.info("No open defects currently requiring assignment.")


# ==========================================
# PAGE 6: RESOLUTION MANAGEMENT
# ==========================================
elif selected_page == "Resolution Management":
    st.title("🔄 Defect Resolution Lifecycle Management")
    st.markdown("Enforce state machine transitions, resolution documentation, retesting, and closure.")

    # Defect Lifecycle Workflow Diagram
    st.markdown("""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="font-weight: 600; font-size: 0.88rem; color: #475569; margin-bottom: 8px;">DEFECT LIFECYCLE WORKFLOW (STRICT STATE MACHINE):</div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 0.82rem; font-weight: 600;">
            <span class="badge badge-new">NEW</span> ➔ 
            <span class="badge badge-assigned">ASSIGNED</span> ➔ 
            <span class="badge badge-inprogress">IN PROGRESS</span> ➔ 
            <span class="badge badge-fixed">FIXED</span> ➔ 
            <span class="badge badge-retesting">RETESTING</span> ➔ 
            <span class="badge badge-closed">CLOSED</span>
        </div>
        <div style="margin-top: 6px; font-size: 0.8rem; color: #d63384; font-weight: 500;">
            * If retesting fails: <b>RETESTING ➔ REOPENED ➔ IN PROGRESS</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Role Context Guidance
    if current_user["role"] == "Developer":
        st.info(f"👨‍💻 **Developer Mode ({current_user['full_name']}):** You can update assigned defects to **IN PROGRESS** or **FIXED** with resolution notes.")
        filtered_defects = dm.get_all_defects(assigned_to_id=current_user["id"])
    elif current_user["role"] == "Tester":
        st.info(f"🧪 **Tester Mode ({current_user['full_name']}):** You can take **FIXED** defects into **RETESTING**, and then **CLOSE** or **REOPEN** them.")
        filtered_defects = dm.get_all_defects()
    else:
        st.info(f"👑 **Admin Mode ({current_user['full_name']}):** Full oversight over all lifecycle stages and transitions.")
        filtered_defects = dm.get_all_defects()

    if filtered_defects:
        def_options = [f"{d['defect_code']} [{d['status']}]: {d['title']}" for d in filtered_defects]
        sel_defect_label = st.selectbox("Select Defect to Manage Resolution:", def_options)
        chosen_code = sel_defect_label.split(" ")[0]
        cur_defect = dm.get_defect_by_code(chosen_code)

        if cur_defect:
            res_col1, res_col2 = st.columns([1, 1])

            with res_col1:
                st.markdown(f"### {cur_defect['defect_code']}: {cur_defect['title']}")
                st.markdown(f"**Current Status:** {get_status_badge(cur_defect['status'])}", unsafe_allow_html=True)
                st.markdown(f"**Assigned Developer:** {cur_defect['assignee_name'] or 'Unassigned'}")
                st.markdown(f"**Severity:** {get_severity_badge(cur_defect['severity'])} | **Priority:** {cur_defect['priority']}", unsafe_allow_html=True)
                st.markdown(f"**Description:** {cur_defect['description']}")
                if cur_defect['resolution_notes']:
                    st.markdown(f"**Existing Resolution Notes:**\n> {cur_defect['resolution_notes']}")

            with res_col2:
                st.markdown("#### Advance Lifecycle Stage")
                valid_next = dm.get_valid_next_statuses(cur_defect["status"], user_role=current_user["role"])

                if not valid_next:
                    st.warning(f"No further lifecycle transitions available for status **'{cur_defect['status']}'** under role **'{current_user['role']}'**.")
                else:
                    with st.form("advance_status_form"):
                        next_status = st.selectbox("Target Next Status *", valid_next)
                        
                        notes_label = "Resolution Description / Root Cause Analysis *" if next_status == "FIXED" else "Action / Retest Comments *"
                        status_comments = st.text_area(notes_label, placeholder="Explain technical fix, commit SHA, or verification results...")
                        
                        sub_btn = st.form_submit_button("🚀 Update Defect Status")

                        if sub_btn:
                            if not status_comments or not status_comments.strip():
                                st.error("Comments or resolution notes are required for lifecycle transitions.")
                            else:
                                try:
                                    dm.update_defect_status(
                                        defect_id=cur_defect["id"],
                                        new_status=next_status,
                                        changed_by_id=current_user["id"],
                                        comments=status_comments,
                                        resolution_notes=status_comments if next_status == "FIXED" else None,
                                        user_role=current_user["role"]
                                    )
                                    st.success(f"Status successfully updated to **{next_status}**!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Transition Error: {str(e)}")

            # Defect History Timeline
            st.markdown("---")
            st.markdown("#### 📜 Lifecycle Audit History")
            history = dm.get_defect_history(cur_defect["id"])
            for h in history:
                esc_h_comm = html.escape(h['comments'] or '')
                esc_h_name = html.escape(h['changed_by_name'] or 'Unknown')
                st.markdown(f"""
                <div class="timeline-item">
                    <b>{h['timestamp']}</b> &mdash; 
                    <span style="color: #64748b;">{h['previous_status']}</span> ➔ 
                    <b>{h['new_status']}</b> by <b>{esc_h_name}</b> ({h['changed_by_role']})<br>
                    <span style="font-size: 0.88rem; color: #334155;">{esc_h_comm}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No defects found matching your current role scope.")


# ==========================================
# PAGE 7: DEFECT PREVENTION (MODULE 1)
# ==========================================
elif selected_page == "Defect Prevention":
    st.title("🛡️ Defect Prevention & Root Cause Analysis")
    st.markdown("Proactive quality engineering: Identify recurring patterns, repeated failure points, and data-driven preventive measures.")

    analysis = prevention.analyze_defect_patterns()

    # Academic Foundation Callout
    st.markdown("""
    <div class="info-box">
        <b>Academic Concept — Defect Prevention:</b><br>
        Defect Prevention is a systematic approach to identifying the root causes of recurring defects and applying process, 
        design, and automated testing improvements so that similar defects do not recur in subsequent builds or sprints.
        (Ref: Orthogonal Defect Classification / CMMI Level 5 Defect Prevention).
    </div>
    """, unsafe_allow_html=True)

    # Top Metrics
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Defects Examined</div>
            <div class="kpi-value">{analysis['total_defects']}</div>
            <div class="kpi-sub">Total database corpus</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col2:
        patterns_count = len(analysis['pattern_clusters'])
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Failure Patterns Detected</div>
            <div class="kpi-value" style="color: #fd7e14;">{patterns_count}</div>
            <div class="kpi-sub">Recurring defect signatures</div>
        </div>
        """, unsafe_allow_html=True)
    with p_col3:
        high_risk_count = len(analysis['modules_requiring_testing'])
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Modules Requiring Extra Testing</div>
            <div class="kpi-value" style="color: #dc3545;">{high_risk_count}</div>
            <div class="kpi-sub">Flagged for preventive testing</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    # Section 1: Modules with Repeated Defects
    st.markdown("### 🔁 Software Modules with Repeated Defects")
    st.caption("Identified from database records having repeated defects or recurring severe failures.")

    df_mod_summary = pd.DataFrame(analysis["modules_summary"])
    if not df_mod_summary.empty:
        display_mod = df_mod_summary[[
            "module", "total_defects", "critical_high", "open_defects",
            "reopened", "dominant_type", "requires_extra_testing"
        ]].copy()
        display_mod.columns = [
            "Software Module", "Total Defects", "Critical/High", "Open",
            "Reopened", "Dominant Defect Type", "Requires Preventive Action"
        ]
        st.dataframe(display_mod, use_container_width=True, hide_index=True)

    # Section 2: Detected Recurring Defect Patterns
    st.markdown("### 🧩 Detected Defect Patterns & Signatures")
    st.caption("Extracted via natural language pattern matching on defect titles, descriptions, and taxonomy.")

    for pat in analysis["pattern_clusters"]:
        with st.expander(f"⚠️ {pat['pattern_name']} ({pat['frequency']} occurrences) &mdash; {pat['category']}", expanded=True):
            st.markdown(f"**Preventive Recommendation:**\n> {pat['prevention_guideline']}")
            st.markdown("**Matched Defect Records:**")
            for d_name in pat["matched_defects"]:
                st.markdown(f"- `{d_name}`")

    # Section 3: High-Risk Modules Requiring Extra Testing
    st.markdown("### 🎯 Modules Requiring Additional Preventive Testing")
    for mod in analysis["modules_requiring_testing"]:
        st.markdown(f"""
        <div class="warning-box">
            <b>Module:</b> {mod['module']} ({mod['defects_count']} defects, {mod['critical_high']} Critical/High)<br>
            <b>Risk Driver:</b> {mod['risk_reason']}<br>
            <b>Mandatory Preventive Test Suites:</b>
            <ul>
                {''.join(f'<li>{t}</li>' for t in mod['recommended_test_suites'])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Section 4: Prevention Recommendations Action Plan
    st.markdown("### 📋 Automated Defect Prevention Action Plan")
    for rec in analysis["recommendations"]:
        st.markdown(f"#### 📌 {rec['focus_area']} [{rec['severity']}]")
        st.markdown(f"*{rec['observation']}*")
        for item in rec["action_items"]:
            st.markdown(f"- [ ] {item}")

    # Export Action Plan
    action_plan_text = f"# SOFTWARE DEFECT PREVENTION ACTION PLAN\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    for rec in analysis["recommendations"]:
        action_plan_text += f"## {rec['focus_area']} [{rec['severity']}]\n{rec['observation']}\n"
        for item in rec["action_items"]:
            action_plan_text += f"- [ ] {item}\n"
        action_plan_text += "\n"

    st.download_button(
        "📥 Download Defect Prevention Plan (.md)",
        data=action_plan_text.encode('utf-8'),
        file_name="defect_prevention_action_plan.md",
        mime="text/markdown"
    )


# ==========================================
# PAGE 8: DEFECT PREDICTION (MODULE 6)
# ==========================================
elif selected_page == "Defect Prediction":
    st.title("🔮 Defect Prediction: Explainable Risk Scoring")
    st.markdown("Multi-factor software defect risk prediction algorithm based on historical SQLite defect metrics.")

    # Academic Transparency Notice
    st.markdown("""
    <div class="info-box">
        <b>Methodology & Academic Transparency:</b><br>
        This module implements an <b>explainable, rule-based defect risk scoring algorithm</b> derived from historical software repository metrics.
        In compliance with academic rigor, this model does <b>not</b> claim to be an opaque neural network. Instead, it provides a transparent, 
        empirically weighted formula combining 5 critical defect metrics to compute a Risk Score between 0 and 100.
    </div>
    """, unsafe_allow_html=True)

    # Algorithm Weights Explainer
    with st.expander("📐 Mathematical Risk Formulation & Weights", expanded=False):
        st.latex(r"R_m = \min\left(100, \; 0.25 \cdot S_{\text{volume}} + 0.30 \cdot S_{\text{severity}} + 0.20 \cdot S_{\text{unresolved}} + 0.15 \cdot S_{\text{reopen}} + 0.10 \cdot S_{\text{recency}}\right)")
        st.markdown("""
        - **Defect Volume ($S_{volume}$, 25%):** Normalized volume of total historical defects logged for this module.
        - **Severity Impact ($S_{severity}$, 30%):** Weighted severity score (Critical = 4.0, High = 2.5, Medium = 1.0, Low = 0.25).
        - **Unresolved Technical Debt ($S_{unresolved}$, 20%):** Proportion and count of defects currently remaining in open states.
        - **Code Fragility / Reopens ($S_{reopen}$, 15%):** Penalizes defects that failed QA retesting (reopened bugs).
        - **Recency Velocity ($S_{recency}$, 10%):** Velocity of defects reported in the last 30 days.
        """)

    predictions = prediction.predict_module_defects()

    # Risk Chart
    st.plotly_chart(analytics.get_risk_score_chart(predictions), use_container_width=True)

    # Predictions Table
    st.markdown("### 📊 Module Defect Risk Table")
    table_rows = []
    for p in predictions:
        table_rows.append({
            "Software Module": p["module"],
            "Total Defects": p["total_defects"],
            "Critical Defects": p["critical_defects"],
            "High Defects": p["high_defects"],
            "Unresolved": p["unresolved_defects"],
            "Reopened": p["reopened_defects"],
            "Risk Score (0-100)": p["risk_score"],
            "Risk Level": p["risk_level"]
        })
    df_pred_table = pd.DataFrame(table_rows)
    st.dataframe(df_pred_table, use_container_width=True, hide_index=True)

    st.markdown("---")
    # Explainability: Deep Dive into Factors
    st.markdown("### 🔍 Explainable Factor Breakdown per Module")
    selected_mod_name = st.selectbox("Select Module to inspect contributing factors:", [p["module"] for p in predictions])
    mod_data = next((p for p in predictions if p["module"] == selected_mod_name), None)

    if mod_data:
        m_col1, m_col2 = st.columns([1, 1])
        with m_col1:
            st.markdown(f"#### Risk Assessment for `{mod_data['module']}`")
            st.markdown(f"**Composite Risk Score:** {get_risk_badge(mod_data['risk_level'], mod_data['risk_score'])}", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            f = mod_data["factors"]
            factor_df = pd.DataFrame([
                {"Factor": "Defect Volume (25%)", "Raw Metric": f"{f['volume']['raw']} defects", "Factor Score": f"{f['volume']['normalized']}/100", "Points Added": f"+{f['volume']['contribution']}"},
                {"Factor": "Severity Impact (30%)", "Raw Metric": f"Sev Sum {f['severity']['raw']}", "Factor Score": f"{f['severity']['normalized']}/100", "Points Added": f"+{f['severity']['contribution']}"},
                {"Factor": "Unresolved Backlog (20%)", "Raw Metric": f"{f['unresolved']['raw']} open bugs", "Factor Score": f"{f['unresolved']['normalized']}/100", "Points Added": f"+{f['unresolved']['contribution']}"},
                {"Factor": "Code Fragility/Reopen (15%)", "Raw Metric": f"{f['reopen']['raw']} reopens", "Factor Score": f"{f['reopen']['normalized']}/100", "Points Added": f"+{f['reopen']['contribution']}"},
                {"Factor": "Recency Velocity (10%)", "Raw Metric": f"{f['recency']['raw']} in 30d", "Factor Score": f"{f['recency']['normalized']}/100", "Points Added": f"+{f['recency']['contribution']}"}
            ])
            st.dataframe(factor_df, use_container_width=True, hide_index=True)

        with m_col2:
            st.markdown("#### 🎯 Targeted Mitigation Actions")
            for rec in mod_data["recommendations"]:
                st.markdown(f"""
                <div class="warning-box" style="margin-bottom: 8px;">
                    {rec}
                </div>
                """, unsafe_allow_html=True)


# ==========================================
# PAGE 9: ANALYTICS & REPORTS
# ==========================================
elif selected_page == "Analytics & Reports":
    st.title("📈 Defect Analytics & Report Generation")
    st.markdown("Generate executive quality reports, developer throughput metrics, and printable summaries.")

    all_defects = dm.get_all_defects()
    df_all = pd.DataFrame(all_defects)

    # Date Filter
    st.markdown("#### Report Filters")
    rf_col1, rf_col2 = st.columns(2)
    with rf_col1:
        rep_project = st.selectbox("Select Project for Report", ["All"] + dm.get_unique_projects())
    with rf_col2:
        rep_severity = st.selectbox("Select Severity Scope", ["All"] + dm.VALID_SEVERITIES)

    filtered_rep = dm.get_all_defects(project_name=rep_project, severity=rep_severity)
    df_rep = pd.DataFrame(filtered_rep)

    st.markdown(f"**Report Scope:** {len(df_rep)} defect records included.")

    # Visualizations for Report
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(analytics.get_severity_chart(df_rep), use_container_width=True)
    with c2:
        st.plotly_chart(analytics.get_status_chart(df_rep), use_container_width=True)

    # Developer Performance Matrix
    st.markdown("### 👨‍💻 Developer Performance & Defect Resolution Matrix")
    st.plotly_chart(analytics.get_developer_resolution_chart(), use_container_width=True)

    # Printable Executive Summary
    st.markdown("---")
    st.markdown("### 📄 Printable Academic Quality Report")
    
    kpis = analytics.get_dashboard_kpis()
    report_md = f"""# EXECUTIVE SOFTWARE DEFECT MANAGEMENT REPORT
**System:** Software Defect Management and Prediction System  
**Generated Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Evaluator Scope:** {rep_project} | Severity: {rep_severity}

---

## 1. Executive Summary & KPIs
- **Total Defects Logged:** {kpis['total']}
- **Active Open Defects:** {kpis['open']}
- **Resolved / Closed Defects:** {kpis['resolved']}
- **Critical / Blocker Defects:** {kpis['critical']}
- **Defects Reopened (Retest Failures):** {kpis['reopened']}
- **Overall Resolution Rate:** {kpis['resolution_rate']}%

## 2. Defect Classification Summary
- **Critical:** {len(df_all[df_all['severity'] == 'Critical']) if not df_all.empty else 0}
- **High:** {len(df_all[df_all['severity'] == 'High']) if not df_all.empty else 0}
- **Medium:** {len(df_all[df_all['severity'] == 'Medium']) if not df_all.empty else 0}
- **Low:** {len(df_all[df_all['severity'] == 'Low']) if not df_all.empty else 0}

## 3. High-Risk Modules Identified
"""
    preds = prediction.predict_module_defects()
    for p in preds[:4]:
        report_md += f"- **{p['module']}:** Risk Score = {p['risk_score']} ({p['risk_level']}) | Defects = {p['total_defects']}\n"

    report_md += """
---
*Report certified by Software Defect Management & Prediction System.*
"""

    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; font-family: monospace; white-space: pre-wrap;">
{report_md}
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        "📥 Download Executive Report (Markdown)",
        data=report_md.encode('utf-8'),
        file_name=f"executive_defect_report_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )


# ==========================================
# PAGE 10: USER MANAGEMENT
# ==========================================
elif selected_page == "User Management":
    if not auth.can_manage_users(current_user):
        st.error("⛔ Access Denied: User Management is strictly restricted to Administrators.")
        st.info("Please use the sidebar 'Quick Switch Demo Role' to switch to Admin.")
        st.stop()

    st.title("👤 User Accounts & Role Management")
    st.markdown("Manage system access accounts, roles (Admin, Tester, Developer), and demo credentials.")

    users = auth.get_all_users()
    df_users = pd.DataFrame(users)

    # Demo Credentials Quick Reference
    st.markdown("### 🔑 Predefined Demo Accounts")
    st.markdown("""
    | Role | Username | Password | Full Name | Capabilities |
    | :--- | :--- | :--- | :--- | :--- |
    | **Admin** | `admin` | `admin123` | Sarah Jenkins | View all, assign defects, modify priority, oversight |
    | **Tester** | `tester` | `tester123` | Alex Rivera | Report defects, upload screenshots, retest, close/reopen |
    | **Tester 2** | `tester2` | `tester123` | Maya Lin | Report defects, retest and verify fixes |
    | **Developer 1** | `dev1` | `dev123` | David Kim | View assigned, update to IN PROGRESS / FIXED, notes |
    | **Developer 2** | `dev2` | `dev123` | Elena Rostova | View assigned, resolve defects |
    | **Developer 3** | `dev3` | `dev123` | Marcus Vance | View assigned, UI/UX defect resolution |
    """)

    st.markdown("---")
    st.markdown("### 👥 Registered Users Inventory")
    if not df_users.empty:
        st.dataframe(df_users[["id", "username", "full_name", "email", "role", "created_at"]], use_container_width=True, hide_index=True)

    # Register New User Form - Strictly Restricted to Admin
    st.markdown("---")
    st.markdown("### ➕ Register New User")
    st.caption("Administrator portal: Provision and configure new user credentials directly in SQLite.")
    with st.form("create_user_form"):
        u_c1, u_c2 = st.columns(2)
        with u_c1:
            new_username = st.text_input("Username *", placeholder="e.g. john_qa")
            new_name = st.text_input("Full Name *", placeholder="e.g. John Doe")
            new_role = st.selectbox("Role *", ["Tester", "Developer", "Admin"])
        with u_c2:
            new_email = st.text_input("Email Address *", placeholder="e.g. john@defects.io")
            new_pw = st.text_input("Password *", type="password", placeholder="Enter secure password")

        create_btn = st.form_submit_button("Register User Account")

        if create_btn:
            if not new_username or not new_pw or not new_name or not new_email:
                st.error("All user fields are required.")
            else:
                try:
                    user_id = auth.create_user(
                        username=new_username,
                        password=new_pw,
                        full_name=new_name,
                        email=new_email,
                        role=new_role,
                        creator_role=current_user["role"]
                    )
                    st.success(f"User '{new_username}' successfully registered with ID {user_id}!")
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e).upper():
                        st.error(f"Error: Username '{new_username}' already exists. Please choose a different username.")
                    else:
                        st.error(f"Error registering user: {str(e)}")

    # Admin Role Modifier Tool
    st.markdown("---")
    st.markdown("### 🔄 Modify Existing User Role")
    with st.form("modify_user_role_form"):
        m_c1, m_c2 = st.columns(2)
        with m_c1:
            other_users = [u for u in users if u['id'] != current_user['id']]
            user_choices = [f"{u['id']}: {u['username']} ({u['full_name']}) - Current: {u['role']}" for u in other_users]
            if user_choices:
                sel_user_str = st.selectbox("Select User to Modify Role:", user_choices)
                target_uid = int(sel_user_str.split(":")[0])
            else:
                sel_user_str = None
                st.info("No other user accounts to modify.")
        with m_c2:
            target_new_role = st.selectbox("Assign New Role:", ["Tester", "Developer", "Admin"])
        
        update_role_btn = st.form_submit_button("Update Role")
        if update_role_btn and sel_user_str:
            auth.update_user_role(target_uid, target_new_role, creator_role=current_user["role"])
            st.success("User role updated successfully!")
            st.rerun()


# ==========================================
# PAGE 11: ABOUT PROJECT
# ==========================================
elif selected_page == "About Project":
    st.title("🛡️ Software Defect Management & Prediction System")
    st.markdown("### Complete Academic Project Submission & Architecture Overview")

    st.markdown("""
    This project is a complete, enterprise-grade, fully functional academic system designed to demonstrate 
    all six foundational principles of **Software Defect Management**:
    """)

    # 6 Core Concepts Mapping Cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <h4 style="color: #0d6efd; margin-top: 0;">1. Defect Prevention</h4>
            Analyzes database records for recurring failure patterns, identifies modules with repeated defects,
            and produces automated preventive recommendations (SAST, BDD, Concurrency controls).
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="kpi-card">
            <h4 style="color: #198754; margin-top: 0;">2. Defect Discovery</h4>
            Formal defect reporting interface with strict input validation, automatic sequential code generation
            (`BUG-0001`), screenshot attachments, and detailed reproduction steps.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="kpi-card">
            <h4 style="color: #0dcaf0; margin-top: 0;">3. Defect Recording & Reporting</h4>
            Persistent SQLite storage, multi-criteria filtering (module, severity, priority, status), search,
            detailed defect inspection, and CSV data export.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="kpi-card">
            <h4 style="color: #fd7e14; margin-top: 0;">4. Defect Classification</h4>
            Comprehensive taxonomy adhering to IEEE 1044 / ISO 25010 standards across Severity, Priority,
            and Technical Defect Type, with visual badges and reclassification audit logging.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="kpi-card">
            <h4 style="color: #6f42c1; margin-top: 0;">5. Defect Resolution</h4>
            Enforces strict lifecycle state machine: <code>NEW ➔ ASSIGNED ➔ IN PROGRESS ➔ FIXED ➔ RETESTING ➔ CLOSED</code>
            (with <code>RETESTING ➔ REOPENED</code> regression loops) and complete timestamped audit history.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="kpi-card">
            <h4 style="color: #dc3545; margin-top: 0;">6. Defect Prediction</h4>
            Transparent, explainable multi-factor risk-scoring algorithm (0-100) combining defect volume, severity impact,
            unresolved backlog debt, fragility (reopened bugs), and recent velocity.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🛠️ Technology Stack")
    st.markdown("""
    - **Frontend:** Streamlit 1.35+ with responsive custom CSS
    - **Backend:** Python 3.10+
    - **Database:** SQLite 3 with strict foreign keys, indexing, and transactional integrity
    - **Data Processing:** Pandas
    - **Data Visualization:** Plotly Express & Plotly Graph Objects
    - **Test Harness:** Pytest automated test suite
    """)

    st.markdown("---")
    st.markdown("### 📋 Quick Evaluation Instructions")
    st.markdown("""
    1. **Explore Dashboard:** Observe real-time KPIs and interactive Plotly visualizations.
    2. **Report a Defect:** Switch role to *Tester* in the sidebar and navigate to **'Report New Defect'**. Submit a bug and note the unique auto-generated ID.
    3. **Assign the Defect:** Switch role to *Admin* and open **'Assign Defects'** to assign it to *dev1*.
    4. **Resolve the Defect:** Switch role to *Developer (dev1)* and open **'Resolution Management'** to advance status to *IN PROGRESS* and then *FIXED*.
    5. **Retest & Verify:** Switch role back to *Tester*, test the retest workflow to either *CLOSE* or *REOPEN* the bug.
    6. **Review Prediction & Prevention:** Inspect the explainable risk calculations and automated preventive action plans.
    """)

