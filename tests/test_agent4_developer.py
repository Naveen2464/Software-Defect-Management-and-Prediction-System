"""
tests/test_agent4_developer.py - Dedicated Test Suite for AGENT 4: DEVELOPER ROLE SPECIALIST.
Verifies Developer permissions (8 pages), personal workload filtering, lifecycle transitions
(IN PROGRESS, FIXED), resolution notes, and strict rejection of unauthorized operations.
"""

import os
import tempfile
import pytest
import database
import auth
import defect_management as dm


@pytest.fixture
def dev_db():
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


def test_developer_authentication_and_identity(dev_db):
    """Verify Developer login credentials and role profile."""
    user = auth.verify_user("dev1", "dev123", db_path=dev_db)
    assert user is not None, "Developer login failed"
    assert user["username"] == "dev1"
    assert user["role"] == "Developer"
    assert user["full_name"].startswith("David Kim")


def test_developer_allowed_navigation_pages(dev_db):
    """Verify Developer has exactly 8 allowed pages; Report New Defect, Assign Defects, User Management must be excluded."""
    dev1 = auth.get_user_by_username("dev1", db_path=dev_db)
    allowed = auth.get_allowed_pages(dev1)
    assert len(allowed) == 8, f"Expected 8 pages for Developer, found {len(allowed)}"

    # Required pages
    assert "Dashboard" in allowed
    assert "All Defects" in allowed
    assert "Defect Classification" in allowed
    assert "Resolution Management" in allowed
    assert "Defect Prevention" in allowed
    assert "Defect Prediction" in allowed
    assert "Analytics & Reports" in allowed
    assert "About Project" in allowed

    # Strictly restricted pages
    assert "Report New Defect" not in allowed
    assert "Assign Defects" not in allowed
    assert "User Management" not in allowed

    # UI Permission checks
    assert auth.can_view_page(dev1, "Report New Defect") is False
    assert auth.can_view_page(dev1, "Assign Defects") is False
    assert auth.can_view_page(dev1, "User Management") is False
    assert auth.can_view_page(dev1, "Resolution Management") is True


def test_developer_only_sees_assigned_defects(dev_db):
    """Verify Developer query returns only defects assigned to their user ID."""
    dev1 = auth.get_user_by_username("dev1", db_path=dev_db)
    dev2 = auth.get_user_by_username("dev2", db_path=dev_db)

    # Fetch defects for dev1
    dev1_defects = dm.get_all_defects(assigned_to_id=dev1["id"], db_path=dev_db)
    assert len(dev1_defects) > 0

    # Ensure every single defect is assigned to dev1
    for d in dev1_defects:
        assert d["assigned_to_id"] == dev1["id"]
        assert d["assigned_to_id"] != dev2["id"]


def test_developer_lifecycle_in_progress_and_fixed(dev_db):
    """Verify Developer can transition assigned defect to IN PROGRESS and then FIXED with notes."""
    dev1 = auth.get_user_by_username("dev1", db_path=dev_db)

    # Find a defect assigned to dev1 or assign one
    conn = database.get_connection(dev_db)
    conn.execute("UPDATE defects SET status = 'ASSIGNED', assigned_to_id = ? WHERE id = 1", (dev1["id"],))
    conn.commit()
    conn.close()

    # Step 1: Advance to IN PROGRESS
    s1 = dm.update_defect_status(
        defect_id=1,
        new_status="IN PROGRESS",
        changed_by_id=dev1["id"],
        user_role=dev1["role"],
        comments="Started investigating root cause in auth service",
        db_path=dev_db
    )
    assert s1 is True
    d1 = dm.get_defect_by_id(1, db_path=dev_db)
    assert d1["status"] == "IN PROGRESS"

    # Step 2: Advance to FIXED with resolution description
    s2 = dm.update_defect_status(
        defect_id=1,
        new_status="FIXED",
        changed_by_id=dev1["id"],
        user_role=dev1["role"],
        comments="Fixed null check in token validation pipeline",
        resolution_notes="Added guard clause preventing null pointer exception. Commit SHA: e4f89a2",
        db_path=dev_db
    )
    assert s2 is True
    d2 = dm.get_defect_by_id(1, db_path=dev_db)
    assert d2["status"] == "FIXED"
    assert "e4f89a2" in d2["resolution_notes"]


