# VIVA DEFENSE & PRESENTATION GUIDE
## Software Defect Management and Prediction System

This guide prepares you to present and defend your academic software project with 100% confidence in front of professors and external examiners.

---

## 1. 2-Minute High-Impact Project Pitch

> *"Good morning respected evaluators. Today I am presenting the **Software Defect Management and Prediction System**.*
> 
> *In traditional software testing, defect tracking tools like spreadsheets or legacy systems act merely as passive bug repositories—they record issues after they cause failures. Our project bridges software testing theory with enterprise practice by implementing all six core concepts of Defect Management:*
> 1. *Defect Prevention through empirical pattern recognition and root cause analysis,*
> 2. *Defect Discovery with standardized validation and automatic unique code generation,*
> 3. *Defect Recording and Reporting using a normalized relational SQLite database with instant CSV export,*
> 4. *Defect Classification adhering to IEEE 1044 / ISO 25010 across Severity, Priority, and Defect Type,*
> 5. *Defect Resolution governed by an enforceable finite-state machine that prevents unauthorized closures and tracks a complete audit trail, and*
> 6. *Defect Prediction using a transparent, multi-factor risk-scoring algorithm that predicts high-risk software modules before release.*
> 
> *The system features Role-Based Access Control for Admins, Testers, and Developers, interactive Plotly visualizations, and 29 automated Pytest test cases with 100% pass rate."*

---

## 2. Live Demonstration Flow (Step-by-Step)

Follow these steps during your live demo:

### Step 1: Dashboard Overview (Page 1)
- Point to the **6 Top KPI Cards**: Total Defects (16), Open Defects, Resolved, Critical, Reopened, and Resolution Rate.
- Explain the **Interactive Plotly Visualizations**:
  - Donut chart of Severity (Critical, High, Medium, Low).
  - Status Donut showing the distribution across lifecycle stages.
  - Defect Category & Module distribution.
  - Monthly defect discovery trends.
  - Developer-wise workload and resolution.
  - High-Risk Modules predicted by our algorithm.

### Step 2: Defect Discovery (Page 2)
- In the sidebar, use the **Quick Switch Demo Role** to switch to **Tester (alex.tester)**.
- Navigate to **"2. Report New Defect"**.
- Fill out the form:
  - Project: *E-Commerce Web Portal*
  - Module: *Payment Gateway*
  - Title: *Payment gateway times out during card 3D Secure redirect*
  - Severity: *Critical*, Priority: *P1 - Urgent*
  - Description: *Customer card remains charged but order status displays Pending.*
  - Steps, Expected, Actual.
- Click **"🚀 Submit Defect"**.
- Point out the success banner and the auto-generated defect ID: **`BUG-0017`**.

### Step 3: Defect Recording & Inspection (Page 3)
- Navigate to **"3. All Defects"**.
- Show the multi-criteria filters (filter by Module = Payment Gateway, or Severity = Critical).
- Click **"Export Defect Records (CSV)"** to demonstrate reporting.
- In the Defect Detail Inspector, select `BUG-0001`:
  - Show the detailed description, steps to reproduce, expected/actual results.
  - Show the **Screenshot Attachment** rendered directly from the test evidence.
  - Show the **Defect History Audit Trail** showing timestamps, previous/new status, and the developer/tester names.

### Step 4: Defect Classification (Page 4)
- Explain the distinction between **Severity** (technical impact) and **Priority** (business urgency).
- Show the classification breakdown charts (Severity Donut, Priority Bar, Defect Type Bar).
- Use the **Reclassification Tool** to change a defect's priority or severity, enter an audit comment, and show how it is recorded.

### Step 5: Triage & Assignment (Page 5)
- Switch role to **Admin (admin)** using the sidebar switcher.
- Navigate to **"5. Assign Defects"**.
- Show the Developer Workload balance chart.
- Select our newly created defect (`BUG-0017`) and assign it to **David Kim (dev1)** with instructions.

### Step 6: Defect Resolution Lifecycle (Page 6)
- Switch role to **Developer (dev1)**.
- Navigate to **"6. Resolution Management"**.
- Explain the **Defect Lifecycle Finite State Machine**:
  `NEW` ➔ `ASSIGNED` ➔ `IN PROGRESS` ➔ `FIXED` ➔ `RETESTING` ➔ `CLOSED`
- Select the assigned bug:
  - Notice the allowed next state is **`IN PROGRESS`**. Click Update.
  - Now advance to **`FIXED`**, type resolution notes: *"Implemented idempotency token in webhook handler"*, and submit.
