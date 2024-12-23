from unittest.mock import MagicMock

import pytest
import streamlit as st

from app.telegram.service import UserInfo
from app.web.analytics import AnalyticsPage


@pytest.fixture
def mock_service(mock_td_client):
    service = MagicMock()

    # Mock return values for service methods
    service.get_chats.return_value = [{"id": 111, "name": "Group111"}, {"id": 222, "name": "Group222"}]

    service.get_chat_members.return_value = [
        {"member_id": {"@type": "messageSenderUser", "user_id": 555}},
        {"member_id": {"@type": "messageSenderUser", "user_id": 666}},
    ]

    service.get_users_common_chats_count_for_chat.return_value = [
        UserInfo(user_id=555, username="@alice", name="Alice", count=3, common_group_ids=[999]),
        UserInfo(user_id=666, username="@bob", name="Bob", count=2, common_group_ids=[888]),
    ]

    # Mock get_user_profile_photo to return bytes
    service.get_user_profile_photo.side_effect = lambda user_id: b"fake_photo1" if user_id == 555 else b"fake_photo2"

    # Mock get_chat_info_by_id to return chat info with 'title' and 'photo'
    service.get_chat_info_by_id.side_effect = lambda chat_id: {
        "@type": "chat",
        "id": chat_id,
        "title": f"Group{chat_id}",
        "photo": {"small": {"id": 12345}},
    }

    # Mock get_chat_photo to return bytes
    service.get_chat_photo.side_effect = lambda chat_info: b"fake_group_photo"

    return service


def test_analytics_page_show_chats(mock_service, monkeypatch):
    # Mock Streamlit functions
    monkeypatch.setattr(st, "selectbox", lambda label, options: "Group111")
    monkeypatch.setattr(st, "button", lambda label: True)
    monkeypatch.setattr(st, "rerun", lambda: None)

    # Mock st.spinner as a context manager using contextlib
    from contextlib import contextmanager

    @contextmanager
    def mock_spinner(text):
        yield

    monkeypatch.setattr(st, "spinner", mock_spinner)

    # Mock st.components.v1.html to prevent actual file operations
    monkeypatch.setattr(st.components.v1, "html", lambda source, height, scrolling: None)

    # Initialize the AnalyticsPage with the mocked service
    page = AnalyticsPage(chat_member_service=mock_service)

    # Run the show method, which should use the mocked Streamlit and service methods
    page.show()

    # Assertions to verify that _stats is populated correctly
    assert page._stats, "Analyze chat should populate _stats after the button is clicked"
    assert len(page._stats) == 2
    assert page._stats[0].user_id == 555
    assert page._stats[0].username == "@alice"
    assert page._stats[0].name == "Alice"
    assert page._stats[0].count == 3
    assert page._stats[0].common_group_ids == [999]
    assert page._stats[1].user_id == 666
    assert page._stats[1].username == "@bob"
    assert page._stats[1].name == "Bob"
    assert page._stats[1].count == 2
    assert page._stats[1].common_group_ids == [888]
