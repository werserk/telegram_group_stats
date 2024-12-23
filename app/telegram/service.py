import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger

from app.constants import (
    COMMON_GROUPS_LIMIT,
    DOWNLOAD_PRIORITY,
    MAX_COUNT_CHATS_RESPONSE,
    RECEIVE_LOOP_TIMEOUT,
    SUPERGROUP_FETCH_LIMIT,
    ChatType,
)
from app.telegram.client import TDLibClient

logging.basicConfig(level=logging.INFO)  # Set basic logging level


@dataclass
class UserInfo:
    user_id: int
    username: Optional[str] = None
    name: Optional[str] = None
    count: int = 0
    common_group_ids: List[int] = field(default_factory=list)


class ChatMemberService:
    """High-level operations on chats/members with TDLibClient."""

    def __init__(self, td_client: TDLibClient) -> None:
        self._td_client = td_client
        self._my_user_id: Optional[int] = self._init_my_user_id()

    @property
    def my_user_id(self) -> Optional[int]:
        return self._my_user_id

    def _init_my_user_id(self) -> Optional[int]:
        event = self._send_and_wait_for_response({"@type": "getMe"}, success_condition="user")
        if not event:
            logger.error("Failed to retrieve current user info")
            return None
        return event.get("id")

    def _send_and_wait_for_response(
        self,
        request_data: Dict[str, Any],
        success_condition: Union[str, List[str], Callable[[Dict[str, Any]], bool]],
        timeout: float = RECEIVE_LOOP_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """Sends a request and waits for a response matching success_condition."""

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
            response = self._td_client.receive()
            if response is None:
                time.sleep(timeout)
                continue
            if response.get("@type") == "error":
                logger.error(f"TDLib error: {response.get('message')}")
                return None
            if is_successful(response):
                return response

    def get_chat_id_by_username(self, username: str) -> Optional[int]:
        event = self._send_and_wait_for_response(
            {"@type": "searchPublicChat", "username": username}, success_condition="chat"
        )
        if event:
            return event.get("id")
        return None

    def get_chat_info_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        return self._send_and_wait_for_response({"@type": "getChat", "chat_id": chat_id}, success_condition="chat")

    def get_chats(self) -> List[Dict[str, Any]]:
        event = self._send_and_wait_for_response(
            {"@type": "getChats", "limit": MAX_COUNT_CHATS_RESPONSE}, success_condition="chats"
        )
        if event is None:
            return []
        chat_ids = event.get("chat_ids", [])
        result = []
        for cid in chat_ids:
            info = self.get_chat_info_by_id(cid)
            if not info:
                continue
            chat_type = info["type"]["@type"]
            if chat_type not in (ChatType.BASIC_GROUP.value, ChatType.SUPERGROUP.value):
                continue
            result.append({"id": cid, "name": info.get("title", "Unknown")})
        return result

    def get_chat_members(self, chat_id: int) -> List[Dict[str, Any]]:
        chat_info = self.get_chat_info_by_id(chat_id)
        if not chat_info:
            logger.error(f"Failed to get chat info for id={chat_id}")
            return []
        chat_type = chat_info["type"]["@type"]
        if chat_type == ChatType.BASIC_GROUP.value:
            return self._get_basic_group_members(chat_info)
        elif chat_type == ChatType.SUPERGROUP.value:
            return self._get_supergroup_members(chat_info["type"]["supergroup_id"])
        return []

    def _get_basic_group_members(self, chat_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        basic_group_id = chat_info["type"]["basic_group_id"]
        full_info = self._send_and_wait_for_response(
            {"@type": "getBasicGroupFullInfo", "basic_group_id": basic_group_id},
            success_condition="basicGroupFullInfo",
        )
        if full_info is None:
            return []
        return full_info.get("members", [])

    def _get_supergroup_members(self, supergroup_id: int) -> List[Dict[str, Any]]:
        offset = 0
        limit = SUPERGROUP_FETCH_LIMIT
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
            members_chunk = response["members"]
            all_members.extend(members_chunk)
            if len(members_chunk) < limit:
                break
            offset += len(members_chunk)
        return all_members

    def get_users_common_chats_count_for_chat(
        self, chat_id: int, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[List[UserInfo]]:
        members = self.get_chat_members(chat_id)
        if not members:
            logger.error("Failed to get chat members")
            return None
        result: List[UserInfo] = []
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
                logger.error(f"Failed to get common groups for user_id={user_id}")
                continue
            common_ids = common_groups_response.get("chat_ids", [])
            user_info = UserInfo(
                user_id=user_id,
                username=self._get_tag_by_user_id(user_id),
                name=self._get_name_by_user_id(user_id),
                count=len(common_ids),
                common_group_ids=common_ids,
            )
            result.append(user_info)
        return result

    def _extract_user_id(self, member: Dict[str, Any]) -> Optional[int]:
        member_id_obj = member.get("member_id", {})
        if member_id_obj.get("@type") == "messageSenderUser":
            return member_id_obj.get("user_id")
        return None

    def _get_name_by_user_id(self, user_id: int) -> Optional[str]:
        user_response = self._send_and_wait_for_response(
            {"@type": "getUser", "user_id": user_id}, success_condition="user"
        )
        if user_response is None:
            return None
        first_name = user_response.get("first_name", "")
        last_name = user_response.get("last_name", "")
        return f"{first_name} {last_name}".strip()

    def _get_tag_by_user_id(self, user_id: int) -> Optional[str]:
        user_response = self._send_and_wait_for_response(
            {"@type": "getUser", "user_id": user_id}, success_condition="user"
        )
        if user_response is None:
            return None
        active_usernames = user_response.get("usernames", {}).get("active_usernames", [])
        if not active_usernames:
            return None
        return f"@{active_usernames[0]}"

    def get_user_profile_photo(self, user_id: int) -> Optional[bytes]:
        user_data = self._send_and_wait_for_response(
            {"@type": "getUser", "user_id": user_id},
            success_condition="user",
        )
        if not user_data:
            return None
        profile_photo = user_data.get("profile_photo", {})
        file_id = profile_photo.get("small", {}).get("id")
        if file_id is None:
            return None
        return self._download_file(file_id)

    def get_chat_photo(self, chat_info: Dict[str, Any]) -> Optional[bytes]:
        if not chat_info or "photo" not in chat_info:
            return None
        photo_obj = chat_info["photo"]
        file_id = photo_obj.get("small", {}).get("id")
        if file_id is None:
            return None
        return self._download_file(file_id)

    def _download_file(self, file_id: int) -> Optional[bytes]:
        response = self._send_and_wait_for_response(
            {"@type": "downloadFile", "file_id": file_id, "priority": DOWNLOAD_PRIORITY},
            success_condition="file",
        )
        if not response:
            return None
        local_path = response.get("local", {}).get("path")
        if not local_path:
            return None
        try:
            with open(local_path, "rb") as file_obj:
                return file_obj.read()
        except OSError as err:
            logger.error(f"Failed to read file {local_path}: {err}")
            return None
