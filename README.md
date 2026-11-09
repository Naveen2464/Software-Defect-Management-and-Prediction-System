# Software Defect Management and Prediction System

A complete, enterprise-grade, fully functional academic project implementing the complete software quality engineering and defect management framework:
1. **Defect Prevention** (pattern identification, root-cause recommendations, high-risk module isolation)
2. **Defect Discovery** (validated defect reporting, auto-generated unique ID `BUG-XXXX`, screenshot attachments)
3. **Defect Recording and Reporting** (persistent SQLite storage, multi-criteria filtering, CSV export)
4. **Defect Classification** (IEEE 1044 / ISO 25010 standards: Severity, Priority, Defect Type)
5. **Defect Resolution** (deterministic state machine: `NEW` ➔ `ASSIGNED` ➔ `IN PROGRESS` ➔ `FIXED` ➔ `RETESTING` ➔ `CLOSED` and `REOPENED` regression loops with complete timestamped audit history)
6. **Defect Prediction** (transparent, explainable multi-factor risk-scoring algorithm 0–100)

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your workstation (Windows, Linux, Ubuntu, or macOS).

### 2. Install Dependencies
Open your terminal or VS Code Command Prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

### 3. Launch the Application
Run the Streamlit application:

```bash
streamlit run app.py
```

The application will start immediately and automatically open your default web browser at:
👉 **`http://localhost:8501`**

---

## 🔑 Role-Based Access Control (RBAC) & Predefined Demo Accounts

The system enforces end-to-end multi-tier Role-Based Access Control at both the UI navigation layer and the backend API layer.

### Role Permissions Matrix:

| Feature / Page | Admin (11 Pages) | Tester (9 Pages) | Developer (8 Pages) |
| :--- | :---: | :---: | :---: |
| **1. Dashboard** | Global Overview & KPIs | Discovery Backlog | Personal Workload & Assigned Queue |
| **2. Report New Defect** | ✅ Full Access | ✅ Submit & Attach Screenshots | ⛔ Restricted |
| **3. All Defects** | ✅ All Defects | ✅ All Defects | 🔒 Only Assigned Defects |
| **4. Defect Classification** | ✅ View & Reclassify | ✅ View & Reclassify | 👁️ Read-only View |
| **5. Assign Defects** | ✅ Assign Developers | ⛔ Restricted | ⛔ Restricted |
| **6. Resolution Management** | ✅ Full Oversight | ✅ Retest, Close, Reopen | 🔒 Update to In Progress / Fixed |
| **7. Defect Prevention** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **8. Defect Prediction** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **9. Analytics & Reports** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **10. User Management** | ✅ Provision Users & Roles | ⛔ Restricted | ⛔ Restricted |
| **11. About Project** | ✅ Full Access | ✅ Full Access | ✅ Full Access |

### Predefined Demo Accounts:

| Role | Username | Password | Full Name | Academic Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Sarah Jenkins | Full system oversight, developer assignment, priority change, user provisioning |
| **Tester** | `tester` | `tester123` | Alex Rivera | Report defects, upload screenshots, retest fixed builds, close/reopen |
| **Tester 2** | `tester2` | `tester123` | Maya Lin | Report defects, verify fixes in QA staging |
| **Developer 1** | `dev1` | `dev123` | David Kim | View assigned defects, transition to `IN PROGRESS`, mark `FIXED` with notes |
| **Developer 2** | `dev2` | `dev123` | Elena Rostova | View assigned defects, resolve backend defects |
| **Developer 3** | `dev3` | `dev123` | Marcus Vance | View assigned defects, resolve UI/UX defects |

> **⚡ Quick Switch Demo Role:** Use the expander in the sidebar to switch between any demo user instantly. The application updates the authenticated session identity, refreshes permissions, resets navigation to an accessible page, and updates the role badge (Purple for Admin, Blue for Tester, Green for Developer).

---

## 🧪 Automated Testing

All 29 unit, integration, RBAC, and lifecycle state-machine tests can be executed via Pytest:

```bash
pytest -v
```

