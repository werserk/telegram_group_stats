import pytest

from app.constants import ChatType
from app.telegram.service import ChatMemberService


@pytest.fixture
def service_factory(mock_td_client):
    def _create_service(test_responses):
        get_me_response = {"@type": "user", "id": 12345}
        if isinstance(test_responses, list):
            receive_side_effect = [get_me_response] + test_responses
        else:
            receive_side_effect = [get_me_response, test_responses]

        mock_td_client.receive.side_effect = receive_side_effect
        return ChatMemberService(mock_td_client)

    return _create_service


def test_get_my_user_id(service_factory, mock_td_client):
    service = service_factory(None)
    user_id = service.my_user_id
    assert user_id == 12345


def test_get_chats_empty(service_factory, mock_td_client):
    test_responses = {"@type": "chats", "chat_ids": []}
    service = service_factory(test_responses)
    chats = service.get_chats()
    assert chats == []


def test_get_chats_success(service_factory, mock_td_client):
    test_responses = [
        {"@type": "chats", "chat_ids": [111, 222]},
        {"@type": "chat", "id": 111, "title": "Chat111", "type": {"@type": ChatType.BASIC_GROUP.value}},
        {"@type": "chat", "id": 222, "title": "Chat222", "type": {"@type": ChatType.SUPERGROUP.value}},
    ]
    service = service_factory(test_responses)
    chats = service.get_chats()
    assert len(chats) == 2
    assert chats[0]["name"] == "Chat111"
    assert chats[1]["name"] == "Chat222"


def test_get_chat_members_basic(service_factory, mock_td_client):
    test_responses = [
        {
            "@type": "chat",
            "id": 111,
            "title": "Basic Chat",
            "type": {"@type": ChatType.BASIC_GROUP.value, "basic_group_id": 9999},
        },
        {"@type": "basicGroupFullInfo", "members": [{"@type": "chatMember", "member_id": "some_member"}]},
    ]
    service = service_factory(test_responses)
    members = service.get_chat_members(111)
    assert len(members) == 1
    assert members[0] == {"@type": "chatMember", "member_id": "some_member"}
