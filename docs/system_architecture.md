# SYSTEM ARCHITECTURE SPECIFICATION
## Software Defect Management and Prediction System

This document outlines the architectural blueprint, data flow, state machine, and entity relationships for the Software Defect Management and Prediction System.

---

### 1. High-Level Architectural Diagram

The system employs a multi-tiered architecture comprising a presentation layer powered by Streamlit, application services handling business logic, and a transactional SQLite database engine.

```mermaid
flowchart TD
    subgraph Presentation_Layer["Presentation Layer (Streamlit & Custom CSS)"]
        UI_Dash["Executive Dashboard"]
        UI_Disc["Defect Discovery Form"]
        UI_Rec["Defect Inventory & Search"]
        UI_Class["Taxonomy & Reclassification"]
        UI_Assign["Engineering Workload & Triage"]
        UI_Res["Resolution & Retest Hub"]
        UI_Prev["Defect Prevention Insights"]
        UI_Pred["Defect Risk Prediction Engine"]
    end

    subgraph Service_Layer["Core Logic & Processing Services"]
        AUTH["Authentication & RBAC (auth.py)"]
        DM["Defect Lifecycle Manager (defect_management.py)"]
        PREV["Pattern & RCA Engine (prevention.py)"]
        PRED["Risk Scoring Engine (prediction.py)"]
        ANALYTICS["KPI & Plotly Visualizer (analytics.py)"]
    end

    subgraph Data_Layer["Relational Persistence Layer (SQLite 3)"]
        T_USERS[("users Table")]
        T_PROJECTS[("projects Table")]
        T_DEFECTS[("defects Table")]
        T_ASSIGN[("assignments Table")]
        T_HISTORY[("defect_history Table")]
        IDX["Performance B-Tree Indexes"]
    end

    Presentation_Layer --> Service_Layer
    Service_Layer --> Data_Layer
```

---

### 2. Defect Lifecycle Finite State Machine

The defect resolution workflow enforces a deterministic state machine. Out-of-order or invalid transitions are strictly rejected at the business logic layer.

```mermaid
stateDiagram-v2
    [*] --> NEW: Tester Discovers Defect
    NEW --> ASSIGNED: Admin Assigns Developer
    ASSIGNED --> IN_PROGRESS: Developer Starts Investigation
    IN_PROGRESS --> FIXED: Developer Submits Fix & Notes
    FIXED --> RETESTING: Tester Begins QA Verification
    RETESTING --> CLOSED: Verification Passes (Defect Closed)
    RETESTING --> REOPENED: Verification Fails (Regression)
    REOPENED --> IN_PROGRESS: Developer Re-evaluates Fix
    CLOSED --> REOPENED: Post-Release Regression Discovered
```

---

### 3. Entity-Relationship (ER) Diagram

The relational schema ensures 3NF normalization, referential integrity via foreign key constraints, and fast query execution via multi-column indexing.

```mermaid
erDiagram
    USERS ||--o{ DEFECTS : "reports (reporter_id)"
    USERS ||--o{ DEFECTS : "assigned_to (assigned_to_id)"
    USERS ||--o{ ASSIGNMENTS : "assigns (assigned_by_id)"
    USERS ||--o{ ASSIGNMENTS : "receives (assigned_to_id)"
    USERS ||--o{ DEFECT_HISTORY : "modifies (changed_by_id)"
    PROJECTS ||--o{ DEFECTS : "contains (project_name)"
    DEFECTS ||--o{ ASSIGNMENTS : "tracks"
    DEFECTS ||--o{ DEFECT_HISTORY : "records"

    USERS {
        int id PK
        string username UK
        string password_hash
        string full_name
        string email
        string role
        string created_at
    }

    PROJECTS {
        int id PK
        string name UK
        string description
        string created_at
    }

    DEFECTS {
        int id PK
        string defect_code UK
        string project_name
        string module
        string title
        string description
        string steps_to_reproduce
        string expected_result
        string actual_result
        string defect_type
        string severity
        string priority
        string environment
        string screenshot_path
        int reporter_id FK
        int assigned_to_id FK
        string status
        string resolution_notes
        string created_at
        string updated_at
    }

    ASSIGNMENTS {
        int id PK
        int defect_id FK
        int assigned_by_id FK
        int assigned_to_id FK
        string assigned_at
        string notes
    }

    DEFECT_HISTORY {
        int id PK
        int defect_id FK
        string previous_status
        string new_status
        int changed_by_id FK
        string comments
        string timestamp
    }
```

