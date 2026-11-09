"""
tests/test_ui_apptest.py - Automated Streamlit UI & Session State Tests using Streamlit AppTest framework.
Verifies UI role rendering, sidebar navigation options, session state updates, and demo role switching.
"""

import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
import auth
import database

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture(scope="module", autouse=True)
def init_main_db():
    database.init_db()
    database.seed_sample_data(force=False)


def test_apptest_login_page_renders_when_unauthenticated():
    """Verify that unauthenticated session renders the dedicated login card."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    # Should display Login header and sign-in button
    login_titles = [m.value for m in at.markdown if "User Login" in str(m.value)]
    assert len(login_titles) > 0


def test_apptest_admin_sidebar_navigation_options():
    """Verify Admin sees exactly all 11 navigation options in the sidebar."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    admin_user = auth.get_user_by_username("admin")
    at.session_state["user"] = admin_user
    at.session_state["selected_page"] = "Dashboard"
    at.run()
    assert not at.exception

    # Find the role navigation radio in sidebar
    radios = [r for r in at.sidebar.radio]
    assert len(radios) > 0
    nav_radio = radios[0]
    # Admin must have 11 items
    assert len(nav_radio.options) == 11
    # Check key pages
    option_texts = " ".join(nav_radio.options)
    assert "Dashboard" in option_texts
    assert "Assign Defects" in option_texts
    assert "User Management" in option_texts


def test_apptest_tester_sidebar_navigation_options():
    """Verify Tester sees exactly 9 navigation options in the sidebar."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    tester_user = auth.get_user_by_username("tester")
    at.session_state["user"] = tester_user
    at.session_state["selected_page"] = "Dashboard"
    at.run()
    assert not at.exception

    radios = [r for r in at.sidebar.radio]
    assert len(radios) > 0
    nav_radio = radios[0]
    # Tester must have 9 items
    assert len(nav_radio.options) == 9
    option_texts = " ".join(nav_radio.options)
    assert "Report New Defect" in option_texts
    assert "Assign Defects" not in option_texts
    assert "User Management" not in option_texts


def test_apptest_developer_sidebar_navigation_options():
    """Verify Developer sees exactly 8 navigation options in the sidebar."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    dev_user = auth.get_user_by_username("dev1")
    at.session_state["user"] = dev_user
    at.session_state["selected_page"] = "Dashboard"
    at.run()
    assert not at.exception

    radios = [r for r in at.sidebar.radio]
    assert len(radios) > 0
    nav_radio = radios[0]
    # Developer must have 8 items
    assert len(nav_radio.options) == 8
    option_texts = " ".join(nav_radio.options)
    assert "Report New Defect" not in option_texts
    assert "Assign Defects" not in option_texts
    assert "User Management" not in option_texts
    assert "All Defects" in option_texts
    assert "Resolution Management" in option_texts


def test_apptest_quick_switch_demo_role_updates_session():
    """Verify Quick Switch Demo Role updates user session and resets page if unauthorized."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    # Start as Admin on User Management page
    admin_user = auth.get_user_by_username("admin")
    at.session_state["user"] = admin_user
    at.session_state["selected_page"] = "User Management"
    at.run()
    assert not at.exception
    assert at.session_state["user"]["role"] == "Admin"

    # Simulate switching to Developer dev1
    dev1 = auth.get_user_by_username("dev1")
    at.session_state["user"] = dev1
    # Check that can_view_page("User Management") is False
    assert auth.can_view_page(dev1, "User Management") is False
    
    # Running app as dev1 while selected_page was "User Management"
    # Sidebar resets selected_page to allowed page
    at.run()
    assert not at.exception
    assert at.session_state["user"]["role"] == "Developer"
    assert at.session_state["selected_page"] in auth.get_allowed_pages(dev1)