def test_developer_cannot_close_defect_directly(dev_db):
    """Verify Developer CANNOT advance a defect to CLOSED."""
    dev1 = auth.get_user_by_username("dev1", db_path=dev_db)

    # Set defect to FIXED
    conn = database.get_connection(dev_db)
    conn.execute("UPDATE defects SET status = 'FIXED', assigned_to_id = ? WHERE id = 1", (dev1["id"],))
    conn.commit()
    conn.close()

    # Developer tries to mark CLOSED -> Rejected
    with pytest.raises(Exception):
        dm.update_defect_status(
            defect_id=1,
            new_status="CLOSED",
            changed_by_id=dev1["id"],
            user_role=dev1["role"],
            comments="Attempting direct closure",
            db_path=dev_db
        )


def test_developer_cannot_modify_another_developers_defect(dev_db):
    """Verify Developer CANNOT modify a defect assigned to a different developer."""
    dev1 = auth.get_user_by_username("dev1", db_path=dev_db)
    dev2 = auth.get_user_by_username("dev2", db_path=dev_db)

    # Assign defect 2 to dev2
    conn = database.get_connection(dev_db)
    conn.execute("UPDATE defects SET status = 'ASSIGNED', assigned_to_id = ? WHERE id = 2", (dev2["id"],))
    conn.commit()
    conn.close()

    # dev1 attempts to modify dev2's defect -> PermissionError
    with pytest.raises(PermissionError) as exc_info:
        dm.update_defect_status(
            defect_id=2,
            new_status="IN PROGRESS",
            changed_by_id=dev1["id"],
            user_role=dev1["role"],
            comments="Unauthorized attempt to modify colleague's defect",
            db_path=dev_db
        )
    assert "Developers can only modify defects assigned to them" in str(exc_info.value)


def test_developer_unauthorized_backend_operations_rejected(dev_db):
    """Verify Developer CANNOT report defects, reclassify defects, assign defects, or manage users."""
    dev1 = auth.get_user_by_username("dev1", db_path=dev_db)

    # 1. Developer cannot report defect
    with pytest.raises(PermissionError) as exc_info:
        dm.create_defect(
            project_name="Core ERP",
            module="Billing",
            title="Dev unauthorized defect",
            description="Dev trying to report",
            steps_to_reproduce="N/A",
            expected_result="N/A",
            actual_result="N/A",
            defect_type="Functional",
            severity="Low",
            priority="P4 - Low",
            environment="Development",
            reporter_id=dev1["id"],
            reporter_role=dev1["role"],
            db_path=dev_db
        )
    assert "Developers are not permitted to report new defects" in str(exc_info.value)

    # 2. Developer cannot reclassify defect
    with pytest.raises(PermissionError) as exc_info:
        dm.update_defect_classification(
            defect_id=1,
            severity="Critical",
            priority="P1 - Urgent",
            defect_type="Security",
            changed_by_id=dev1["id"],
            user_role=dev1["role"],
            db_path=dev_db
        )
    assert "Developers cannot modify defect classifications" in str(exc_info.value)

    # 3. Developer cannot assign defects
    with pytest.raises(PermissionError) as exc_info:
        dm.assign_defect(
            defect_id=1,
            assigned_to_id=dev1["id"],
            assigned_by_id=dev1["id"],
            assigned_by_role=dev1["role"],
            db_path=dev_db
        )
    assert "Only Admins can assign" in str(exc_info.value)

    # 4. Developer cannot create users
    with pytest.raises(PermissionError) as exc_info:
        auth.create_user(
            username="dev_created_user",
            password="password123",
            full_name="Dev User",
            email="devuser@defects.io",
            role="Tester",
            creator_role=dev1["role"],
            db_path=dev_db
        )
    assert "Only Admins can register new users" in str(exc_info.value)