---

### 4. Defect Discovery & Resolution Sequence

The sequence diagram below displays the end-to-end interactions between the three user roles across a defect's lifespan.

```mermaid
sequenceDiagram
    autonumber
    actor Tester as QA Tester
    actor Admin as QA Admin / Lead
    actor Dev as Developer
    participant UI as Streamlit UI
    participant App as Application Logic
    participant DB as SQLite Database

    Tester->>UI: Submit Defect Report (Module, Title, Severity, Steps)
    UI->>App: create_defect()
    App->>DB: INSERT into defects (status='NEW')
    App->>DB: INSERT into defect_history (previous='NONE', new='NEW')
    DB-->>UI: Return unique defect_code (e.g. BUG-0017)
    UI-->>Tester: Display Confirmation & Defect Details

    Admin->>UI: Select Defect & Assign to Developer
    UI->>App: assign_defect(defect_id, dev_id)
    App->>DB: UPDATE defects (status='ASSIGNED')
    App->>DB: INSERT into assignments & defect_history
    DB-->>UI: Update Success

    Dev->>UI: Transition Status to 'IN PROGRESS'
    UI->>App: update_defect_status('IN PROGRESS')
    App->>DB: UPDATE defects & INSERT defect_history

    Dev->>UI: Transition to 'FIXED' with Resolution Notes
    UI->>App: update_defect_status('FIXED', notes)
    App->>DB: UPDATE defects & INSERT defect_history

    Tester->>UI: Advance to 'RETESTING' in QA Staging
    UI->>App: update_defect_status('RETESTING')
    App->>DB: UPDATE defects & INSERT defect_history

    alt Fix is Verified
        Tester->>UI: Advance to 'CLOSED'
        UI->>App: update_defect_status('CLOSED', 'Passes all tests')
        App->>DB: UPDATE defects (status='CLOSED')
    else Fix Fails Verification
        Tester->>UI: Advance to 'REOPENED'
        UI->>App: update_defect_status('REOPENED', 'Bug still persists')
        App->>DB: UPDATE defects (status='REOPENED')
    end
```

---

### 5. Multi-Factor Defect Risk Prediction Algorithm

The prediction engine evaluates risk across five distinct software quality dimensions without opaque black-box assumptions:

$$\text{Risk Score } R_m = \min\left(100, \; 0.25 \cdot S_{\text{volume}} + 0.30 \cdot S_{\text{severity}} + 0.20 \cdot S_{\text{unresolved}} + 0.15 \cdot S_{\text{reopen}} + 0.10 \cdot S_{\text{recency}}\right)$$

#### Sub-Component Specifications:
1. **$S_{\text{volume}}$ (Weight: 25%):**
   $$\min\left(100, \; \frac{D_m}{5.0} \times 100\right)$$
   Measures absolute defect density; saturated at 5 defects.
2. **$S_{\text{severity}}$ (Weight: 30%):**
   $$\text{Raw}_{\text{sev}} = (C_m \times 4.0) + (H_m \times 2.5) + (M_m \times 1.0) + (L_m \times 0.25)$$
   $$S_{\text{severity}} = \min\left(100, \; \frac{\text{Raw}_{\text{sev}}}{10.0} \times 100\right)$$
3. **$S_{\text{unresolved}}$ (Weight: 20%):**
   $$S_{\text{unresolved}} = \left(\frac{U_m}{D_m}\right) \times 100 \times \min\left(1.0, \; \frac{U_m}{2.0}\right)$$
   Penalizes active unresolved technical debt.
4. **$S_{\text{reopen}}$ (Weight: 15%):**
   $$S_{\text{reopen}} = \min(100, \; R_m \times 50.0)$$
   Captures regression instability and fragile implementations.
5. **$S_{\text{recency}}$ (Weight: 10%):**
   $$S_{\text{recency}} = \min\left(100, \; \frac{\text{Recent}_m}{3.0} \times 100\right)$$
   Reflects defect clustering within the last 30 calendar days.

