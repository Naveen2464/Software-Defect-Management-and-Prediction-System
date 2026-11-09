"""
prevention.py - Defect Prevention Module.
Analyzes database records for recurring defect patterns, identifies vulnerable modules,
and generates automated, data-driven preventive recommendations.
"""

from typing import Dict, List, Any
from collections import Counter
import pandas as pd
from database import get_connection


def analyze_defect_patterns(db_path: str = None) -> Dict[str, Any]:
    """
    Perform deep analysis on actual SQLite defect data to extract:
    - Frequently occurring defect types and categories
    - Modules with repeated defects
    - Common technical failure patterns
    - High-risk modules requiring additional preventive testing
    - Tailored prevention strategies based on empirical defect patterns
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT id, defect_code, project_name, module, title, description,
               defect_type, severity, priority, status, created_at
        FROM defects
    """, conn)
    conn.close()

    if df.empty:
        return {
            "total_defects": 0,
            "modules_summary": [],
            "frequent_categories": [],
            "pattern_clusters": [],
            "modules_requiring_testing": [],
            "recommendations": []
        }

    total_defects = len(df)

    # 1. Frequent Categories / Types
    type_counts = df["defect_type"].value_counts().to_dict()
    frequent_categories = [
        {"category": k, "count": int(v), "percentage": round((v / total_defects) * 100, 1)}
        for k, v in type_counts.items()
    ]

    # 2. Module Analysis & Repetition Identification
    module_stats = []
    modules_requiring_testing = []

    for module_name, group in df.groupby("module"):
        mod_total = len(group)
        crit_high = len(group[group["severity"].isin(["Critical", "High"])])
        open_count = len(group[group["status"].isin(["NEW", "ASSIGNED", "IN PROGRESS", "REOPENED"])])
        reopened_count = len(group[group["status"] == "REOPENED"])
        top_type = group["defect_type"].mode().iloc[0] if not group["defect_type"].empty else "General"
        types_dist = group["defect_type"].value_counts().to_dict()

        is_repeated = mod_total >= 2
        requires_extra = mod_total >= 3 or crit_high >= 2 or reopened_count >= 1

        summary_item = {
            "module": module_name,
            "total_defects": mod_total,
            "critical_high": crit_high,
            "open_defects": open_count,
            "reopened": reopened_count,
            "dominant_type": top_type,
            "type_distribution": types_dist,
            "is_repeated": is_repeated,
            "requires_extra_testing": requires_extra
        }
        module_stats.append(summary_item)

        if requires_extra:
            test_types = []
            if "Security" in types_dist:
                test_types.append("Automated Security SAST/DAST & Penetration Testing")
            if "Database" in types_dist or "Integration" in types_dist:
                test_types.append("Concurrency, Deadlock & Transaction Isolation Testing")
            if "Performance" in types_dist:
                test_types.append("Load Stress & Memory Leak Profiling")
            if "UI/UX" in types_dist:
                test_types.append("Cross-Browser Responsive Visual Regression")
            if "Functional" in types_dist or not test_types:
                test_types.append("Boundary Value & Equivalence Partitioning Test Suite")

            modules_requiring_testing.append({
                "module": module_name,
                "defects_count": mod_total,
                "critical_high": crit_high,
                "primary_vulnerability": top_type,
                "recommended_test_suites": test_types,
                "risk_reason": f"{crit_high} Critical/High severity issues; dominant pattern: {top_type} failure."
            })

    # Sort modules by total defects descending
    module_stats = sorted(module_stats, key=lambda x: x["total_defects"], reverse=True)
    modules_requiring_testing = sorted(modules_requiring_testing, key=lambda x: x["defects_count"], reverse=True)

    # 3. Detect Recurring Defect Patterns from Title and Description
    patterns_catalog = [
        {
            "pattern_name": "Authentication & Token Management Vulnerabilities",
            "keywords": ["auth", "token", "jwt", "login", "session", "bypass", "password", "injection", "unencrypted"],
            "category": "Security & Identity",
            "prevention_guideline": "Enforce parameterized SQL statements, mandatory HTTPS redirection, and implement cryptographic tokens with short-lived expiration and server-side revocation."
        },
        {
            "pattern_name": "Concurrency, Race Conditions & Deadlocks",
            "keywords": ["deadlock", "race condition", "concurrent", "locked", "timeout", "thread", "queue"],
            "category": "Data Integrity & Concurrency",
            "prevention_guideline": "Apply optimistic database locking with row versioning, configure idempotent message queues, and execute automated multi-threaded stress tests."
        },
        {
            "pattern_name": "Input Validation & Boundary Value Oversights",
            "keywords": ["negative", "zero", "validation", "overflow", "precision", "rounding", "float", "mime", "extension"],
            "category": "Validation & Robustness",
            "prevention_guideline": "Implement strict server-side schema validation (e.g. Pydantic / Bean Validation) on all input parameters, with explicit boundary checks for <= 0 and floating-point decimal types."
        },
        {
            "pattern_name": "Resource Leaks & Asynchronous Saturation",
            "keywords": ["memory leak", "cpu", "oom", "resource", "exhaustion", "saturation", "spike", "canvas", "unclosed"],
            "category": "Performance & Scalability",
            "prevention_guideline": "Introduce deterministic context managers ('with' blocks) for file and socket handles, run continuous memory profiling in staging pipelines, and enforce chunked data streaming."
        },
        {
            "pattern_name": "Third-Party API & Network Resilience Failures",
            "keywords": ["webhook", "retry", "api", "twilio", "stripe", "network", "flapping", "disconnection", "e.164"],
            "category": "Integration & Network",
            "prevention_guideline": "Adopt circuit breaker patterns, strict payload contract tests, and idempotent retry policies with exponential jitter for external integrations."
        }
    ]

    detected_patterns = []
    for pattern in patterns_catalog:
        matched_defects = []
        for _, row in df.iterrows():
            text = f"{row['title']} {row['description']}".lower()
            if any(k in text for k in pattern["keywords"]):
                matched_defects.append(f"{row['defect_code']}: {row['title']}")

        if matched_defects:
            detected_patterns.append({
                "pattern_name": pattern["pattern_name"],
                "category": pattern["category"],
                "frequency": len(matched_defects),
                "matched_defects": matched_defects,
                "prevention_guideline": pattern["prevention_guideline"]
            })

    detected_patterns = sorted(detected_patterns, key=lambda x: x["frequency"], reverse=True)

    # 4. Generate Data-Driven Prevention Recommendations
    recommendations = []

    # Check top category
    if frequent_categories:
        top_cat = frequent_categories[0]
        if top_cat["category"] == "Security":
            recommendations.append({
                "focus_area": "Security Architecture & Shift-Left Code Auditing",
                "severity": "CRITICAL",
                "observation": f"Security issues comprise {top_cat['percentage']}% ({top_cat['count']} defects) of all reported issues in the database.",
                "action_items": [
                    "Integrate automated SAST (Static Application Security Testing) tools into GitHub Actions / GitLab CI.",
                    "Adopt automated dependency vulnerability scanning (Dependabot / Snyk) to catch outdated libraries.",
                    "Enforce strict OWASP ASVS verification across all authentication endpoints.",
                    "Mandate input sanitization and parameterized queries across all database access layers."
                ]
            })
        elif top_cat["category"] == "Functional":
            recommendations.append({
                "focus_area": "Requirements Traceability & Unit Test Coverage",
                "severity": "HIGH",
                "observation": f"Functional defects account for {top_cat['percentage']}% ({top_cat['count']} defects) of logged issues.",
                "action_items": [
                    "Implement Behavior-Driven Development (BDD) specs with Gherkin acceptance criteria before implementation.",
                    "Target minimum 85% branch coverage on core domain logic modules.",
                    "Conduct peer code reviews with explicit checklists for boundary value edge cases."
                ]
            })

    # Check highest defect module
    if module_stats:
        worst_module = module_stats[0]
        if worst_module["total_defects"] >= 3:
            recommendations.append({
                "focus_area": f"Architectural Refactoring for '{worst_module['module']}'",
                "severity": "HIGH",
                "observation": f"The module '{worst_module['module']}' exhibits recurrent failure patterns with {worst_module['total_defects']} total defects ({worst_module['critical_high']} Critical/High).",
                "action_items": [
                    f"Perform a root-cause retrospective on all resolved defects in '{worst_module['module']}'.",
                    f"Implement an isolated integration test harness specifically mocking '{worst_module['module']}' boundaries.",
                    "Mandate that two senior engineers approve pull requests affecting this module."
                ]
            })

    # General recommendations based on recurrent patterns
    for pat in detected_patterns[:3]:
        recommendations.append({
            "focus_area": f"Preventive Control: {pat['pattern_name']}",
            "severity": "MEDIUM",
            "observation": f"Detected in {pat['frequency']} defects across the codebase.",
            "action_items": [
                pat["prevention_guideline"],
                "Add targeted automated integration test fixtures reproducing these failure scenarios."
            ]
        })

    return {
        "total_defects": total_defects,
        "modules_summary": module_stats,
        "frequent_categories": frequent_categories,
        "pattern_clusters": detected_patterns,
        "modules_requiring_testing": modules_requiring_testing,
        "recommendations": recommendations
    }

