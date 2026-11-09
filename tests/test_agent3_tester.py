"""
tests/test_agent3_tester.py - Dedicated Test Suite for AGENT 3: TESTER ROLE SPECIALIST.
Verifies Tester permissions (9 pages), defect submission, automatic ID generation,
screenshot attachments, retesting, closing, reopening, and rejection of unauthorized operations.
"""

import os
import tempfile
import pytest
import database
import auth
import defect_management as dm


@pytest.fixture
def tester_db():
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


def test_tester_authentication_and_identity(tester_db):
    """Verify Tester login credentials, profile, and role badge configuration."""
    user = auth.verify_user("tester", "tester123", db_path=tester_db)
    assert user is not None, "Tester login failed"
    assert user["username"] == "tester"
    assert user["role"] == "Tester"
    assert user["full_name"].startswith("Alex Rivera")


def test_tester_allowed_navigation_pages(tester_db):
    """Verify Tester has exactly 9 allowed pages; Assign Defects and User Management must be excluded."""
    tester = auth.get_user_by_username("tester", db_path=tester_db)
    allowed = auth.get_allowed_pages(tester)
    assert len(allowed) == 9, f"Expected 9 pages for Tester, found {len(allowed)}"

    # Required pages
    assert "Dashboard" in allowed
    assert "Report New Defect" in allowed
    assert "All Defects" in allowed
    assert "Defect Classification" in allowed
    assert "Resolution Management" in allowed
    assert "Defect Prevention" in allowed
    assert "Defect Prediction" in allowed
    assert "Analytics & Reports" in allowed
    assert "About Project" in allowed

    # Strictly restricted pages
    assert "Assign Defects" not in allowed
    assert "User Management" not in allowed

    # UI Permission checks
    assert auth.can_view_page(tester, "Assign Defects") is False
    assert auth.can_view_page(tester, "User Management") is False
    assert auth.can_view_page(tester, "Report New Defect") is True


def test_tester_defect_submission_and_auto_id_generation(tester_db):
    """Verify Tester can submit a defect and receive a sequential unique defect ID."""
    tester = auth.get_user_by_username("tester", db_path=tester_db)
    
    # Pre-check current count
    all_defs = dm.get_all_defects(db_path=tester_db)
    initial_count = len(all_defs)

    defect_id, defect_code = dm.create_defect(
        project_name="E-Commerce Web Portal",
        module="Shopping Cart",
        title="Coupon discount applied twice during checkout",
        description="Entering promo code 'SPRING20' applies 20% discount twice on subtotal",
        steps_to_reproduce="1. Add item ($100)\n2. Apply promo 'SPRING20'\n3. Observe final price $64 instead of $80",
        expected_result="Single 20% discount applied ($80)",
        actual_result="Discount applied exponentially ($64)",
        defect_type="Functional",
        severity="High",
        priority="P2 - High",
        environment="QA / Test",
        reporter_id=tester["id"],
        reporter_role=tester["role"],
        db_path=tester_db
    )

    assert defect_id > 0
    assert defect_code.startswith("BUG-")
    assert defect_code == f"BUG-{initial_count + 1:04d}"

    record = dm.get_defect_by_code(defect_code, db_path=tester_db)
    assert record["reporter_name"] == tester["full_name"]
    assert record["module"] == "Shopping Cart"
    assert record["severity"] == "High"


def test_tester_screenshot_attachment_handling(tester_db):
    """Verify Tester can attach screenshot paths and they persist in the defect record."""
    tester = auth.get_user_by_username("tester", db_path=tester_db)
    
    fake_screenshot = os.path.join("uploads", "test_screenshot_evidence.png")
    
    defect_id, defect_code = dm.create_defect(
        project_name="Inventory ERP",
        module="Inventory Sync",
        title="Negative inventory count allowed on bulk import",
        description="CSV upload allows quantities < 0 without validation failure",
        steps_to_reproduce="Upload inventory.csv with quantity -50",
        expected_result="Row rejected with validation error",
        actual_result="Negative stock recorded in DB",
        defect_type="Functional",
        severity="Medium",
        priority="P3 - Normal",
        environment="QA / Test",
        reporter_id=tester["id"],
        reporter_role=tester["role"],
        screenshot_path=fake_screenshot,
        db_path=tester_db
    )

    record = dm.get_defect_by_id(defect_id, db_path=tester_db)
    assert record["screenshot_path"] == fake_screenshot


