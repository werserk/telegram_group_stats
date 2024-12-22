import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger

from app.telegram.client import TDLibClient
from app.telegram.constants import (
    COMMON_GROUPS_LIMIT,
    DOWNLOAD_PRIORITY,
    MAX_COUNT_CHATS_RESPONSE,
    RECEIVE_LOOP_TIMEOUT,
    ChatType,
)

logging.basicConfig(level=logging.INFO)


@dataclass
class UserInfo:
    """Контейнер данных о пользователе."""

    user_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    count: int = 0
    common_group_ids: List[int] = field(default_factory=list)


class ChatMemberService:
    """
    Сервис для работы с информацией о чатах и участниках (мемберах) в Telegram через TDLibClient.
    """

    def __init__(self, td_client: TDLibClient) -> None:
        """
        :param td_client: Экземпляр TDLibClient для отправки и приёма запросов в TDLib.
        """
        self._td_client = td_client
        self._my_user_id: Optional[int] = self._init_my_user_id()

    @property
    def my_user_id(self) -> Optional[int]:
        """Геттер для идентификатора текущего пользователя."""
        return self._my_user_id

    def _init_my_user_id(self) -> Optional[int]:
        """Первоначальный запрос к TDLib для получения своего user_id."""
        event = self._send_and_wait_for_response({"@type": "getMe"}, success_condition="user")
        if not event:
            logger.error("Failed to retrieve current user info.")
            return None
        return event.get("id")

    def _send_and_wait_for_response(
        self,
        request_data: Dict[str, Any],
        success_condition: Union[str, List[str], Callable[[Dict[str, Any]], bool]],
        timeout: float = RECEIVE_LOOP_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """
        Универсальный метод: отправляет запрос в TDLib и ожидает ответ, удовлетворя условию success_condition.

        :param request_data: Данные запроса, отправляемые в TDLib.
        :param success_condition: Строка @type, список @type или функция для проверки события.
        :param timeout: Таймаут в секундах между итерациями (по умолчанию см. constants).
        :return: Словарь события, если условие выполнено; иначе None.
        """

        def is_successful(event: Dict[str, Any]) -> bool:
            if isinstance(success_condition, str):
                return event.get("@type") == success_condition
            elif isinstance(success_condition, list):
                return event.get("@type") in success_condition
            elif callable(success_condition):
                return success_condition(event)
            return False

        self._td_client.send(request_data)

        while True:
            event = self._td_client.receive()
            if event is None:
                time.sleep(timeout)
                continue

            if event.get("@type") == "error":
                logger.error(f"TDLib error: {event.get('message')}")
                return None

            if is_successful(event):
                return event

    def get_chat_id_by_username(self, username: str) -> Optional[int]:
        """Находит чат по публичному username."""
        event = self._send_and_wait_for_response(
            {"@type": "searchPublicChat", "username": username}, success_condition="chat"
        )
        if event:
            return event.get("id")
        return None

    def get_chat_info_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о чате по ID."""
        return self._send_and_wait_for_response({"@type": "getChat", "chat_id": chat_id}, success_condition="chat")

    def get_chats(self) -> List[Dict[str, Any]]:
        """
        Возвращает все доступные пользователю чаты (BASIC_GROUP или SUPERGROUP).
        """
        event = self._send_and_wait_for_response(
            {"@type": "getChats", "limit": MAX_COUNT_CHATS_RESPONSE}, success_condition="chats"
        )
        if event is None:
            return []

        chat_ids = event.get("chat_ids", [])
        chats_info = []
        for c_id in chat_ids:
            info = self.get_chat_info_by_id(c_id)
            if not info:
                continue
            ctype = info["type"]["@type"]
            # Фильтрация типов чатов
            if ctype not in (ChatType.BASIC_GROUP.value, ChatType.SUPERGROUP.value):
                continue
            chats_info.append({"id": c_id, "name": info.get("title", "Unknown")})
        return chats_info

    def get_chat_members(self, chat_id: int) -> List[Dict[str, Any]]:
        """Возвращает участников чата (как для BASIC_GROUP, так и для SUPERGROUP)."""
        chat_info = self.get_chat_info_by_id(chat_id)
        if not chat_info:
            logger.error(f"Failed to get chat info by ID {chat_id}")
            return []

        ctype = chat_info["type"]["@type"]
        if ctype == ChatType.BASIC_GROUP.value:
            return self._get_basic_group_members(chat_info)
        elif ctype == ChatType.SUPERGROUP.value:
            return self._get_supergroup_members(chat_info["type"]["supergroup_id"])
        return []

    def _get_basic_group_members(self, chat_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Частный метод для получения участников BASIC_GROUP."""
        basic_group_id = chat_info["type"]["basic_group_id"]
        full_info = self._send_and_wait_for_response(
            {"@type": "getBasicGroupFullInfo", "basic_group_id": basic_group_id},
            success_condition="basicGroupFullInfo",
        )
        if full_info is None:
            return []
        return full_info.get("members", [])

    def _get_supergroup_members(self, supergroup_id: int) -> List[Dict[str, Any]]:
        """Частный метод для получения участников SUPERGROUP."""
        offset = 0
        limit = 200
        all_members = []

        while True:
            response = self._send_and_wait_for_response(
                {
                    "@type": "getSupergroupMembers",
                    "supergroup_id": supergroup_id,
                    "filter": {"@type": "supergroupMembersFilterRecent"},
                    "offset": offset,
                    "limit": limit,
                },
                success_condition="chatMembers",
            )
            if not response or "members" not in response:
                break

            members = response["members"]
            all_members.extend(members)

            if len(members) < limit:
                break
            offset += len(members)

        return all_members

    def get_users_common_chats_count_for_chat(
        self, chat_id: int, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[List[UserInfo]]:
        """
        Для каждого участника заданного чата считает, в скольких общих чатах (BASIC_GROUP/SUPERGROUP) он состоит с нами.

        :param chat_id: ID чата.
        :param progress_callback: Функция обратного вызова для обновления прогресса, если нужно.
        :return: Список UserInfo, или None при ошибке.
        """
        members = self.get_chat_members(chat_id)
        if not members:
            logger.error("Failed to get chat members.")
            return None

        results: List[UserInfo] = []
        total_members = len(members)

        for index, member in enumerate(members, start=1):
            if progress_callback:
                progress_callback(index, total_members)

            user_id = self._extract_user_id(member)
            if user_id is None or user_id == self._my_user_id:
                continue

            common_groups_response = self._send_and_wait_for_response(
                {
                    "@type": "getGroupsInCommon",
                    "user_id": user_id,
                    "offset_chat_id": 0,
                    "limit": COMMON_GROUPS_LIMIT,
                },
                success_condition="chats",
            )
            if common_groups_response is None:
                logger.error(f"Failed to get common groups for user_id: {user_id}")
                continue

            chat_ids = common_groups_response.get("chat_ids", [])
            results.append(
                UserInfo(
                    user_id=user_id,
                    username=self._get_tag_by_user_id(user_id),
                    name=self._get_name_by_user_id(user_id),
                    count=len(chat_ids),
                    common_group_ids=chat_ids,
                )
            )
        return results

    def _extract_user_id(self, member: Dict[str, Any]) -> Optional[int]:
        """
        Вспомогательный метод, достающий user_id из member.
        """
        member_id = member.get("member_id", {})
        if member_id.get("@type") == "messageSenderUser":
            return member_id.get("user_id")
        return None

    def _get_name_by_user_id(self, user_id: int) -> Optional[str]:
        """Возвращает first_name + last_name для user_id."""
        user = self._send_and_wait_for_response({"@type": "getUser", "user_id": user_id}, success_condition="user")
        if user is None:
            return None
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        return f"{first_name} {last_name}".strip()

    def _get_tag_by_user_id(self, user_id: int) -> Optional[str]:
        """Возвращает @username пользователя, если он есть."""
        user = self._send_and_wait_for_response({"@type": "getUser", "user_id": user_id}, success_condition="user")
        if user is None:
            return None
        usernames = user.get("usernames", {}).get("active_usernames", [])
        return f"@{usernames[0]}" if usernames else None

    def get_user_profile_photo(self, user_id: int) -> Optional[bytes]:
        """
        Возвращает фотографию профиля пользователя (small-версию), или None, если нет фото.
        """
        user_data = self._send_and_wait_for_response({"@type": "getUser", "user_id": user_id}, success_condition="user")
        if not user_data:
            return None

        profile_photo = user_data.get("profile_photo", {})
        file_id = profile_photo.get("small", {}).get("id")
        if file_id is None:
            return None

        return self._download_file(file_id)

    def get_chat_photo(self, chat_info: Dict[str, Any]) -> Optional[bytes]:
        """
        Возвращает small-фото чата (группы/супергруппы), или None, если нет фото.
        """
        if not chat_info or "photo" not in chat_info:
            return None

        photo = chat_info["photo"]
        file_id = photo.get("small", {}).get("id")
        if file_id is None:
            return None
        return self._download_file(file_id)

    def _download_file(self, file_id: int) -> Optional[bytes]:
        """Загружает файл по file_id и возвращает его содержимое в виде байтов."""
        file_response = self._send_and_wait_for_response(
            {"@type": "downloadFile", "file_id": file_id, "priority": DOWNLOAD_PRIORITY}, success_condition="file"
        )
        if not file_response:
            return None

        local_path = file_response.get("local", {}).get("path")
        if not local_path:
            return None

        try:
            with open(local_path, "rb") as f:
                return f.read()
        except OSError as e:
            logger.error(f"Failed to read file {local_path}: {e}")
            return None
