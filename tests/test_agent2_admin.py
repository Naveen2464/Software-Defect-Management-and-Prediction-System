"""
tests/test_agent2_admin.py - Dedicated Test Suite for AGENT 2: ADMIN TESTER.
Verifies all 11 navigation pages, defect creation, classification, assignment,
user provisioning, role modification, and full system oversight.
"""

import os
import tempfile
import pytest
import database
import auth
import defect_management as dm


@pytest.fixture
def admin_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.init_db(path)
    database.seed_sample_data(path, force=True)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def test_admin_authentication_and_identity(admin_db):
    """Verify Admin credentials, identity, and profile fields."""
    user = auth.verify_user("admin", "admin123", db_path=admin_db)
    assert user is not None, "Admin login verification failed"
    assert user["username"] == "admin"
    assert user["role"] == "Admin"
    assert user["full_name"].startswith("Sarah Jenkins")
    assert "@" in user["email"]


def test_admin_access_to_all_11_pages(admin_db):
    """Verify Admin has permissions to view exactly all 11 navigation pages."""
    admin = auth.get_user_by_username("admin", db_path=admin_db)
    allowed = auth.get_allowed_pages(admin)
    assert len(allowed) == 11, f"Expected 11 pages for Admin, found {len(allowed)}"
    
    expected_pages = [
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
    ]
    assert allowed == expected_pages
    for page in expected_pages:
        assert auth.can_view_page(admin, page) is True, f"Admin should have access to {page}"


def test_admin_defect_creation(admin_db):
    """Verify Admin can create and register a new defect with full metadata."""
    admin = auth.get_user_by_username("admin", db_path=admin_db)
    defect_id, defect_code = dm.create_defect(
        project_name="E-Commerce Web Portal",
        module="Payment Gateway",
        title="Admin reported gateway failure",
        description="Gateway timeout during high-volume flash sale",
        steps_to_reproduce="1. Trigger 500 checkout requests\n2. Observe gateway drop",
        expected_result="200 OK with queuing",
        actual_result="504 Gateway Timeout",
        defect_type="Performance",
        severity="Critical",
        priority="P1 - Urgent",
        environment="Production",
        reporter_id=admin["id"],
        reporter_role=admin["role"],
        db_path=admin_db
    )
    assert defect_id > 0
    assert defect_code.startswith("BUG-")
    
    record = dm.get_defect_by_id(defect_id, db_path=admin_db)
    assert record["title"] == "Admin reported gateway failure"
    assert record["reporter_id"] == admin["id"]
    assert record["severity"] == "Critical"
    assert record["status"] in ("NEW", "ASSIGNED")


def test_admin_defect_classification(admin_db):
    """Verify Admin can reclassify defect severity, priority, and defect type."""
    admin = auth.get_user_by_username("admin", db_path=admin_db)
    defect = dm.get_defect_by_code("BUG-0001", db_path=admin_db)
    assert defect is not None

    success = dm.update_defect_classification(
        defect_id=defect["id"],
        severity="Critical",
        priority="P1 - Urgent",
        defect_type="Security",
        changed_by_id=admin["id"],
        user_role=admin["role"],
        comments="Escalated to Critical/P1 due to security audit finding",
        db_path=admin_db
    )
    assert success is True

    updated = dm.get_defect_by_id(defect["id"], db_path=admin_db)
    assert updated["severity"] == "Critical"
    assert updated["priority"] == "P1 - Urgent"
    assert updated["defect_type"] == "Security"


def test_admin_developer_assignment(admin_db):
    """Verify Admin can assign an open defect to a developer."""
    admin = auth.get_user_by_username("admin", db_path=admin_db)
    dev1 = auth.get_user_by_username("dev1", db_path=admin_db)
    
    # Create a fresh NEW defect to assign
    defect_id, defect_code = dm.create_defect(
        project_name="E-Commerce Web Portal",
        module="Shopping Cart",
        title="Unassigned defect for testing triage",
        description="Testing triage assignment flow",
        steps_to_reproduce="N/A",
        expected_result="N/A",
        actual_result="N/A",
        defect_type="Functional",
        severity="Medium",
        priority="P3 - Normal",
        environment="QA / Test",
        reporter_id=admin["id"],
        reporter_role=admin["role"],
        db_path=admin_db
    )
    initial = dm.get_defect_by_id(defect_id, db_path=admin_db)
    assert initial["status"] == "NEW"

    success = dm.assign_defect(
        defect_id=defect_id,
        assigned_to_id=dev1["id"],
        assigned_by_id=admin["id"],
        assigned_by_role=admin["role"],
        notes="Urgent assignment: please investigate concurrency bottleneck.",
        db_path=admin_db
    )
    assert success is True

    updated = dm.get_defect_by_id(defect_id, db_path=admin_db)
    assert updated["assigned_to_id"] == dev1["id"]
    assert updated["assignee_name"] == dev1["full_name"]
    assert updated["status"] == "ASSIGNED"


def test_admin_user_management_provisioning(admin_db):
    """Verify Admin can create new user accounts and update existing roles."""
    admin = auth.get_user_by_username("admin", db_path=admin_db)
    
    # 1. Admin creates a new Tester user
    new_uid = auth.create_user(
        username="qa_lead_mark",
        password="securePassword123",
        full_name="Mark Robinson",
        email="mark.qa@defects.io",
        role="Tester",
        creator_role=admin["role"],
        db_path=admin_db
    )
    assert new_uid > 0
    created = auth.get_user_by_id(new_uid, db_path=admin_db)
    assert created["username"] == "qa_lead_mark"
    assert created["role"] == "Tester"

    # 2. Admin updates the user's role to Developer
    success = auth.update_user_role(
        user_id=new_uid,
        new_role="Developer",
        creator_role=admin["role"],
        db_path=admin_db
    )
    assert success is True
    updated = auth.get_user_by_id(new_uid, db_path=admin_db)
    assert updated["role"] == "Developer"


def test_admin_permission_helpers(admin_db):
    """Verify all centralized auth helper functions evaluate to True for Admin."""
    admin = auth.get_user_by_username("admin", db_path=admin_db)
    assert auth.can_report_defects(admin) is True
    assert auth.can_assign_defects(admin) is True
    assert auth.can_change_priority_severity(admin) is True
    assert auth.can_update_resolution(admin) is True
    assert auth.can_retest_and_close(admin) is True
    assert auth.can_manage_users(admin) is True
