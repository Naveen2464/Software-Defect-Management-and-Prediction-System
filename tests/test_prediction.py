"""
tests/test_prediction.py - Automated tests for defect prediction risk scoring,
explainable factor contributions, risk tier categorization, and defect prevention pattern analysis.
"""

import os
import tempfile
import pytest
import database
import prediction
import prevention


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


def test_predict_module_defects_structure(populated_db):
    """Verify that defect prediction produces valid structure and bounded scores."""
    predictions = prediction.predict_module_defects(db_path=populated_db)
    assert len(predictions) > 0, "Expected module predictions."

    valid_levels = ["Critical Risk", "High Risk", "Medium Risk", "Low Risk"]

    for p in predictions:
        assert "module" in p
        assert "risk_score" in p
        assert 0.0 <= p["risk_score"] <= 100.0, f"Risk score {p['risk_score']} out of bounds [0, 100]."
        assert p["risk_level"] in valid_levels
        assert "factors" in p
        assert "recommendations" in p

        # Check factor structure
        factors = p["factors"]
        for f_key in ["volume", "severity", "unresolved", "reopen", "recency"]:
            assert f_key in factors
            assert "raw" in factors[f_key]
            assert "normalized" in factors[f_key]
            assert "contribution" in factors[f_key]


def test_risk_level_thresholds():
    """Verify risk tier mapping logic."""
    assert prediction.calculate_risk_level(85.0) == "Critical Risk"
    assert prediction.calculate_risk_level(80.0) == "Critical Risk"
    assert prediction.calculate_risk_level(75.0) == "High Risk"
    assert prediction.calculate_risk_level(60.0) == "High Risk"
    assert prediction.calculate_risk_level(45.0) == "Medium Risk"
    assert prediction.calculate_risk_level(30.0) == "Medium Risk"
    assert prediction.calculate_risk_level(20.0) == "Low Risk"
    assert prediction.calculate_risk_level(0.0) == "Low Risk"


def test_high_risk_ranking(populated_db):
    """Verify modules with critical/reopened bugs rank higher than stable modules."""
    predictions = prediction.predict_module_defects(db_path=populated_db)
    
    # Sort order must be descending
    scores = [p["risk_score"] for p in predictions]
    assert scores == sorted(scores, reverse=True), "Predictions should be sorted descending by risk score."

    # Top modules should be high or critical risk
    top_pred = predictions[0]
    assert top_pred["risk_level"] in ["Critical Risk", "High Risk"]
    assert len(top_pred["recommendations"]) > 0


def test_prevention_pattern_analysis(populated_db):
    """Verify defect prevention analyzes patterns and produces recommendations."""
    analysis = prevention.analyze_defect_patterns(db_path=populated_db)

    assert analysis["total_defects"] >= 15
    assert len(analysis["modules_summary"]) > 0
    assert len(analysis["frequent_categories"]) > 0
    assert len(analysis["pattern_clusters"]) > 0
    assert len(analysis["modules_requiring_testing"]) > 0
    assert len(analysis["recommendations"]) > 0

    # Verify at least one security or concurrency pattern was found
    pattern_names = [p["pattern_name"] for p in analysis["pattern_clusters"]]
    assert any("Authentication" in name or "Concurrency" in name for name in pattern_names)

