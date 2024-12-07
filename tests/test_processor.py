import pytest

from app.telegram.processor import ChatMemberService

"""
BE AWARE: THESE TESTS ARE NOT SUITABLE FOR EVERY USER. EVERY USER MUST HAVE A TEST USER ACCOUNT.

Constants used for testing. These represent various user IDs, chat IDs, and related data:
- SELF_USER_ID: the ID of the current (authorized) user.
- USER_ID_1, USER_ID_2: different test user IDs.
- CHAT_ID_BASIC, CHAT_ID_TEST: example chat IDs for testing.
- BASIC_GROUP_ID: a basic group identifier for mocking group chats.
- CHAT_TITLE: an example title for a test chat.
- CHATS_LIMIT: a large limit for chat retrieval, matching the service defaults.
"""

SELF_USER_ID = 916542313
USER_ID_1 = 916542313
USER_ID_2 = 642169077
CHAT_ID_BASIC = -1002401691915
CHAT_ID_TEST = -1002401691915
BASIC_GROUP_ID = -1002401691915
CHAT_USERNAME = "@test_group_chat_werserk"
CHATS_LIMIT = 100000


@pytest.fixture
def mock_td_client():
    """
    Provides a mock TDLibClient instance.
    """

    class MockTDLibClient:
        def send(self, query):
            pass

        def receive(self):
            return None

    return MockTDLibClient()


@pytest.fixture
def service(mock_td_client, monkeypatch):
    """
    Provides a ChatMemberService instance with the _send_and_wait_for_response method mocked.
    """
    instance = ChatMemberService(mock_td_client)

    def mock_wait_for_response(self, request_data, success_condition):
        return None

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response)
    return instance


def test_get_my_user_id(service, monkeypatch):
    """
    Tests that _get_my_user_id retrieves the current user's ID correctly.
    """

    def mock_wait_for_response(self, request_data, success_condition):
        return {"@type": "user", "id": SELF_USER_ID}

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response)
    result = service.get_my_user_id()
    assert result == SELF_USER_ID


def test_get_chat_id_by_username_success(service, monkeypatch):
    """
    Tests that get_chat_id_by_username returns the chat ID when a matching chat is found.
    """

    def mock_wait_for_response(self, request_data, success_condition):
        return {"@type": "chat", "id": CHAT_ID_BASIC}

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response)
    result = service.get_chat_id_by_username(CHAT_USERNAME)
    assert result == CHAT_ID_BASIC


def test_get_chat_id_by_username_none(service, monkeypatch):
    """
    Tests that get_chat_id_by_username returns None if no matching chat is found.
    """

    def mock_wait_for_response_none(self, request_data, success_condition):
        return None

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response_none)
    result = service.get_chat_id_by_username("unknown_user")
    assert result is None


def test_get_chat_info_by_id(service, monkeypatch):
    """
    Tests that get_chat_info_by_id returns correct chat information.
    """

    def mock_wait_for_response(self, request_data, success_condition):
        return {"@type": "chat", "id": CHAT_ID_BASIC, "title": CHAT_USERNAME}

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response)
    result = service.get_chat_info_by_id(CHAT_ID_BASIC)
    assert result["id"] == CHAT_ID_BASIC
    assert result["title"] == CHAT_USERNAME


def test_get_chats_no_info(service, monkeypatch):
    """
    Tests that get_chats returns an empty list if no detailed info for chats is available.
    """

    def mock_wait_for_response_chats(self, request_data, success_condition):
        if request_data["@type"] == "getChats":
            return {"@type": "chats", "chat_ids": []}
        return None

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response_chats)
    result = service.get_chats()
    assert result == []


def test_get_chats_success(service, monkeypatch):
    """
    Tests that get_chats returns a list of chats with correct IDs and titles when info is available.
    """

    def mock_wait_for_response_detailed(self, request_data, success_condition):
        if request_data["@type"] == "getChats":
            return {"@type": "chats", "chat_ids": [CHAT_ID_BASIC]}
        if request_data["@type"] == "getChat":
            return {
                "@type": "chat",
                "id": CHAT_ID_BASIC,
                "title": CHAT_USERNAME,
                "type": {"@type": "chatTypeBasicGroup", "basic_group_id": BASIC_GROUP_ID},
            }

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response_detailed)
    result = service.get_chats()
    assert len(result) == 1
    assert result[0]["id"] == CHAT_ID_BASIC
    assert result[0]["name"] == CHAT_USERNAME


def test_get_chat_members(service, monkeypatch):
    """
    Tests that get_chat_members returns the correct member data for a basic group chat.
    """

    def mock_wait_for_response_members(self, request_data, success_condition):
        if request_data["@type"] == "getChat":
            return {
                "@type": "chat",
                "id": CHAT_ID_TEST,
                "title": CHAT_USERNAME,
                "type": {"@type": "chatTypeBasicGroup", "basic_group_id": BASIC_GROUP_ID},
            }
        if request_data["@type"] == "getBasicGroupFullInfo":
            return {
                "@type": "basicGroupFullInfo",
                "members": [
                    {"@type": "chatMember", "member_id": {"@type": "messageSenderUser", "user_id": USER_ID_1}},
                    {"@type": "chatMember", "member_id": {"@type": "messageSenderUser", "user_id": USER_ID_2}},
                ],
            }

    monkeypatch.setattr(ChatMemberService, "_send_and_wait_for_response", mock_wait_for_response_members)
    result = service.get_chat_members(CHAT_ID_TEST)
    assert len(result) == 2
    assert result[0]["member_id"]["user_id"] == USER_ID_1
    assert result[1]["member_id"]["user_id"] == USER_ID_2


def test_get_users_common_chats_count_for_chat(service, monkeypatch):
    """
    Tests that get_users_common_chats_count_for_chat returns correct counts for each user and skips the self user.
    """

    def mock_get_chat_members(self, chat_id):
        return [
            {"member_id": {"@type": "messageSenderUser", "user_id": service._ChatMemberService__my_user_id}},
        ]

    def mock_get_common_groups_with_user(self, user_id):
        if user_id == USER_ID_2:
            return {"@type": "chats", "chat_ids": [CHAT_ID_TEST]}
        return None

    monkeypatch.setattr(ChatMemberService, "get_chat_members", mock_get_chat_members)
    monkeypatch.setattr(ChatMemberService, "get_common_groups_with_user", mock_get_common_groups_with_user)

    result = service.get_users_common_chats_count_for_chat(CHAT_ID_TEST)
    assert result == [
        {"user_id": USER_ID_2, "count_of_common_chats": 1},
    ]

    def mock_get_common_groups_with_user_none(self, user_id):
        return None

    monkeypatch.setattr(ChatMemberService, "get_common_groups_with_user", mock_get_common_groups_with_user_none)
    result = service.get_users_common_chats_count_for_chat(CHAT_ID_TEST)
    assert result == []