### Expected Output:
```text
tests/test_database.py::test_init_db_creates_all_tables PASSED           [  3%]
tests/test_database.py::test_indexes_exist PASSED                        [  6%]
tests/test_database.py::test_password_hashing PASSED                     [ 10%]
tests/test_database.py::test_seed_sample_data PASSED                     [ 13%]
tests/test_database.py::test_seed_sample_data_idempotency PASSED         [ 17%]
tests/test_database.py::test_foreign_key_enforcement PASSED              [ 20%]
tests/test_database.py::test_admin_user_management_permissions PASSED    [ 24%]
tests/test_defects.py::test_generate_next_defect_code PASSED             [ 27%]
tests/test_defects.py::test_create_defect_success PASSED                 [ 31%]
tests/test_defects.py::test_create_defect_validation_errors PASSED       [ 34%]
tests/test_defects.py::test_assign_defect PASSED                         [ 37%]
tests/test_defects.py::test_complete_lifecycle_transitions PASSED        [ 41%]
tests/test_defects.py::test_reopen_lifecycle_flow PASSED                 [ 44%]
tests/test_defects.py::test_invalid_lifecycle_transition_rejected PASSED [ 48%]
tests/test_defects.py::test_developer_cannot_close_defect PASSED         [ 51%]
tests/test_defects.py::test_reclassification PASSED                      [ 55%]
tests/test_defects.py::test_csv_export PASSED                            [ 58%]
tests/test_prediction.py::test_predict_module_defects_structure PASSED   [ 62%]
tests/test_prediction.py::test_risk_level_thresholds PASSED              [ 65%]
tests/test_prediction.py::test_high_risk_ranking PASSED                  [ 68%]
tests/test_prediction.py::test_prevention_pattern_analysis PASSED        [ 72%]
tests/test_rbac.py::test_admin_has_access_to_all_11_pages PASSED         [ 75%]
tests/test_rbac.py::test_tester_page_permissions PASSED                  [ 79%]
tests/test_rbac.py::test_developer_page_permissions PASSED               [ 82%]
tests/test_rbac.py::test_developer_can_only_modify_assigned_defects PASSED [ 86%]
tests/test_rbac.py::test_developer_cannot_close_defects PASSED           [ 89%]
tests/test_rbac.py::test_tester_retest_and_close_lifecycle PASSED        [ 93%]
tests/test_rbac.py::test_tester_reopen_on_failed_retest PASSED           [ 96%]
tests/test_rbac.py::test_backend_unauthorized_operations_rejected PASSED [100%]

============================= 29 passed in 5.30s ==============================
```

---

## 📁 Project Folder Structure

```text
software_testing-assignment1/
│
├── app.py                      # Main Streamlit dashboard & multi-page navigation
├── database.py                 # SQLite relational schema, indexing, and seed data loader
├── auth.py                     # Authentication, salted SHA-256 password hashing & RBAC
├── defect_management.py        # Defect discovery, state-machine lifecycle, triage & audit
├── prevention.py               # Pattern discovery, repeated failure analysis & prevention plan
├── prediction.py               # Explainable multi-factor defect risk-scoring algorithm (0-100)
├── analytics.py                # Plotly interactive charts, KPI metrics, and report exporter
├── requirements.txt            # Python dependencies
├── README.md                   # Installation and usage instructions
│
├── database/
│   └── defects.db              # SQLite database (auto-created on startup)
│
├── uploads/                    # Directory for defect screenshot attachments
│
├── assets/
│   └── style.css               # Modern enterprise design & status pill badge styling
│
├── tests/                      # Automated Pytest suite (29 automated tests)
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_defects.py
│   ├── test_prediction.py
│   └── test_rbac.py
│
└── docs/                       # Complete Academic Documentation
    ├── project_report.md       # Full 24-section Academic Project Report
    ├── project_report.html     # Beautiful interactive HTML submission report
    ├── viva_defense_guide.md   # Comprehensive viva and oral defense guide
    └── system_architecture.md  # Architectural specification with Mermaid diagrams
```
```

---

## 🛠️ Technology Stack

- **Frontend:** Streamlit 1.35+ with responsive custom CSS
- **Backend:** Python 3.10+
- **Database:** SQLite 3 with strict foreign keys, indexing, and transactional integrity
- **Data Processing:** Pandas
- **Data Visualization:** Plotly Express & Plotly Graph Objects
- **Test Harness:** Pytest automated test framework

---

## 🧭 Navigation & Feature Walkthrough

The application sidebar provides 11 dedicated functional pages:

1. **Dashboard:** 6 real-time KPI cards and 7 interactive Plotly visualizations (Severity, Status, Category, Module, Monthly Trend, Developer Resolution, and Predicted Risk).
2. **Report New Defect:** Complete defect intake form with automatic ID generation (`BUG-0017`), required field validation, and screenshot upload.
3. **All Defects:** Searchable and filterable registry with CSV export and an interactive detail inspector with history timelines.
4. **Defect Classification:** IEEE 1044 / ISO 25010 taxonomy breakdown and authorized reclassification tool.
5. **Assign Defects:** Workload balance chart and assignment triage interface for Admins.
6. **Resolution Management:** Role-aware lifecycle action station enforcing the defect state machine:
   `NEW` ➔ `ASSIGNED` ➔ `IN PROGRESS` ➔ `FIXED` ➔ `RETESTING` ➔ `CLOSED`  
   (or `RETESTING` ➔ `REOPENED` ➔ `IN PROGRESS`).
7. **Defect Prevention:** Empirical pattern detection, high-risk module isolation, and downloadable action plans.
8. **Defect Prediction:** Explainable risk-scoring algorithm with transparent factor contributions (Volume, Severity, Unresolved, Reopen, Recency).
9. **Analytics & Reports:** Executive summary metrics, developer performance matrix, and downloadable reports.
10. **User Management:** Registered user inventory, demo credential guide, and new user registration form.
11. **About Project:** Academic overview, 6 concepts mapping, and evaluation guide.

---

## 📄 Academic Project Report & Architecture

Complete academic documentation is included inside the `docs/` directory:
- **`docs/project_report.md`**: Complete 24-section formal academic project report formatted according to university standards.
- **`docs/system_architecture.md`**: Full architectural specification featuring Mermaid flowcharts, state-machine diagrams, entity-relationship diagrams, and sequence flows.

#   S o f t w a r e - D e f e c t - M a n a g e m e n t - a n d - P r e d i c t i o n - S y s t e m  
 