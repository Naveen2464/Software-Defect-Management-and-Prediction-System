"""
defect_management.py - Core defect lifecycle, recording, assignment, classification, and workflow tracking.
Enforces academic defect lifecycle state transitions and complete audit history.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from database import get_connection

# Allowed lifecycle state transitions
VALID_TRANSITIONS = {
    "NEW": ["ASSIGNED"],
    "ASSIGNED": ["IN PROGRESS"],
    "IN PROGRESS": ["FIXED"],
    "FIXED": ["RETESTING"],
    "RETESTING": ["CLOSED", "REOPENED"],
    "REOPENED": ["IN PROGRESS"],
    "CLOSED": ["REOPENED"]  # Permitted if regression occurs during post-release
}

VALID_SEVERITIES = ["Critical", "High", "Medium", "Low"]
VALID_PRIORITIES = ["P1 - Urgent", "P2 - High", "P3 - Normal", "P4 - Low"]
VALID_DEFECT_TYPES = [
    "Functional", "Performance", "Security", "UI/UX",
    "Compatibility", "Database", "Integration"
]
VALID_ENVIRONMENTS = ["Production", "Staging", "QA / Test", "Development"]


def generate_next_defect_code(db_path: str = None) -> str:
    """Generate next sequential unique defect code like BUG-0001."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT defect_code FROM defects ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row or not row["defect_code"]:
        return "BUG-0001"

    last_code = row["defect_code"]
    try:
        prefix, num_str = last_code.split("-")
        next_num = int(num_str) + 1
        return f"BUG-{next_num:04d}"
    except Exception:
        return f"BUG-0001"


