"""
tests/test_defects.py - Automated tests for defect creation, ID generation, validation,
assignment, lifecycle state transitions, history logging, and reclassification.
"""

import os
import tempfile
import pytest
import database
import auth
import defect_management as dm
import analytics


@pytest.fixture
def populated_db():
    """Create a temporary database populated with sample data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.init_db(path)
    database.seed_sample_data(path, force=True)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_generate_next_defect_code(populated_db):
    """Verify that defect code generation increments sequentially."""
    next_code = dm.generate_next_defect_code(db_path=populated_db)
    assert next_code.startswith("BUG-")
    # Sample data has 16 defects, next should be BUG-0017
    assert next_code == "BUG-0017"


def test_create_defect_success(populated_db):
    """Verify successful defect creation, persistence, and audit logging."""
    tester = auth.get_user_by_username("tester", db_path=populated_db)
    assert tester is not None

    defect_id, code = dm.create_defect(
        project_name="E-Commerce Web Portal",
        module="Checkout",
        title="Coupon code discount not deducted from order total",
        description="Entering 'SAVE20' displays success banner but does not discount subtotal.",
        steps_to_reproduce="1. Add item\n2. Enter code SAVE20\n3. Click Apply",
        expected_result="20% deducted from total",
        actual_result="Total remains full price",
        defect_type="Functional",
        severity="High",
        priority="P2 - High",
        environment="QA / Test",
        reporter_id=tester["id"],
        db_path=populated_db
    )

    assert defect_id > 0
    assert code == "BUG-0017"

    # Verify retrieval
    defect = dm.get_defect_by_id(defect_id, db_path=populated_db)
    assert defect["defect_code"] == "BUG-0017"
    assert defect["status"] == "NEW"
    assert defect["module"] == "Checkout"
    assert defect["reporter_name"] == tester["full_name"]

    # Verify history entry created
    history = dm.get_defect_history(defect_id, db_path=populated_db)
    assert len(history) == 1
    assert history[0]["new_status"] == "NEW"


def test_create_defect_validation_errors(populated_db):
    """Verify input validation fails on empty fields or invalid choices."""
    tester = auth.get_user_by_username("tester", db_path=populated_db)

    # Empty title
    with pytest.raises(ValueError, match="title is required"):
        dm.create_defect(
            project_name="Portal", module="Auth", title="",
            description="desc", steps_to_reproduce="", expected_result="",
            actual_result="", defect_type="Functional", severity="High",
            priority="P1 - Urgent", environment="QA / Test", reporter_id=tester["id"],
            db_path=populated_db
        )

    # Invalid severity
    with pytest.raises(ValueError, match="Invalid severity"):
        dm.create_defect(
            project_name="Portal", module="Auth", title="Valid Title",
            description="desc", steps_to_reproduce="", expected_result="",
            actual_result="", defect_type="Functional", severity="Catastrophic",
            priority="P1 - Urgent", environment="QA / Test", reporter_id=tester["id"],
            db_path=populated_db
        )

    # Invalid defect type
    with pytest.raises(ValueError, match="Invalid defect type"):
        dm.create_defect(
            project_name="Portal", module="Auth", title="Valid Title",
            description="desc", steps_to_reproduce="", expected_result="",
            actual_result="", defect_type="CosmicRayGlitch", severity="High",
            priority="P1 - Urgent", environment="QA / Test", reporter_id=tester["id"],
            db_path=populated_db
        )


def test_assign_defect(populated_db):
    """Verify defect assignment transitions NEW to ASSIGNED and logs history."""
    admin = auth.get_user_by_username("admin", db_path=populated_db)
    dev = auth.get_user_by_username("dev1", db_path=populated_db)
    tester = auth.get_user_by_username("tester", db_path=populated_db)

    defect_id, _ = dm.create_defect(
        project_name="Portal", module="Auth", title="Assignment Test Bug",
        description="Test desc", steps_to_reproduce="", expected_result="",
        actual_result="", defect_type="Functional", severity="Low",
        priority="P4 - Low", environment="QA / Test", reporter_id=tester["id"],
        db_path=populated_db
    )

    success = dm.assign_defect(
        defect_id=defect_id,
        assigned_to_id=dev["id"],
        assigned_by_id=admin["id"],
        notes="Please investigate urgently.",
        db_path=populated_db
    )
    assert success is True

    defect = dm.get_defect_by_id(defect_id, db_path=populated_db)
    assert defect["status"] == "ASSIGNED"
    assert defect["assigned_to_id"] == dev["id"]

    history = dm.get_defect_history(defect_id, db_path=populated_db)
    assert len(history) == 2
    assert history[-1]["new_status"] == "ASSIGNED"


def test_complete_lifecycle_transitions(populated_db):
    """
    Verify complete defect lifecycle workflow:
    NEW -> ASSIGNED -> IN PROGRESS -> FIXED -> RETESTING -> CLOSED
    """
    admin = auth.get_user_by_username("admin", db_path=populated_db)
    dev = auth.get_user_by_username("dev1", db_path=populated_db)
    tester = auth.get_user_by_username("tester", db_path=populated_db)

    # 1. Create defect (NEW)
    defect_id, _ = dm.create_defect(
        project_name="Portal", module="Billing", title="Tax rounding failure",
        description="desc", steps_to_reproduce="", expected_result="",
        actual_result="", defect_type="Functional", severity="Medium",
        priority="P3 - Normal", environment="QA / Test", reporter_id=tester["id"],
        db_path=populated_db
    )
    assert dm.get_defect_by_id(defect_id, db_path=populated_db)["status"] == "NEW"

    # 2. Assign (NEW -> ASSIGNED)
    dm.assign_defect(defect_id, dev["id"], admin["id"], "Take this", db_path=populated_db)
    assert dm.get_defect_by_id(defect_id, db_path=populated_db)["status"] == "ASSIGNED"

    # 3. Developer starts work (ASSIGNED -> IN PROGRESS)
    dm.update_defect_status(
        defect_id=defect_id,
        new_status="IN PROGRESS",
        changed_by_id=dev["id"],
        comments="Started investigating rounding algorithm.",
        user_role="Developer",
        db_path=populated_db
    )
    assert dm.get_defect_by_id(defect_id, db_path=populated_db)["status"] == "IN PROGRESS"

    # 4. Developer fixes defect (IN PROGRESS -> FIXED)
    dm.update_defect_status(
        defect_id=defect_id,
        new_status="FIXED",
        changed_by_id=dev["id"],
        comments="Fixed using decimal module in PR #104.",
        resolution_notes="Implemented decimal.Decimal rounding.",
        user_role="Developer",
        db_path=populated_db
    )
    def_fixed = dm.get_defect_by_id(defect_id, db_path=populated_db)
    assert def_fixed["status"] == "FIXED"
    assert "decimal" in def_fixed["resolution_notes"]

    # 5. Tester starts retesting (FIXED -> RETESTING)
    dm.update_defect_status(
        defect_id=defect_id,
        new_status="RETESTING",
        changed_by_id=tester["id"],
        comments="Deploying to QA environment for verification.",
        user_role="Tester",
        db_path=populated_db
    )
    assert dm.get_defect_by_id(defect_id, db_path=populated_db)["status"] == "RETESTING"

    # 6. Tester closes defect (RETESTING -> CLOSED)
    dm.update_defect_status(
        defect_id=defect_id,
        new_status="CLOSED",
        changed_by_id=tester["id"],
        comments="Verified tax calculations across 100 test cases. Passed.",
        user_role="Tester",
        db_path=populated_db
    )
    assert dm.get_defect_by_id(defect_id, db_path=populated_db)["status"] == "CLOSED"


def test_reopen_lifecycle_flow(populated_db):
    """
    Verify retest failure workflow:
    RETESTING -> REOPENED -> IN PROGRESS
    """
    tester = auth.get_user_by_username("tester", db_path=populated_db)

    # BUG-0006 is in RETESTING in seed data, assigned to dev2
    bug6 = dm.get_defect_by_code("BUG-0006", db_path=populated_db)
    assert bug6["status"] == "RETESTING"
    assigned_dev = auth.get_user_by_id(bug6["assigned_to_id"], db_path=populated_db)

    # Tester fails retesting and reopens
    dm.update_defect_status(
        defect_id=bug6["id"],
        new_status="REOPENED",
        changed_by_id=tester["id"],
        comments="Deadlock still occurs when concurrency exceeds 100 req/sec.",
        user_role="Tester",
        db_path=populated_db
    )
    assert dm.get_defect_by_code("BUG-0006", db_path=populated_db)["status"] == "REOPENED"

    # Assigned Developer moves REOPENED -> IN PROGRESS
    dm.update_defect_status(
        defect_id=bug6["id"],
        new_status="IN PROGRESS",
        changed_by_id=assigned_dev["id"],
        comments="Re-opened investigation on connection pool parameters.",
        user_role="Developer",
        db_path=populated_db
    )
    assert dm.get_defect_by_code("BUG-0006", db_path=populated_db)["status"] == "IN PROGRESS"


def test_invalid_lifecycle_transition_rejected(populated_db):
    """Verify that illegal status jumps (e.g. NEW -> CLOSED) are rejected with ValueError."""
    admin = auth.get_user_by_username("admin", db_path=populated_db)
    tester = auth.get_user_by_username("tester", db_path=populated_db)

    defect_id, _ = dm.create_defect(
        project_name="Portal", module="Auth", title="Transition Test",
        description="desc", steps_to_reproduce="", expected_result="",
        actual_result="", defect_type="Functional", severity="Low",
        priority="P4 - Low", environment="QA / Test", reporter_id=tester["id"],
        db_path=populated_db
    )

    # Attempt NEW -> CLOSED
    with pytest.raises(ValueError, match="Invalid lifecycle transition"):
        dm.update_defect_status(
            defect_id=defect_id,
            new_status="CLOSED",
            changed_by_id=admin["id"],
            db_path=populated_db
        )


def test_developer_cannot_close_defect(populated_db):
    """Verify that Developers cannot directly close defects (enforcing QA separation of duties)."""
    bug6 = dm.get_defect_by_code("BUG-0006", db_path=populated_db)  # RETESTING
    assigned_dev = auth.get_user_by_id(bug6["assigned_to_id"], db_path=populated_db)

    with pytest.raises(PermissionError, match="Developers can only transition defects"):
        dm.update_defect_status(
            defect_id=bug6["id"],
            new_status="CLOSED",
            changed_by_id=assigned_dev["id"],
            user_role="Developer",
            db_path=populated_db
        )


def test_reclassification(populated_db):
    """Verify updating severity, priority, and defect type creates audit history."""
    admin = auth.get_user_by_username("admin", db_path=populated_db)
    bug1 = dm.get_defect_by_code("BUG-0001", db_path=populated_db)

    dm.update_defect_classification(
        defect_id=bug1["id"],
        severity="High",
        priority="P2 - High",
        defect_type="Security",
        changed_by_id=admin["id"],
        comments="Downgraded severity after partial mitigation.",
        db_path=populated_db
    )

    updated = dm.get_defect_by_code("BUG-0001", db_path=populated_db)
    assert updated["severity"] == "High"
    assert updated["priority"] == "P2 - High"

    history = dm.get_defect_history(bug1["id"], db_path=populated_db)
    assert "Downgraded severity" in history[-1]["comments"]


def test_csv_export(populated_db):
    """Verify CSV export functionality."""
    import pandas as pd
    defects = dm.get_all_defects(db_path=populated_db)
    df = pd.DataFrame(defects)
    csv_bytes = analytics.export_defects_to_csv(df)
    assert len(csv_bytes) > 0
    assert b"BUG-0001" in csv_bytes

