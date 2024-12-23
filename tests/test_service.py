# tests/test_service.py

import pytest

from app.constants import ChatType
from app.telegram.service import ChatMemberService


@pytest.fixture
def service_factory(mock_td_client):
    """
    Фикстура-фабрика для создания ChatMemberService с настроенным mock_td_client.

    Args:
        mock_td_client: Мокнутый экземпляр TDLibClient.

    Returns:
        Функция, принимающая `test_responses` и возвращающая экземпляр ChatMemberService.
    """

    def _create_service(test_responses):
        # Предполагаем, что первый ответ всегда на getMe
        get_me_response = {"@type": "user", "id": 12345}
        if isinstance(test_responses, list):
            # Если предоставлен список ответов, добавляем getMe в начало
            receive_side_effect = [get_me_response] + test_responses
        else:
            # Иначе предполагаем один ответ
            receive_side_effect = [get_me_response, test_responses]

        mock_td_client.receive.side_effect = receive_side_effect
        return ChatMemberService(mock_td_client)

    return _create_service


def test_get_my_user_id(service_factory, mock_td_client):
    # В данном тесте достаточно только getMe
    service = service_factory(None)  # Второй аргумент не нужен, так как getMe уже добавлен
    user_id = service.my_user_id
    assert user_id == 12345


def test_get_chats_empty(service_factory, mock_td_client):
    # После getMe, возвращаем пустой список чатов
    test_responses = {"@type": "chats", "chat_ids": []}
    service = service_factory(test_responses)
    chats = service.get_chats()
    assert chats == []


def test_get_chats_success(service_factory, mock_td_client):
    # После getMe, возвращаем список чатов и информацию о каждом чате
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
    # После getMe, возвращаем информацию о чате и его участников
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
