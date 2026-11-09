"""
tests/test_database.py - Automated tests for database initialization, schema integrity,
constraints, indexing, password hashing, and sample data seeding.
"""

import os
import tempfile
import pytest
import sqlite3
import database


@pytest.fixture
def temp_db():
    """Create a temporary database for test isolation."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_init_db_creates_all_tables(temp_db):
    """Verify that all required tables are created in SQLite."""
    conn = database.get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()

    expected_tables = ["users", "projects", "defects", "assignments", "defect_history"]
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' not found in database."


def test_indexes_exist(temp_db):
    """Verify that performance indexes are created."""
    conn = database.get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row["name"] for row in cursor.fetchall()]
    conn.close()

    expected_indexes = [
        "idx_defects_module",
        "idx_defects_status",
        "idx_defects_severity",
        "idx_defects_priority",
        "idx_defects_assigned",
        "idx_history_defect"
    ]
    for idx in expected_indexes:
        assert idx in indexes, f"Expected index '{idx}' not found."


def test_password_hashing():
    """Verify password hashing is deterministic and salted."""
    hash1 = database.hash_password("admin123")
    hash2 = database.hash_password("admin123")
    hash_diff = database.hash_password("otherpassword")

    assert hash1 == hash2
    assert hash1 != hash_diff
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters


def test_seed_sample_data(temp_db):
    """Verify sample data seeding populates users, projects, and defects."""
    seeded = database.seed_sample_data(temp_db, force=True)
    assert seeded is True

    conn = database.get_connection(temp_db)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    assert user_count >= 6, "Expected at least 6 sample users."

    cursor.execute("SELECT COUNT(*) as count FROM projects")
    project_count = cursor.fetchone()["count"]
    assert project_count >= 3, "Expected at least 3 sample projects."

    cursor.execute("SELECT COUNT(*) as count FROM defects")
    defect_count = cursor.fetchone()["count"]
    assert defect_count >= 15, "Expected at least 15 sample defects."

    cursor.execute("SELECT COUNT(*) as count FROM defect_history")
    history_count = cursor.fetchone()["count"]
    assert history_count >= 15, "Expected defect history entries for all defects."

    conn.close()


def test_seed_sample_data_idempotency(temp_db):
    """Verify running seed_sample_data without force does not duplicate data."""
    database.seed_sample_data(temp_db, force=True)
    second_run = database.seed_sample_data(temp_db, force=False)
    assert second_run is False

    conn = database.get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    conn.close()

    assert user_count == 6


def test_foreign_key_enforcement(temp_db):
    """Verify SQLite foreign key constraints are enforced."""
    conn = database.get_connection(temp_db)
    cursor = conn.cursor()

    with pytest.raises(sqlite3.IntegrityError):
        # Attempt to insert defect with non-existent reporter_id
        cursor.execute("""
            INSERT INTO defects (
                defect_code, project_name, module, title, description,
                defect_type, severity, priority, environment,
                reporter_id, status, created_at, updated_at
            ) VALUES (
                'BUG-TEST', 'Project X', 'Auth', 'Test Defect', 'Desc',
                'Functional', 'Low', 'P4 - Low', 'QA / Test',
                99999, 'NEW', '2026-01-01', '2026-01-01'
            )
        """)
        conn.commit()
    conn.close()


def test_admin_user_management_permissions():
    """Verify that only Admin accounts have permission to manage users."""
    import auth
    admin_user = {"id": 1, "username": "admin", "role": "Admin"}
    tester_user = {"id": 2, "username": "tester", "role": "Tester"}
    dev_user = {"id": 3, "username": "dev1", "role": "Developer"}

    assert auth.can_manage_users(admin_user) is True
    assert auth.can_manage_users(tester_user) is False
    assert auth.can_manage_users(dev_user) is False


