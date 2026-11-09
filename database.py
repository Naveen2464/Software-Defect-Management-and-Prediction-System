"""
database.py - Database design and operations for Software Defect Management and Prediction System.
Uses SQLite with strict foreign keys, indexing, and migration/initialization support.
"""

import sqlite3
import os
import hashlib
from datetime import datetime, timedelta

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "defects.db")
_CURRENT_DB_PATH = None


def set_db_path(path: str):
    """Set custom database path (useful for testing)."""
    global _CURRENT_DB_PATH
    _CURRENT_DB_PATH = path


def get_db_path(db_path: str = None) -> str:
    """Return the active database path."""
    if db_path:
        return db_path
    if _CURRENT_DB_PATH:
        return _CURRENT_DB_PATH
    return DEFAULT_DB_PATH


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Establish and configure an SQLite connection."""
    target_path = get_db_path(db_path)
    dir_name = os.path.dirname(target_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 15000;")
    return conn


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with consistent salt."""
    salt = "defect_mgmt_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()


def init_db(db_path: str = None):
    """Initialize database tables, constraints, and indexes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Admin', 'Tester', 'Developer')),
        created_at TEXT NOT NULL
    );
    """)

    # 2. Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 3. Defects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS defects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        defect_code TEXT UNIQUE NOT NULL,
        project_name TEXT NOT NULL,
        module TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        steps_to_reproduce TEXT,
        expected_result TEXT,
        actual_result TEXT,
        defect_type TEXT NOT NULL CHECK(defect_type IN (
            'Functional', 'Performance', 'Security', 'UI/UX', 
            'Compatibility', 'Database', 'Integration'
        )),
        severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low')),
        priority TEXT NOT NULL CHECK(priority IN ('P1 - Urgent', 'P2 - High', 'P3 - Normal', 'P4 - Low')),
        environment TEXT NOT NULL,
        screenshot_path TEXT,
        reporter_id INTEGER NOT NULL,
        assigned_to_id INTEGER,
        status TEXT NOT NULL DEFAULT 'NEW' CHECK(status IN (
            'NEW', 'ASSIGNED', 'IN PROGRESS', 'FIXED', 
            'RETESTING', 'REOPENED', 'CLOSED'
        )),
        resolution_notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 4. Assignments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        defect_id INTEGER NOT NULL,
        assigned_by_id INTEGER NOT NULL,
        assigned_to_id INTEGER NOT NULL,
        assigned_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (defect_id) REFERENCES defects(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by_id) REFERENCES users(id) ON DELETE RESTRICT,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    # 5. Defect History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS defect_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        defect_id INTEGER NOT NULL,
        previous_status TEXT NOT NULL,
        new_status TEXT NOT NULL,
        changed_by_id INTEGER NOT NULL,
        comments TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (defect_id) REFERENCES defects(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by_id) REFERENCES users(id) ON DELETE RESTRICT
    );
    """)

    # Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defects_module ON defects(module);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defects_status ON defects(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defects_severity ON defects(severity);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defects_priority ON defects(priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defects_assigned ON defects(assigned_to_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_defect ON defect_history(defect_id);")

    conn.commit()
    conn.close()


def seed_sample_data(db_path: str = None, force: bool = False):
    """Seed realistic initial data for demonstration purposes."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]

    if user_count > 0 and not force:
        conn.close()
        return False

    if force:
        # Clear existing tables safely
        cursor.execute("DELETE FROM defect_history")
        cursor.execute("DELETE FROM assignments")
        cursor.execute("DELETE FROM defects")
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM users")
        conn.commit()

    now = datetime.now()

    # 1. Seed Users
    users_data = [
        ("admin", hash_password("admin123"), "Naveen (QA Director)", "admin@defects.io", "Admin", (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")),
        ("tester", hash_password("tester123"), "Alex Rivera (Lead QA)", "alex.tester@defects.io", "Tester", (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")),
        ("tester2", hash_password("tester123"), "Maya Lin (QA Specialist)", "maya.tester@defects.io", "Tester", (now - timedelta(days=85)).strftime("%Y-%m-%d %H:%M:%S")),
        ("dev1", hash_password("dev123"), "David Kim (Senior Backend)", "david.kim@defects.io", "Developer", (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")),
        ("dev2", hash_password("dev123"), "Elena Rostova (Full Stack)", "elena.r@defects.io", "Developer", (now - timedelta(days=80)).strftime("%Y-%m-%d %H:%M:%S")),
        ("dev3", hash_password("dev123"), "Marcus Vance (Frontend UI)", "marcus.v@defects.io", "Developer", (now - timedelta(days=75)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    cursor.executemany("""
        INSERT INTO users (username, password_hash, full_name, email, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, users_data)
    conn.commit()

    # Retrieve User IDs
    cursor.execute("SELECT id, username FROM users")
    user_map = {row["username"]: row["id"] for row in cursor.fetchall()}

    # 2. Seed Projects
    projects_data = [
        ("E-Commerce Web Portal", "Customer-facing online storefront and catalog platform.", (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")),
        ("Mobile Banking App", "Secure cross-platform native iOS & Android banking system.", (now - timedelta(days=80)).strftime("%Y-%m-%d %H:%M:%S")),
        ("Healthcare Records System", "Electronic health records and diagnostic patient portal.", (now - timedelta(days=70)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    cursor.executemany("""
        INSERT INTO projects (name, description, created_at)
        VALUES (?, ?, ?)
    """, projects_data)
    conn.commit()

    # 3. Seed Realistic Defects across 6 modules
    # Statuses: NEW, ASSIGNED, IN PROGRESS, FIXED, RETESTING, REOPENED, CLOSED
    defects_data = [
        {
            "code": "BUG-0001",
            "project": "E-Commerce Web Portal",
            "module": "Login & Authentication",
            "title": "SQL Injection vulnerability in login authentication bypass",
            "description": "Entering unescaped quotation strings in password field allows authentication bypass.",
            "steps": "1. Go to /login\n2. Enter username 'admin'\n3. Enter password: ' OR '1'='1\n4. Submit form.",
            "expected": "Authentication rejected with 401 Unauthorized.",
            "actual": "Bypasses credentials and logs in as administrator.",
            "type": "Security",
            "severity": "Critical",
            "priority": "P1 - Urgent",
            "env": "QA / Test",
            "screenshot": "uploads/bug_0001_screenshot.png",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev1"],
            "status": "FIXED",
            "notes": "Replaced raw string query concatenation with parameterized SQLite queries and Argon2 hashing.",
            "days_ago": 45,
            "updated_days_ago": 30
        },
        {
            "code": "BUG-0002",
            "project": "E-Commerce Web Portal",
            "module": "Login & Authentication",
            "title": "Session token does not expire after user logout",
            "description": "JWT session token remains active in browser cookies after explicit user logout.",
            "steps": "1. Login with tester account\n2. Click Logout\n3. Reuse cached auth header token in API request.",
            "expected": "Token is invalidated in blacklist cache.",
            "actual": "Server returns 200 OK with sensitive profile payload.",
            "type": "Security",
            "severity": "High",
            "priority": "P1 - Urgent",
            "env": "Production",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev1"],
            "status": "REOPENED",
            "notes": "Initial blacklist TTL expired too soon; reopened for Redis server-side token revocation.",
            "days_ago": 40,
            "updated_days_ago": 5
        },
        {
            "code": "BUG-0003",
            "project": "E-Commerce Web Portal",
            "module": "Login & Authentication",
            "title": "Password reset token sent via unencrypted HTTP link",
            "description": "Forgot password email contains plaintext reset token without HTTPS enforcement.",
            "steps": "1. Click Forgot Password\n2. Inspect generated email link URL.",
            "expected": "Strict HTTPS redirect URL with single-use nonce.",
            "actual": "Plain HTTP link allows man-in-the-middle token sniffing.",
            "type": "Security",
            "severity": "Critical",
            "priority": "P2 - High",
            "env": "Staging",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev1"],
            "status": "CLOSED",
            "notes": "Enforced HTTPS scheme on link builder and added TLS termination.",
            "days_ago": 55,
            "updated_days_ago": 20
        },
        {
            "code": "BUG-0004",
            "project": "E-Commerce Web Portal",
            "module": "Payment Gateway",
            "title": "Double debit on credit card payment retry during network timeout",
            "description": "If user clicks Pay Now during transient network disconnect, order charges twice.",
            "steps": "1. Add item to cart\n2. Proceed to checkout\n3. Throttle network to 2kbps\n4. Click Pay Now twice.",
            "expected": "Idempotency key prevents duplicate transaction.",
            "actual": "Two separate payment intent transactions created on Stripe.",
            "type": "Functional",
            "severity": "Critical",
            "priority": "P1 - Urgent",
            "env": "Production",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev2"],
            "status": "IN PROGRESS",
            "notes": "Implementing idempotency key header and client-side payment button disabling.",
            "days_ago": 15,
            "updated_days_ago": 3
        },
        {
            "code": "BUG-0005",
            "project": "E-Commerce Web Portal",
            "module": "Payment Gateway",
            "title": "Currency conversion rounding error causing 1 cent discrepancy",
            "description": "Converting EUR to USD truncates floating point values instead of banker rounding.",
            "steps": "1. Set currency to EUR\n2. Add item valued at 19.99 EUR\n3. Check invoice.",
            "expected": "Exact rounded currency total matching payment receipt.",
            "actual": "Total off by $0.01 due to IEEE 754 precision float error.",
            "type": "Functional",
            "severity": "High",
            "priority": "P2 - High",
            "env": "QA / Test",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev2"],
            "status": "FIXED",
            "notes": "Switched currency calculations to Python decimal.Decimal.",
            "days_ago": 28,
            "updated_days_ago": 12
        },
        {
            "code": "BUG-0006",
            "project": "E-Commerce Web Portal",
            "module": "Payment Gateway",
            "title": "Webhook race condition fails to update order payment status",
            "description": "High volume payment webhooks result in row locks and rollback of order status.",
            "steps": "1. Fire 50 concurrent payment webhook events for 50 orders simultaneously.",
            "expected": "All 50 orders marked as 'PAID'.",
            "actual": "4 orders left in 'PENDING' status due to deadlocks.",
            "type": "Integration",
            "severity": "High",
            "priority": "P1 - Urgent",
            "env": "Staging",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev2"],
            "status": "RETESTING",
            "notes": "Added distributed queue with exponential backoff retry.",
            "days_ago": 22,
            "updated_days_ago": 4
        },
        {
            "code": "BUG-0007",
            "project": "Mobile Banking App",
            "module": "Payment Gateway",
            "title": "Zero amount transaction accepted by validation filter",
            "description": "User can initiate 0.00 transfer which locks ledger accounts.",
            "steps": "1. Go to funds transfer\n2. Enter 0.00\n3. Click Send.",
            "expected": "Client & server validation: Amount must be greater than zero.",
            "actual": "Server accepted request and created empty ledger entry.",
            "type": "Functional",
            "severity": "Medium",
            "priority": "P3 - Normal",
            "env": "QA / Test",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev1"],
            "status": "CLOSED",
            "notes": "Added Pydantic validator constraint gt=0.",
            "days_ago": 60,
            "updated_days_ago": 35
        },
        {
            "code": "BUG-0008",
            "project": "E-Commerce Web Portal",
            "module": "Shopping Cart",
            "title": "Negative item quantity allows cart value manipulation",
            "description": "Manipulating quantity input payload to negative integer subtracts total bill.",
            "steps": "1. Add item to cart\n2. Intercept request and set quantity = -2\n3. Review total.",
            "expected": "Server rejects negative quantities with 400 Bad Request.",
            "actual": "Negative price deducted from overall cart order balance.",
            "type": "Security",
            "severity": "Critical",
            "priority": "P1 - Urgent",
            "env": "Staging",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev2"],
            "status": "CLOSED",
            "notes": "Added schema validation rejecting integers <= 0.",
            "days_ago": 70,
            "updated_days_ago": 50
        },
        {
            "code": "BUG-0009",
            "project": "E-Commerce Web Portal",
            "module": "Shopping Cart",
            "title": "Cart items vanish on browser refresh for guest shoppers",
            "description": "Guest cart session local storage not synchronized with session cookie.",
            "steps": "1. Browse as guest\n2. Add item\n3. Press F5 reload.",
            "expected": "Items persist across browser reloads.",
            "actual": "Cart shows 0 items.",
            "type": "UI/UX",
            "severity": "Medium",
            "priority": "P3 - Normal",
            "env": "QA / Test",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev3"],
            "status": "ASSIGNED",
            "notes": "Assigned to Marcus for local storage sync review.",
            "days_ago": 10,
            "updated_days_ago": 8
        },
        {
            "code": "BUG-0010",
            "project": "Healthcare Records System",
            "module": "Database Sync",
            "title": "Deadlock during concurrent patient record medical chart update",
            "description": "Simultaneous updates by nurse and doctor cause unhandled sqlite3.OperationalError.",
            "steps": "1. Nurse updates vitals\n2. Doctor updates medication simultaneously.",
            "expected": "Optimistic locking with revision number.",
            "actual": "500 Internal Server Error: Database is locked.",
            "type": "Database",
            "severity": "Critical",
            "priority": "P1 - Urgent",
            "env": "QA / Test",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev1"],
            "status": "IN PROGRESS",
            "notes": "Implementing row-level versioning and timeout retry.",
            "days_ago": 18,
            "updated_days_ago": 2
        },
        {
            "code": "BUG-0011",
            "project": "Healthcare Records System",
            "module": "Database Sync",
            "title": "Offline sync queue drops records when reconnection flickers",
            "description": "Network flapping during tablet sync causes batch payload drop without retry.",
            "steps": "1. Disconnect WiFi\n2. Add 5 records\n3. Toggle WiFi rapidly on/off.",
            "expected": "Persistent transactional sync queue.",
            "actual": "2 of 5 records lost permanently.",
            "type": "Database",
            "severity": "High",
            "priority": "P1 - Urgent",
            "env": "QA / Test",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev1"],
            "status": "NEW",
            "notes": "Newly reported during network resilience testing.",
            "days_ago": 5,
            "updated_days_ago": 5
        },
        {
            "code": "BUG-0012",
            "project": "E-Commerce Web Portal",
            "module": "User Profile",
            "title": "Profile picture upload accepts executable .exe disguised as .png",
            "description": "File upload validation checks only extension, ignoring MIME magic bytes.",
            "steps": "1. Rename malicious.exe to photo.png\n2. Upload in user profile.",
            "expected": "File type inspection rejects executable binary.",
            "actual": "File uploaded and saved to public uploads directory.",
            "type": "Security",
            "severity": "Critical",
            "priority": "P1 - Urgent",
            "env": "Staging",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev3"],
            "status": "FIXED",
            "notes": "Implemented Pillow image verification to enforce strict image formats.",
            "days_ago": 35,
            "updated_days_ago": 15
        },
        {
            "code": "BUG-0013",
            "project": "Mobile Banking App",
            "module": "User Profile",
            "title": "Address field text overflows mobile screen container",
            "description": "Long address text without line breaks clips outside card viewport on iPhone SE.",
            "steps": "1. Enter 150 character street name\n2. View profile card on 375px screen.",
            "expected": "Text wraps cleanly or ellipses applied.",
            "actual": "Text overflows screen width horizontally.",
            "type": "UI/UX",
            "severity": "Low",
            "priority": "P4 - Low",
            "env": "QA / Test",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev3"],
            "status": "CLOSED",
            "notes": "Added CSS word-break: break-word and max-width 100%.",
            "days_ago": 50,
            "updated_days_ago": 32
        },
        {
            "code": "BUG-0014",
            "project": "E-Commerce Web Portal",
            "module": "Order Processing",
            "title": "High CPU utilization spike during mass order CSV export",
            "description": "Exporting 10,000 orders loads entire table in memory causing 100% CPU lock.",
            "steps": "1. Go to Admin Orders\n2. Select Date Range 'All'\n3. Click Export CSV.",
            "expected": "Streaming generator response with chunked fetch.",
            "actual": "Web worker times out after 60 seconds of CPU saturation.",
            "type": "Performance",
            "severity": "High",
            "priority": "P2 - High",
            "env": "Production",
            "reporter": user_map["admin"],
            "assigned_to": user_map["dev1"],
            "status": "ASSIGNED",
            "notes": "Assigned to David Kim to refactor export to stream cursor.",
            "days_ago": 12,
            "updated_days_ago": 10
        },
        {
            "code": "BUG-0015",
            "project": "Mobile Banking App",
            "module": "Order Processing",
            "title": "Order notification SMS fails for international phone numbers",
            "description": "Twilio integration strips leading '+' international country code prefix.",
            "steps": "1. Place order with UK number (+44...)\n2. Check SMS delivery logs.",
            "expected": "SMS delivered successfully in E.164 format.",
            "actual": "Twilio returns 400 Invalid Phone Number format.",
            "type": "Integration",
            "severity": "Medium",
            "priority": "P3 - Normal",
            "env": "Staging",
            "reporter": user_map["tester2"],
            "assigned_to": user_map["dev2"],
            "status": "NEW",
            "notes": "Needs E.164 phone formatting library.",
            "days_ago": 7,
            "updated_days_ago": 7
        },
        {
            "code": "BUG-0016",
            "project": "Healthcare Records System",
            "module": "Report Generator",
            "title": "Memory leak in PDF generation background worker",
            "description": "Report worker memory footprint grows by 250MB per batch until OOM killed.",
            "steps": "1. Run 20 consecutive medical summary PDF exports\n2. Monitor process RSS.",
            "expected": "Memory released after garbage collection.",
            "actual": "Worker crashes after 15th export.",
            "type": "Performance",
            "severity": "High",
            "priority": "P2 - High",
            "env": "QA / Test",
            "reporter": user_map["tester"],
            "assigned_to": user_map["dev2"],
            "status": "IN PROGRESS",
            "notes": "Found unclosed file descriptors in PDF canvas loop.",
            "days_ago": 14,
            "updated_days_ago": 1
        }
    ]

    for d in defects_data:
        created_time = (now - timedelta(days=d["days_ago"])).strftime("%Y-%m-%d %H:%M:%S")
        updated_time = (now - timedelta(days=d["updated_days_ago"])).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO defects (
                defect_code, project_name, module, title, description,
                steps_to_reproduce, expected_result, actual_result,
                defect_type, severity, priority, environment,
                screenshot_path, reporter_id, assigned_to_id,
                status, resolution_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["code"], d["project"], d["module"], d["title"], d["description"],
            d["steps"], d["expected"], d["actual"],
            d["type"], d["severity"], d["priority"], d["env"],
            d.get("screenshot", None), d["reporter"], d["assigned_to"],
            d["status"], d["notes"], created_time, updated_time
        ))
        defect_id = cursor.lastrowid

        # Insert initial assignment if assigned
        if d["assigned_to"]:
            cursor.execute("""
                INSERT INTO assignments (defect_id, assigned_by_id, assigned_to_id, assigned_at, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                defect_id,
                user_map["admin"],
                d["assigned_to"],
                created_time,
                "Assigned during triage."
            ))

        # Insert initial history record (NEW)
        cursor.execute("""
            INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            defect_id,
            "NONE",
            "NEW",
            d["reporter"],
            "Defect discovered and logged into system.",
            created_time
        ))

        # Insert intermediate history if status advanced
        if d["status"] != "NEW":
            assigned_time = (now - timedelta(days=max(d["days_ago"] - 2, 1))).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                defect_id,
                "NEW",
                "ASSIGNED",
                user_map["admin"],
                "Defect assigned to developer.",
                assigned_time
            ))

            if d["status"] in ["IN PROGRESS", "FIXED", "RETESTING", "REOPENED", "CLOSED"]:
                inprogress_time = (now - timedelta(days=max(d["days_ago"] - 5, 1))).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    defect_id,
                    "ASSIGNED",
                    "IN PROGRESS",
                    d["assigned_to"] or user_map["dev1"],
                    "Investigating root cause and developing fix.",
                    inprogress_time
                ))

            if d["status"] in ["FIXED", "RETESTING", "REOPENED", "CLOSED"]:
                fixed_time = (now - timedelta(days=max(d["days_ago"] - 8, 1))).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    defect_id,
                    "IN PROGRESS",
                    "FIXED",
                    d["assigned_to"] or user_map["dev1"],
                    d["notes"] or "Fix applied in pull request.",
                    fixed_time
                ))

            if d["status"] in ["RETESTING", "REOPENED", "CLOSED"]:
                retesting_time = (now - timedelta(days=max(d["days_ago"] - 10, 1))).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    defect_id,
                    "FIXED",
                    "RETESTING",
                    d["reporter"],
                    "Build deployed to QA environment. Commencing verification.",
                    retesting_time
                ))

            if d["status"] == "REOPENED":
                reopened_time = (now - timedelta(days=d["updated_days_ago"])).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    defect_id,
                    "RETESTING",
                    "REOPENED",
                    d["reporter"],
                    "Retesting failed: " + (d["notes"] or "Issue persists under edge conditions."),
                    reopened_time
                ))

            if d["status"] == "CLOSED":
                closed_time = (now - timedelta(days=d["updated_days_ago"])).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO defect_history (defect_id, previous_status, new_status, changed_by_id, comments, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    defect_id,
                    "RETESTING",
                    "CLOSED",
                    d["reporter"],
                    "Fix verified successfully in QA regression suite. Closed.",
                    closed_time
                ))

    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_db()
    seed_sample_data(force=True)
    print("Database initialized and sample data seeded successfully.")

