"""
tests/test_rbac.py - Comprehensive Role-Based Access Control (RBAC) Test Suite.
Validates permissions for Admin, Tester, and Developer across all 11 modules and workflows.
"""

import os
import tempfile
import pytest
import database
import auth
import defect_management as dm


@pytest.fixture
def rbac_db():
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


def test_admin_has_access_to_all_11_pages(rbac_db):
    admin = auth.get_user_by_username("admin", db_path=rbac_db)
    assert admin is not None
    allowed = auth.get_allowed_pages(admin)
    assert len(allowed) == 11
    expected_pages = [
        "Dashboard", "Report New Defect", "All Defects", "Defect Classification",
        "Assign Defects", "Resolution Management", "Defect Prevention",
        "Defect Prediction", "Analytics & Reports", "User Management", "About Project"
    ]
    assert allowed == expected_pages
    for page in expected_pages:
        assert auth.can_view_page(admin, page) is True


def test_tester_page_permissions(rbac_db):
    tester = auth.get_user_by_username("tester", db_path=rbac_db)
    assert tester is not None
    allowed = auth.get_allowed_pages(tester)
    assert len(allowed) == 9
    assert "Assign Defects" not in allowed
    assert "User Management" not in allowed
    assert auth.can_view_page(tester, "Assign Defects") is False
    assert auth.can_view_page(tester, "User Management") is False
    assert auth.can_view_page(tester, "Dashboard") is True
    assert auth.can_view_page(tester, "Report New Defect") is True
    assert auth.can_view_page(tester, "Resolution Management") is True


def test_developer_page_permissions(rbac_db):
    dev = auth.get_user_by_username("dev1", db_path=rbac_db)
    assert dev is not None
    allowed = auth.get_allowed_pages(dev)
    assert len(allowed) == 8
    assert "Report New Defect" not in allowed
    assert "Assign Defects" not in allowed
    assert "User Management" not in allowed
    assert auth.can_view_page(dev, "Report New Defect") is False
    assert auth.can_view_page(dev, "Assign Defects") is False
    assert auth.can_view_page(dev, "User Management") is False
    assert auth.can_view_page(dev, "Dashboard") is True
    assert auth.can_view_page(dev, "All Defects") is True
    assert auth.can_view_page(dev, "Resolution Management") is True


def test_developer_can_only_modify_assigned_defects(rbac_db):
    dev1 = auth.get_user_by_username("dev1", db_path=rbac_db)
    dev2 = auth.get_user_by_username("dev2", db_path=rbac_db)

    # Create defect assigned to dev1
    defect_id, code = dm.create_defect(
        project_name="Core ERP",
        module="Authentication",
        title="Session crash on logout",
        description="Logout causes 500 error",
        steps_to_reproduce="Click logout",
        expected_result="Redirect to login",
        actual_result="500 crash",
        defect_type="Functional",
        severity="High",
        priority="P2 - High",
        environment="QA / Test",
        reporter_id=1,
        assigned_to_id=dev1["id"],
        reporter_role="Admin",
        db_path=rbac_db
    )

    # dev1 can update their assigned defect
    success = dm.update_defect_status(
        defect_id=defect_id,
        new_status="IN PROGRESS",
        changed_by_id=dev1["id"],
        user_role="Developer",
        comments="Started investigating",
        db_path=rbac_db
    )
    assert success is True

    # dev2 CANNOT update dev1's defect
    with pytest.raises(PermissionError) as exc_info:
        dm.update_defect_status(
            defect_id=defect_id,
            new_status="FIXED",
            changed_by_id=dev2["id"],
            user_role="Developer",
            comments="Unauthorized attempt",
            db_path=rbac_db
        )
    assert "Developers can only modify defects assigned to them" in str(exc_info.value)


def test_developer_cannot_close_defects(rbac_db):
    dev1 = auth.get_user_by_username("dev1", db_path=rbac_db)
    defect = dm.get_defect_by_code("BUG-0002", db_path=rbac_db)
    
    # Ensure defect is assigned to dev1
    dm.assign_defect(
        defect_id=defect["id"],
        assigned_to_id=dev1["id"],
        assigned_by_id=1,
        assigned_by_role="Admin",
        db_path=rbac_db
    )

    # Move to IN PROGRESS
    dm.update_defect_status(defect["id"], "IN PROGRESS", dev1["id"], user_role="Developer", db_path=rbac_db)
    # Move to FIXED
    dm.update_defect_status(defect["id"], "FIXED", dev1["id"], user_role="Developer", comments="Code fixed", db_path=rbac_db)

    # Developer attempts to directly CLOSE -> must be rejected
    with pytest.raises(ValueError):
        # State machine does not allow FIXED -> CLOSED directly
        dm.update_defect_status(defect["id"], "CLOSED", dev1["id"], user_role="Developer", db_path=rbac_db)

    # Even from RETESTING, a developer cannot close
    # Simulate move to RETESTING by tester
    tester = auth.get_user_by_username("tester", db_path=rbac_db)
    dm.update_defect_status(defect["id"], "RETESTING", tester["id"], user_role="Tester", db_path=rbac_db)

    with pytest.raises(PermissionError) as exc_info:
        dm.update_defect_status(defect["id"], "CLOSED", dev1["id"], user_role="Developer", db_path=rbac_db)
    assert "Developers cannot close defects directly" in str(exc_info.value)


