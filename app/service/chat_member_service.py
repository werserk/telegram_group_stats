import time
from typing import Dict, Optional, List, Any, Union, Callable

from loguru import logger

from app.service.client import TDLibClient


class ChatMemberService:
    RECEIVE_LOOP_TIMEOUT = 5
    MAX_COUNT_CHATS_RESPONSE = 100000
    MAX_COUNT_MEMBERS_RESPONSE = 100000

    def __init__(self, td_client: TDLibClient):
        self.td_client = td_client

    def _send_and_wait_for_response(
        self, request_data: Dict[str, Any], success_condition: Union[str, List[str], Callable[[Dict[str, Any]], bool]]
    ) -> Optional[Dict[str, Any]]:
        """
        Universal method for sending a request and waiting for a response.

        :param request_data: The request data to be sent through td_client.
        :param success_condition: Can be a string (@type), a list of types, or a
                                  function returning True if the desired event is received.
        :return: The event dictionary if the condition is met, None if there's an error or no response.
        """

        if isinstance(success_condition, str):

            def condition(event: Dict[str, Any]) -> bool:
                return event.get("@type") == success_condition

        elif isinstance(success_condition, list):

            def condition(event: Dict[str, Any]) -> bool:
                return event.get("@type") in success_condition

        elif callable(success_condition):
            condition = success_condition
        else:
            raise ValueError(
                f"Invalid success_condition type: {type(success_condition)}. Accepted types: str, list, Callable"
            )

        self.td_client.send(request_data)

        while True:
            event = self.td_client.receive()
            if event:
                if event.get("@type") == "error":
                    logger.error(f"Error: {event.get('message')}")
                    return None
                if condition(event):
                    return event
            else:
                time.sleep(self.RECEIVE_LOOP_TIMEOUT)

    def get_chat_id_by_username(self, username: str) -> Optional[int]:
        event = self._send_and_wait_for_response(
            {"@type": "searchPublicChat", "username": username}, success_condition="chat"
        )
        if event is not None:
            return event["id"]
        return None

    def get_chat_info_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        return self._send_and_wait_for_response({"@type": "getChat", "chat_id": chat_id}, success_condition="chat")

    def get_chats(self) -> Optional[List[Dict[str, Any]]]:
        event = self._send_and_wait_for_response(
            {"@type": "getChats", "limit": self.MAX_COUNT_CHATS_RESPONSE}, success_condition="chats"
        )

        if event is None:
            return None

        chat_ids = event["chat_ids"]
        chats = []
        for chat_id in chat_ids:
            chat_info = self.get_chat_info_by_id(chat_id)
            if chat_info is None:
                continue
            # Ensure it's a group type (basicGroup))
            chat_type = chat_info["type"]["@type"]
            if chat_type != "chatTypeBasicGroup":
                # Not a group chat, skip
                continue
            chat = {"id": chat_id, "name": chat_info["title"]}
            chats.append(chat)
        return chats

    def get_chat_members(self, chat_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve all users from a group chat (either basic group or supergroup).

        :param chat_id: The ID of the chat to retrieve members from.
        :return: A list of member objects or None if failed.
        """
        chat_info = self.get_chat_info_by_id(chat_id)
        if chat_info is None:
            return None

        basic_group_id = chat_info["type"]["basic_group_id"]
        full_info = self._send_and_wait_for_response(
            {"@type": "getBasicGroupFullInfo", "basic_group_id": basic_group_id}, success_condition="basicGroupFullInfo"
        )
        if full_info is None:
            return None
        # full_info["members"] is a list of { "@type": "chatMember", "member_id": {...}, ... }
        return full_info["members"]

    def get_common_groups_with_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve all common groups with a specified user.
        Since getGroupsInCommon may return only a part of the chats,
        you should call it repeatedly with new offsets until no more are returned.

        :param user_id: The user with whom we want common groups.
        :return: A list of chat IDs for common groups or None if failed.
        """
        offset_chat_id = 0

        response = self._send_and_wait_for_response(
            {
                "@type": "getGroupsInCommon",
                "user_id": user_id,
                "offset_chat_id": offset_chat_id,
                "limit": self.MAX_COUNT_CHATS_RESPONSE,
            },
            success_condition="chats",
        )

        if response is None:
            logger.error("Failed to get common groups")
            return None
        return response
