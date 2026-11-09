"""
auth.py - Authentication and Role-Based Access Control (RBAC).
Provides user authentication, role management, and authorization checks.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from database import get_connection, hash_password


def verify_user(username: str, password: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Verify user credentials and return user dictionary if valid."""
    if not username or not password:
        return None

    hashed = hash_password(password)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, email, role, created_at
        FROM users
        WHERE username = ? AND password_hash = ?
    """, (username.strip(), hashed))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def get_user_by_id(user_id: int, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Retrieve user details by user ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, email, role, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Retrieve user details by username."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, email, role, created_at
        FROM users
        WHERE username = ?
    """, (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users(role: str = None, db_path: str = None) -> List[Dict[str, Any]]:
    """Retrieve all users, optionally filtered by role."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    if role:
        cursor.execute("""
            SELECT id, username, full_name, email, role, created_at
            FROM users
            WHERE role = ?
            ORDER BY full_name ASC
        """, (role,))
    else:
        cursor.execute("""
            SELECT id, username, full_name, email, role, created_at
            FROM users
            ORDER BY role ASC, full_name ASC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Permitted Navigation Pages by Role
ROLE_PAGES = {
    "Admin": [
        "Dashboard",
        "Report New Defect",
        "All Defects",
        "Defect Classification",
        "Assign Defects",
        "Resolution Management",
        "Defect Prevention",
        "Defect Prediction",
        "Analytics & Reports",
        "User Management",
        "About Project"
    ],
    "Tester": [
        "Dashboard",
        "Report New Defect",
        "All Defects",
        "Defect Classification",
        "Resolution Management",
        "Defect Prevention",
        "Defect Prediction",
        "Analytics & Reports",
        "About Project"
    ],
    "Developer": [
        "Dashboard",
        "All Defects",
        "Defect Classification",
        "Resolution Management",
        "Defect Prevention",
        "Defect Prediction",
        "Analytics & Reports",
        "About Project"
    ]
}

PAGE_ICONS = {
    "Dashboard": "📊",
    "Report New Defect": "🐞",
    "All Defects": "🗂️",
    "Defect Classification": "🏷️",
    "Assign Defects": "👥",
    "Resolution Management": "🔄",
    "Defect Prevention": "🛡️",
    "Defect Prediction": "🔮",
    "Analytics & Reports": "📈",
    "User Management": "👤",
    "About Project": "ℹ️"
}

ROLE_BADGE_CONFIG = {
    "Admin": {
        "label": "Admin",
        "class": "role-badge-admin",
        "color": "#7c3aed"
    },
    "Tester": {
        "label": "Tester",
        "class": "role-badge-tester",
        "color": "#2563eb"
    },
    "Developer": {
        "label": "Developer",
        "class": "role-badge-developer",
        "color": "#059669"
    }
}

DEMO_ACCOUNTS = ["admin", "tester", "tester2", "dev1", "dev2", "dev3"]


def get_allowed_pages(user: Optional[Dict[str, Any]]) -> List[str]:
    """Return permitted navigation pages for the user's role."""
    if not user:
        return []
    role = user.get("role", "")
    return ROLE_PAGES.get(role, [])


def can_view_page(user: Optional[Dict[str, Any]], page_name: str) -> bool:
    """Centralized authorization check for viewing a specific navigation page."""
    if not user:
        return False
    allowed = get_allowed_pages(user)
    # Match bare page name
    clean = page_name
    for p in allowed:
        if clean == p or clean.endswith(p):
            return True
    return False


def can_modify_defect(user: Optional[Dict[str, Any]], defect: Dict[str, Any]) -> bool:
    """Verify if user has permission to modify a specific defect."""
    if not user or not defect:
        return False
    role = user.get("role")
    if role == "Admin":
        return True
    if role == "Developer":
        # Developers can only modify defects assigned to them
        return defect.get("assigned_to_id") == user.get("id")
    if role == "Tester":
        return True
    return False


def create_user(
    username: str,
    password: str,
    full_name: str,
    email: str,
    role: str,
    creator_role: str = "Admin",
    db_path: str = None
) -> int:
    """Register a new user in the system. Enforces Admin authorization."""
    if creator_role != "Admin":
        raise PermissionError("Only Admins can register new users.")

    if not username or not password or not full_name or not email or not role:
        raise ValueError("All fields are required to create a user.")

    role = role.strip()
    if role not in ('Admin', 'Tester', 'Developer'):
        raise ValueError(f"Invalid role '{role}'. Must be Admin, Tester, or Developer.")

    hashed = hash_password(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username.strip(), hashed, full_name.strip(), email.strip(), role, created_at))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_user_role(
    user_id: int,
    new_role: str,
    creator_role: str = "Admin",
    db_path: str = None
) -> bool:
    """Update role for an existing user. Enforces Admin authorization."""
    if creator_role != "Admin":
        raise PermissionError("Only Admins can modify user roles.")

    if new_role not in ('Admin', 'Tester', 'Developer'):
        raise ValueError("Invalid role specified.")

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# Authorization Helpers
def can_report_defects(user: Optional[Dict[str, Any]]) -> bool:
    """Testers and Admins can report new defects."""
    return user and user.get("role") in ("Admin", "Tester")


def can_assign_defects(user: Optional[Dict[str, Any]]) -> bool:
    """Only Admins can assign defects to developers."""
    return user and user.get("role") == "Admin"


def can_change_priority_severity(user: Optional[Dict[str, Any]]) -> bool:
    """Admins and Testers can update priority/severity classification."""
    return user and user.get("role") in ("Admin", "Tester")


def can_update_resolution(user: Optional[Dict[str, Any]]) -> bool:
    """Developers and Admins can update defect resolution."""
    return user and user.get("role") in ("Admin", "Developer")


def can_retest_and_close(user: Optional[Dict[str, Any]]) -> bool:
    """Testers and Admins can retest, close, or reopen defects."""
    return user and user.get("role") in ("Admin", "Tester")


def can_manage_users(user: Optional[Dict[str, Any]]) -> bool:
    """Only Admins can register new users and manage accounts."""
    return user and user.get("role") == "Admin"