def get_valid_next_statuses(current_status: str, user_role: str = "Admin") -> List[str]:
    """Return list of valid next status options based on current status and user role."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    
    # Role-based restriction:
    if user_role == "Developer":
        # Developers can move ASSIGNED -> IN PROGRESS and IN PROGRESS -> FIXED
        return [s for s in allowed if s in ["IN PROGRESS", "FIXED"]]
    elif user_role == "Tester":
        # Testers can move FIXED -> RETESTING and RETESTING -> CLOSED / REOPENED
        return [s for s in allowed if s in ["RETESTING", "CLOSED", "REOPENED"]]
    elif user_role == "Admin":
        return allowed
    return allowed


def create_defect(
    project_name: str,
    module: str,
    title: str,
    description: str,
    steps_to_reproduce: str,
    expected_result: str,
    actual_result: str,
    defect_type: str,
    severity: str,
    priority: str,
    environment: str,
    reporter_id: int,
    screenshot_path: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    reporter_role: Optional[str] = None,
    db_path: str = None
) -> Tuple[int, str]:
    """Validate, create and persist a new defect record. Enforces role authorization."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Determine reporter role
    role = reporter_role
    if not role:
        cursor.execute("SELECT role FROM users WHERE id = ?", (reporter_id,))
        u = cursor.fetchone()
        role = u["role"] if u else "Tester"

    if role not in ("Admin", "Tester"):
        conn.close()
        raise PermissionError("Developers are not permitted to report new defects.")

    if assigned_to_id and role != "Admin":
        conn.close()
        raise PermissionError("Only Administrators can assign defects upon creation.")

    # Validation
    if not title or not title.strip():
        conn.close()
        raise ValueError("Defect title is required.")
    if not description or not description.strip():
        conn.close()
        raise ValueError("Defect description is required.")
    if not module or not module.strip():
        conn.close()
        raise ValueError("Software module is required.")
    if not project_name or not project_name.strip():
        conn.close()
        raise ValueError("Project name is required.")
    if severity not in VALID_SEVERITIES:
        conn.close()
        raise ValueError(f"Invalid severity '{severity}'. Must be one of {VALID_SEVERITIES}")
    if priority not in VALID_PRIORITIES:
        conn.close()
        raise ValueError(f"Invalid priority '{priority}'. Must be one of {VALID_PRIORITIES}")
    if defect_type not in VALID_DEFECT_TYPES:
        conn.close()
        raise ValueError(f"Invalid defect type '{defect_type}'. Must be one of {VALID_DEFECT_TYPES}")
    if environment not in VALID_ENVIRONMENTS:
        conn.close()
        raise ValueError(f"Invalid environment '{environment}'.")

    defect_code = generate_next_defect_code(db_path)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    initial_status = "ASSIGNED" if assigned_to_id else "NEW"

    try:
        cursor.execute("""
            INSERT INTO defects (
                defect_code, project_name, module, title, description,
                steps_to_reproduce, expected_result, actual_result,
                defect_type, severity, priority, environment,
                screenshot_path, reporter_id, assigned_to_id,
                status, resolution_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            defect_code, project_name.strip(), module.strip(), title.strip(), description.strip(),
            steps_to_reproduce.strip() if steps_to_reproduce else "",
            expected_result.strip() if expected_result else "",
            actual_result.strip() if actual_result else "",
            defect_type, severity, priority, environment,
            screenshot_path, reporter_id, assigned_to_id,
            initial_status, None, now_str, now_str
        ))
        defect_id = cursor.lastrowid

        # Record Discovery in History
        cursor.execute("""
            INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (defect_id, "NONE", "NEW", reporter_id, "Defect discovered and logged into system.", now_str))

        if assigned_to_id:
            cursor.execute("""
                INSERT INTO assignments (defect_id, assigned_by_id, assigned_to_id, assigned_at, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (defect_id, reporter_id, assigned_to_id, now_str, "Initial assignment on defect discovery."))
            
            cursor.execute("""
                INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (defect_id, "NEW", "ASSIGNED", reporter_id, "Assigned upon creation.", now_str))

        conn.commit()
        return defect_id, defect_code
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def assign_defect(
    defect_id: int,
    assigned_to_id: int,
    assigned_by_id: int,
    notes: Optional[str] = None,
    assigned_by_role: Optional[str] = None,
    db_path: str = None
) -> bool:
    """Assign or reassign defect to a developer, updating status and history. Enforces Admin authorization."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Verify assigner role is Admin
    role = assigned_by_role
    if not role:
        cursor.execute("SELECT role FROM users WHERE id = ?", (assigned_by_id,))
        u = cursor.fetchone()
        role = u["role"] if u else None

    if role != "Admin":
        conn.close()
        raise PermissionError("Only Admins can assign or reassign defects.")

    cursor.execute("SELECT status, assigned_to_id FROM defects WHERE id = ?", (defect_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Defect ID {defect_id} not found.")

    current_status = row["status"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # If currently NEW, transition to ASSIGNED
    new_status = "ASSIGNED" if current_status == "NEW" else current_status

    try:
        cursor.execute("""
            UPDATE defects
            SET assigned_to_id = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (assigned_to_id, new_status, now_str, defect_id))

        cursor.execute("""
            INSERT INTO assignments (defect_id, assigned_by_id, assigned_to_id, assigned_at, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (defect_id, assigned_by_id, assigned_to_id, now_str, notes or "Defect assigned."))

        cursor.execute("""
            INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (defect_id, current_status, new_status, assigned_by_id, f"Assigned to user ID {assigned_to_id}. {notes or ''}".strip(), now_str))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_defect_status(
    defect_id: int,
    new_status: str,
    changed_by_id: int,
    comments: Optional[str] = None,
    resolution_notes: Optional[str] = None,
    user_role: Optional[str] = None,
    db_path: str = None
) -> bool:
    """Update defect status with strict lifecycle validation and audit history."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT status, resolution_notes, assigned_to_id FROM defects WHERE id = ?", (defect_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Defect with ID {defect_id} not found.")

    current_status = row["status"]

    if current_status == new_status:
        conn.close()
        return True  # No state change needed

    allowed = VALID_TRANSITIONS.get(current_status, [])
    # Check lifecycle transition
    if new_status not in allowed:
        conn.close()
        raise ValueError(
            f"Invalid lifecycle transition: '{current_status}' -> '{new_status}'. "
            f"Allowed next stages: {', '.join(allowed) if allowed else 'None (Terminal state)'}"
        )

    # Determine user role from DB if not passed
    role = user_role
    if not role:
        cursor.execute("SELECT role FROM users WHERE id = ?", (changed_by_id,))
        u = cursor.fetchone()
        role = u["role"] if u else "Admin"

    # Check role permissions for specific transitions
    if role == "Developer":
        # 1. Developers can only update defects assigned to them!
        if row["assigned_to_id"] != changed_by_id:
            conn.close()
            raise PermissionError("Developers can only modify defects assigned to them.")

        # 2. Developers can only transition to IN PROGRESS or FIXED
        if new_status not in ["IN PROGRESS", "FIXED"]:
            conn.close()
            raise PermissionError("Developers can only transition defects to 'IN PROGRESS' or 'FIXED'. Developers cannot close defects directly.")

    if role == "Tester" and new_status not in ["RETESTING", "CLOSED", "REOPENED"]:
        conn.close()
        raise PermissionError("Testers can only transition defects to 'RETESTING', 'CLOSED', or 'REOPENED'.")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_notes = resolution_notes if resolution_notes is not None else row["resolution_notes"]

    try:
        cursor.execute("""
            UPDATE defects
            SET status = ?, resolution_notes = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, updated_notes, now_str, defect_id))

        cursor.execute("""
            INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (defect_id, current_status, new_status, changed_by_id, comments or f"Status changed to {new_status}.", now_str))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_defect_classification(
    defect_id: int,
    severity: str,
    priority: str,
    defect_type: str,
    changed_by_id: int,
    comments: Optional[str] = None,
    user_role: Optional[str] = None,
    db_path: str = None
) -> bool:
    """Update defect classification parameters. Restricted to Admin and Tester."""
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}")
    if defect_type not in VALID_DEFECT_TYPES:
        raise ValueError(f"Invalid defect type: {defect_type}")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    role = user_role
    if not role:
        cursor.execute("SELECT role FROM users WHERE id = ?", (changed_by_id,))
        u = cursor.fetchone()
        role = u["role"] if u else "Admin"

    if role not in ("Admin", "Tester"):
        conn.close()
        raise PermissionError("Developers cannot modify defect classifications.")

    cursor.execute("SELECT severity, priority, defect_type, status FROM defects WHERE id = ?", (defect_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Defect {defect_id} not found.")

    old_sev = row["severity"]
    old_prio = row["priority"]
    old_type = row["defect_type"]
    current_status = row["status"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE defects
        SET severity = ?, priority = ?, defect_type = ?, updated_at = ?
        WHERE id = ?
    """, (severity, priority, defect_type, now_str, defect_id))

    audit_note = f"Reclassified from [{old_sev}, {old_prio}, {old_type}] to [{severity}, {priority}, {defect_type}]. {comments or ''}".strip()
    cursor.execute("""
        INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (defect_id, current_status, current_status, changed_by_id, audit_note, now_str))

    conn.commit()
    conn.close()
    return True


def get_defect_by_id(defect_id: int, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Retrieve complete defect record with reporter and assignee names."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, 
               u_rep.full_name as reporter_name, u_rep.username as reporter_username,
               u_dev.full_name as assignee_name, u_dev.username as assignee_username
        FROM defects d
        LEFT JOIN users u_rep ON d.reporter_id = u_rep.id
        LEFT JOIN users u_dev ON d.assigned_to_id = u_dev.id
        WHERE d.id = ?
    """, (defect_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_defect_by_code(defect_code: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Retrieve complete defect record by code (e.g. BUG-0001)."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, 
               u_rep.full_name as reporter_name, u_rep.username as reporter_username,
               u_dev.full_name as assignee_name, u_dev.username as assignee_username
        FROM defects d
        LEFT JOIN users u_rep ON d.reporter_id = u_rep.id
        LEFT JOIN users u_dev ON d.assigned_to_id = u_dev.id
        WHERE d.defect_code = ?
    """, (defect_code.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_defects(
    project_name: Optional[str] = None,
    module: Optional[str] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    reporter_id: Optional[int] = None,
    search_query: Optional[str] = None,
    db_path: str = None
) -> List[Dict[str, Any]]:
    """Query defects with dynamic filtering and full search capability."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = """
        SELECT d.*, 
               u_rep.full_name as reporter_name,
               u_dev.full_name as assignee_name
        FROM defects d
        LEFT JOIN users u_rep ON d.reporter_id = u_rep.id
        LEFT JOIN users u_dev ON d.assigned_to_id = u_dev.id
        WHERE 1=1
    """
    params = []

    if project_name and project_name != "All":
        query += " AND d.project_name = ?"
        params.append(project_name)

    if module and module != "All":
        query += " AND d.module = ?"
        params.append(module)

    if severity and severity != "All":
        query += " AND d.severity = ?"
        params.append(severity)

    if priority and priority != "All":
        query += " AND d.priority = ?"
        params.append(priority)

    if status and status != "All":
        query += " AND d.status = ?"
        params.append(status)

    if assigned_to_id is not None:
        query += " AND d.assigned_to_id = ?"
        params.append(assigned_to_id)

    if reporter_id is not None:
        query += " AND d.reporter_id = ?"
        params.append(reporter_id)

    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        query += " AND (d.defect_code LIKE ? OR d.title LIKE ? OR d.description LIKE ? OR d.module LIKE ?)"
        params.extend([q, q, q, q])

    query += " ORDER BY d.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_defect_history(defect_id: int, db_path: str = None) -> List[Dict[str, Any]]:
    """Retrieve full audit history for a defect."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.*, u.full_name as changed_by_name, u.role as changed_by_role
        FROM defect_history h
        LEFT JOIN users u ON h.changed_by_id = u.id
        WHERE h.defect_id = ?
        ORDER BY h.id ASC
    """, (defect_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unique_modules(db_path: str = None) -> List[str]:
    """Return sorted list of unique modules found in defects or predefined list."""
    predefined = [
        "Login & Authentication",
        "Payment Gateway",
        "Shopping Cart",
        "User Profile",
        "Order Processing",
        "Database Sync",
        "Report Generator",
        "Notification Service"
    ]
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT module FROM defects WHERE module IS NOT NULL AND module != ''")
    rows = cursor.fetchall()
    conn.close()

    existing = [r["module"] for r in rows]
    combined = sorted(list(set(predefined + existing)))
    return combined


def get_unique_projects(db_path: str = None) -> List[str]:
    """Return sorted list of project names."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM projects ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return [r["name"] for r in rows]
    return ["E-Commerce Web Portal", "Mobile Banking App", "Healthcare Records System"]