def test_tester_retest_and_close_workflow(tester_db):
    """Verify Tester can transition a defect from FIXED to RETESTING and then CLOSED."""
    tester = auth.get_user_by_username("tester", db_path=tester_db)
    dev1 = auth.get_user_by_username("dev1", db_path=tester_db)

    # Prepare defect in FIXED status
    conn = database.get_connection(tester_db)
    conn.execute("UPDATE defects SET status = 'FIXED', assigned_to_id = ? WHERE id = 1", (dev1["id"],))
    conn.commit()
    conn.close()

    # Step 1: Tester advances FIXED -> RETESTING
    s1 = dm.update_defect_status(
        defect_id=1,
        new_status="RETESTING",
        changed_by_id=tester["id"],
        user_role=tester["role"],
        comments="Deploying to QA testbed for regression verification",
        db_path=tester_db
    )
    assert s1 is True
    d1 = dm.get_defect_by_id(1, db_path=tester_db)
    assert d1["status"] == "RETESTING"

    # Step 2: Tester advances RETESTING -> CLOSED
    s2 = dm.update_defect_status(
        defect_id=1,
        new_status="CLOSED",
        changed_by_id=tester["id"],
        user_role=tester["role"],
        comments="Regression passed across 15 automated test runs. Ready for production release.",
        db_path=tester_db
    )
    assert s2 is True
    d2 = dm.get_defect_by_id(1, db_path=tester_db)
    assert d2["status"] == "CLOSED"


def test_tester_reopen_on_failed_retest(tester_db):
    """Verify Tester can transition a defect from RETESTING to REOPENED when test fails."""
    tester = auth.get_user_by_username("tester", db_path=tester_db)
    dev1 = auth.get_user_by_username("dev1", db_path=tester_db)

    # Prepare defect in RETESTING status
    conn = database.get_connection(tester_db)
    conn.execute("UPDATE defects SET status = 'RETESTING', assigned_to_id = ? WHERE id = 2", (dev1["id"],))
    conn.commit()
    conn.close()

    # Retest fails -> REOPENED
    s = dm.update_defect_status(
        defect_id=2,
        new_status="REOPENED",
        changed_by_id=tester["id"],
        user_role=tester["role"],
        comments="Verification failed: Bug still reproduces when request payload exceeds 5MB.",
        db_path=tester_db
    )
    assert s is True
    d = dm.get_defect_by_id(2, db_path=tester_db)
    assert d["status"] == "REOPENED"


def test_tester_unauthorized_backend_operations_rejected(tester_db):
    """Verify Tester CANNOT assign developers or perform user management operations."""
    tester = auth.get_user_by_username("tester", db_path=tester_db)
    dev1 = auth.get_user_by_username("dev1", db_path=tester_db)

    # 1. Tester cannot assign developers
    with pytest.raises(PermissionError) as exc_info:
        dm.assign_defect(
            defect_id=1,
            assigned_to_id=dev1["id"],
            assigned_by_id=tester["id"],
            assigned_by_role=tester["role"],
            db_path=tester_db
        )
    assert "Only Admins can assign" in str(exc_info.value)

    # 2. Tester cannot provision users
    with pytest.raises(PermissionError) as exc_info:
        auth.create_user(
            username="unauth_tester_created",
            password="password123",
            full_name="Unauthorized User",
            email="unauth@defects.io",
            role="Developer",
            creator_role=tester["role"],
            db_path=tester_db
        )
    assert "Only Admins can register new users" in str(exc_info.value)

    # 3. Tester cannot modify user roles
    with pytest.raises(PermissionError) as exc_info:
        auth.update_user_role(
            user_id=dev1["id"],
            new_role="Admin",
            creator_role=tester["role"],
            db_path=tester_db
        )
    assert "Only Admins can modify user roles" in str(exc_info.value)

    # 4. Tester cannot assign developer directly upon defect creation
    with pytest.raises(PermissionError) as exc_info:
        dm.create_defect(
            project_name="Core ERP",
            module="Authentication",
            title="Tester direct assignment test",
            description="Tester trying to assign dev on create",
            steps_to_reproduce="N/A",
            expected_result="N/A",
            actual_result="N/A",
            defect_type="Functional",
            severity="Low",
            priority="P4 - Low",
            environment="QA / Test",
            reporter_id=tester["id"],
            reporter_role=tester["role"],
            assigned_to_id=dev1["id"],
            db_path=tester_db
        )
    assert "Only Administrators can assign defects upon creation" in str(exc_info.value)
