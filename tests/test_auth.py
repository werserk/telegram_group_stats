from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from app.constants import AuthorizationState
from app.web.auth import AuthorizePage


@pytest.fixture
def mock_td_client():
    """Returns a TDLibClient mock with relevant methods stubbed."""
    client = MagicMock()
    return client


def test_auth_page_shows_phone_input(mock_td_client, monkeypatch):
    """
    Test that _show_phone_input is called when the auth state is WAIT_PHONE_NUMBER.
    """
    # Mock Streamlit functions
    monkeypatch.setattr(st, "text_input", lambda *args, **kwargs: "1234567890")
    monkeypatch.setattr(st, "button", lambda label: True)
    monkeypatch.setattr(st, "rerun", lambda: None)

    # Mock st.spinner as a context manager using contextlib
    from contextlib import contextmanager

    @contextmanager
    def mock_spinner(text):
        yield

    monkeypatch.setattr(st, "spinner", mock_spinner)

    # Mock the login_step to set the auth state to WAIT_PHONE_NUMBER
    mock_td_client.login_step.return_value = AuthorizationState.WAIT_PHONE_NUMBER
    mock_td_client.send_phone_number.return_value = AuthorizationState.WAIT_CODE

    # Initialize the AuthorizePage with the mocked TDLibClient
    page = AuthorizePage(td_client=mock_td_client)

    # Patch _show_phone_input to monitor its call
    with patch.object(page, "_show_phone_input") as mock_show_phone:
        page.show()
        mock_show_phone.assert_called_once()


def test_auth_page_no_auth_state(mock_td_client, monkeypatch):
    """
    Test that when the auth state becomes READY, the success message is displayed.
    """
    # Mock Streamlit session_state and functions
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "rerun", lambda: None)

    # Mock st.spinner as a context manager using contextlib
    from contextlib import contextmanager

    @contextmanager
    def mock_spinner(text):
        yield

    monkeypatch.setattr(st, "spinner", mock_spinner)

    # Mock the login_step to set the auth state to READY
    mock_td_client.login_step.return_value = AuthorizationState.READY

    # Initialize the AuthorizePage with the mocked TDLibClient
    page = AuthorizePage(td_client=mock_td_client)

    # Mock st.success to verify it was called with the correct message
    with patch.object(st, "success") as mock_success:
        page.show()
        mock_success.assert_called_once_with("You are authorized! Go to Analytics.")