- Switch role to **Tester (alex.tester)**:
  - Explain to the examiner: *"Notice that the developer could NOT close the defect directly! Academic quality standards require an independent QA retest."*
  - Advance status to **`RETESTING`**.
  - Show the two options: **`CLOSED`** (if verification passes) or **`REOPENED`** (if verification fails).
  - Select **`CLOSED`** with comments: *"Verified fix across 20 test runs."*

### Step 7: Defect Prevention (Page 7)
- Navigate to **"7. Defect Prevention"**.
- Explain: *"This is Module 1. It scans actual SQLite records for recurrent defect patterns."*
- Show the detected failure clusters:
  - Authentication & Token Management
  - Concurrency, Race Conditions & Deadlocks
  - Input Validation & Boundary Overflows
- Show the **Modules Requiring Extra Testing** and the **Automated Prevention Action Plan**.
- Click **"Download Defect Prevention Plan (.md)"**.

### Step 8: Defect Prediction (Page 8)
- Navigate to **"8. Defect Prediction"**.
- Highlight: *"This is Module 6. It calculates an explainable defect risk score (0 to 100) based on historical software metrics."*
- Show the formula:
  $$R_m = 0.25 \cdot S_{\text{volume}} + 0.30 \cdot S_{\text{severity}} + 0.20 \cdot S_{\text{unresolved}} + 0.15 \cdot S_{\text{reopen}} + 0.10 \cdot S_{\text{recency}}$$
- Inspect the **Explainable Factor Breakdown**:
  - Show how many points were contributed by Volume, Severity, Unresolved Debt, Reopened Bugs, and Recency Velocity.
  - Explain why Login and Payment Gateway have higher risk scores than Dashboard or Shopping Cart.

---

## 3. Top 15 Viva Questions & Answers

### Q1: What is the difference between Defect Severity and Defect Priority?
**Answer:**
- **Severity** measures the degree of impact that a defect has on the software system from a technical and operational perspective (Critical, High, Medium, Low). It is determined by QA Testers based on functionality loss (e.g., system crash, data loss).
- **Priority** measures the urgency with which a defect must be resolved from a business and project schedule perspective (P1 - Urgent, P2 - High, P3 - Normal, P4 - Low). It is determined by Project Managers / Product Owners based on release timelines and business impact.
- *Classic Example:* A spelling mistake on the company logo on the homepage has **Low Severity** (cosmetic, system does not crash) but **High Priority** (brand reputation). Conversely, an intermittent crash in an obscure rarely-used admin report has **High Severity** but **Low Priority**.

### Q2: What are the six core concepts of Defect Management implemented in your project?
**Answer:**
1. **Defect Prevention:** Analyzing historical defect patterns to eliminate root causes before coding or release.
2. **Defect Discovery:** Detecting, capturing, validating, and logging defects with reproducible steps.
3. **Defect Recording and Reporting:** Storing defect records persistently, facilitating search, filtering, and metric reporting.
4. **Defect Classification:** Categorizing defects by severity, priority, and technical failure type (IEEE 1044).
5. **Defect Resolution:** Managing the lifecycle from assignment to code fix, independent QA retesting, and closure.
6. **Defect Prediction:** Forecasting software modules with high defect probability using empirical metrics.

### Q3: Why did you use an explainable rule-based scoring algorithm instead of an opaque Machine Learning model for Defect Prediction?
**Answer:**
In Software Reliability Engineering (SRE), transparency and interpretability are paramount. Standard ML models (such as deep neural networks) function as "black boxes" that cannot explain to software architects *why* a module was flagged. Our algorithm explicitly breaks down the composite score (0–100) into five measurable metrics:
- Defect Volume (25%)
- Weighted Severity Impact (30%)
- Unresolved Technical Debt (20%)
- Code Fragility / Reopens (15%)
- Recency Velocity within 30 days (10%)
This allows engineering leads to see exactly which factor drove the risk score and apply targeted mitigation actions.

### Q4: Can a developer directly mark a defect as "CLOSED"?
**Answer:**
No! Our system enforces strict Role-Based Access Control and finite-state machine transitions. When a developer completes a code fix, they can only advance the status to **`FIXED`** with mandatory resolution notes. Only a QA Tester or Admin can advance the defect to **`RETESTING`** and ultimately **`CLOSED`** upon passing verification. This enforces the quality engineering principle of independent verification.