def test_tester_retest_and_close_lifecycle(rbac_db):
    tester = auth.get_user_by_username("tester", db_path=rbac_db)
    dev1 = auth.get_user_by_username("dev1", db_path=rbac_db)
    defect = dm.get_defect_by_code("BUG-0005", db_path=rbac_db)

    # Set defect to FIXED
    conn = database.get_connection(rbac_db)
    conn.execute("UPDATE defects SET status = 'FIXED', assigned_to_id = ? WHERE id = ?", (dev1["id"], defect["id"]))
    conn.commit()
    conn.close()

    # Tester transitions FIXED -> RETESTING
    s1 = dm.update_defect_status(
        defect_id=defect["id"],
        new_status="RETESTING",
        changed_by_id=tester["id"],
        user_role="Tester",
        comments="Validating fix in QA staging build",
        db_path=rbac_db
    )
    assert s1 is True

    # Tester transitions RETESTING -> CLOSED
    s2 = dm.update_defect_status(
        defect_id=defect["id"],
        new_status="CLOSED",
        changed_by_id=tester["id"],
        user_role="Tester",
        comments="Verification passed on build 2.4.1",
        db_path=rbac_db
    )
    assert s2 is True

    updated = dm.get_defect_by_id(defect["id"], db_path=rbac_db)
    assert updated["status"] == "CLOSED"


def test_tester_reopen_on_failed_retest(rbac_db):
    tester = auth.get_user_by_username("tester", db_path=rbac_db)
    dev1 = auth.get_user_by_username("dev1", db_path=rbac_db)
    defect = dm.get_defect_by_code("BUG-0004", db_path=rbac_db)

    # Set to RETESTING
    conn = database.get_connection(rbac_db)
    conn.execute("UPDATE defects SET status = 'RETESTING', assigned_to_id = ? WHERE id = ?", (dev1["id"], defect["id"]))
    conn.commit()
    conn.close()

    # Tester reopens due to failure
    s = dm.update_defect_status(
        defect_id=defect["id"],
        new_status="REOPENED",
        changed_by_id=tester["id"],
        user_role="Tester",
        comments="Bug still reproduces when payload > 10MB",
        db_path=rbac_db
    )
    assert s is True
    updated = dm.get_defect_by_id(defect["id"], db_path=rbac_db)
    assert updated["status"] == "REOPENED"


def test_backend_unauthorized_operations_rejected(rbac_db):
    tester = auth.get_user_by_username("tester", db_path=rbac_db)
    dev1 = auth.get_user_by_username("dev1", db_path=rbac_db)

    # 1. Tester cannot assign defects
    with pytest.raises(PermissionError) as exc_info:
        dm.assign_defect(
            defect_id=1,
            assigned_to_id=dev1["id"],
            assigned_by_id=tester["id"],
            assigned_by_role="Tester",
            db_path=rbac_db
        )
    assert "Only Admins can assign" in str(exc_info.value)

    # 2. Developer cannot report new defects
    with pytest.raises(PermissionError) as exc_info:
        dm.create_defect(
            project_name="Core ERP",
            module="Billing",
            title="Dev reporting test",
            description="Testing developer defect reporting restriction",
            steps_to_reproduce="N/A",
            expected_result="N/A",
            actual_result="N/A",
            defect_type="Functional",
            severity="Low",
            priority="P4 - Low",
            environment="Development",
            reporter_id=dev1["id"],
            reporter_role="Developer",
            db_path=rbac_db
        )
    assert "Developers are not permitted to report new defects" in str(exc_info.value)

    # 3. Developer cannot reclassify defects
    with pytest.raises(PermissionError) as exc_info:
        dm.update_defect_classification(
            defect_id=1,
            severity="Critical",
            priority="P1 - Urgent",
            defect_type="Security",
            changed_by_id=dev1["id"],
            user_role="Developer",
            db_path=rbac_db
        )
    assert "Developers cannot modify defect classifications" in str(exc_info.value)

    # 4. Non-admin cannot register users
    with pytest.raises(PermissionError) as exc_info:
        auth.create_user(
            username="unauth_user",
            password="password123",
            full_name="Unauthorized",
            email="unauth@defects.io",
            role="Tester",
            creator_role="Tester",
            db_path=rbac_db
        )
    assert "Only Admins can register new users" in str(exc_info.value)

    # 5. Non-admin cannot update user roles
    with pytest.raises(PermissionError) as exc_info:
        auth.update_user_role(
            user_id=dev1["id"],
            new_role="Admin",
            creator_role="Developer",
            db_path=rbac_db
        )
    assert "Only Admins can modify user roles" in str(exc_info.value)