### Q5: What happens if a bug fails during QA retesting?
**Answer:**
The defect enters the regression loop:
$$\text{RETESTING} \longrightarrow \text{REOPENED} \longrightarrow \text{IN PROGRESS}$$
The tester transitions the status to **`REOPENED`** and enters retest failure logs. The defect is re-queued for the assigned developer to investigate and fix. The system logs this failure, which increases the module's "Reopened Defect Factor" in our prediction algorithm.

### Q6: What database design choices were made in this project?
**Answer:**
We used SQLite 3 normalized to Third Normal Form (3NF) comprising five tables: `users`, `projects`, `defects`, `assignments`, and `defect_history`. We enforced:
- Primary surrogate keys and unique constraints (`defect_code`, `username`).
- Foreign key constraints with cascading rules (`PRAGMA foreign_keys = ON`).
- B-Tree performance indexes on `module`, `status`, `severity`, `priority`, and `defect_id`.
- Salted SHA-256 password hashing.

### Q7: How does Defect Prevention differ from Defect Discovery?
**Answer:**
- **Defect Discovery** is reactive: it detects faults that have already been injected into the code during testing execution.
- **Defect Prevention** is proactive: it performs root-cause analysis (RCA) on discovered defects to identify recurring patterns (e.g., repeated authentication bypasses or unhandled null pointers) and implements architectural controls, automated SAST tooling, and developer checklists so those defects are never coded in future sprints.

### Q8: What standard did you use for Defect Classification?
**Answer:**
We adopted the taxonomy principles of **IEEE Std 1044-2009** (Standard Classification for Software Anomalies) and **ISO/IEC 25010** (System and Software Quality Models), classifying defects across:
- Operational Severity (Critical, High, Medium, Low)
- Business Priority (P1 to P4)
- Technical Defect Type (Functional, Performance, Security, UI/UX, Compatibility, Database, Integration).

### Q9: How is the unique defect code generated?
**Answer:**
Our `generate_next_defect_code()` function queries the database for the highest existing defect sequence number, parses the integer suffix, increments it, and formats it as a zero-padded string (`BUG-0001`, `BUG-0002`, ..., `BUG-0017`). This prevents duplicate IDs and ensures chronological consistency.

### Q10: How did you test your project?
**Answer:**
We developed 20 automated unit and integration tests using **Pytest**:
- `test_database.py` (6 tests): tests table creation, foreign keys, indexes, password hashing, and seeding idempotency.
- `test_defects.py` (10 tests): tests validation, sequential code generation, lifecycle state transitions, invalid transition rejection, developer permission enforcement, and CSV export.
- `test_prediction.py` (4 tests): tests risk score boundedness ($0 \le R_m \le 100$), risk tiers, and pattern recognition.
All 20 tests pass with a 100% pass rate.

### Q11: How are screenshots handled?
**Answer:**
Testers can upload screenshots (`.png`, `.jpg`, `.jpeg`). The application saves the file to the `uploads/` directory with a unique timestamped filename and persists the path in `defects.screenshot_path`. If a screenshot is missing or not provided, the application handles it gracefully without crashing.

### Q12: Why did you choose Streamlit and Plotly?
**Answer:**
Streamlit allows building modern, responsive, data-driven web applications natively in Python without fragile frontend JavaScript frameworks. Plotly enables interactive, hardware-accelerated SVG visualizations (hover tooltips, dynamic filtering, slice extraction) that update in real time as database records change.

### Q13: What is the Boehm Defect Cost Amplification model?
**Answer:**
Barry Boehm's empirical research showed that the cost of finding and fixing a software defect increases exponentially as the defect escapes into later lifecycle phases. A defect that costs \$1 to fix in Requirements costs \$10 to fix in Coding, \$50 to fix in Testing, and \$100 to \$1000+ to fix in Production. This highlights why Defect Prevention and Prediction are essential.

### Q14: How does the system ensure data persistence?
**Answer:**
All operations (new defects, assignments, reclassifications, status updates) execute immediate parameterized SQL transactions committed directly to `database/defects.db`. Even if the Streamlit server or computer is restarted, all records, assignments, and audit logs remain fully intact.

### Q15: What are the future enhancements for this project?
**Answer:**
1. Integration with enterprise Jira and GitHub Issues via bi-directional webhooks.
2. Natural Language Processing (NLP) sentence-transformers to detect duplicate bug reports before submission.
3. Automated CI/CD webhooks linking defect resolution directly to Git commit SHAs.

