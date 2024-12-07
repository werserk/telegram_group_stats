import time
from typing import Any, Callable, Dict, List, Optional, Union

from loguru import logger

from app.telegram.client import TDLibClient


class ChatMemberService:
    RECEIVE_LOOP_TIMEOUT = 5
    MAX_COUNT_CHATS_RESPONSE = 100000
    MAX_COUNT_MEMBERS_RESPONSE = 100000

    def __init__(self, td_client: TDLibClient):
        """
        Initialize the ChatMemberService.

        :param td_client: An instance of TDLibClient for sending and receiving requests.
        """
        self.td_client = td_client
        self.__my_user_id = self.get_my_user_id()

    def get_my_user_id(self) -> Optional[int]:
        """
        Retrieve the current user's ID and store it for future checks.

        :return: The user ID of the current authenticated user, or None if failed.
        """
        event = self._send_and_wait_for_response({"@type": "getMe"}, success_condition="user")
        if event is None:
            logger.error("Failed to retrieve current user info.")
            return None
        return event.get("id")

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """
        Retrieve the user ID of a given username.

        :param username: The username to retrieve the user ID for.
        :return: The user ID of the user with the given username, or None if not found.
        """
        event = self._send_and_wait_for_response(
            {"@type": "searchPublicChat", "username": username}, success_condition="chat"
        )
        if event is None:
            logger.error(f"Failed to retrieve user ID for username: {username}")
            return None
        return event.get("id")

    def _send_and_wait_for_response(
        self, request_data: Dict[str, Any], success_condition: Union[str, List[str], Callable[[Dict[str, Any]], bool]]
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a request and waits for a response that meets the success_condition.

        :param request_data: The request data to be sent through td_client.
        :param success_condition: Can be a string (@type), a list of @types, or a callable that checks the event.
        :return: The event dictionary if the condition is met, None otherwise.
        """
        condition: Callable[[Dict[str, Any]], bool]

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
        """
        Retrieve the chat ID for a given username.

        :param username: The username of the public chat.
        :return: The chat ID if found, None otherwise.
        """
        event = self._send_and_wait_for_response(
            {"@type": "searchPublicChat", "username": username}, success_condition="chat"
        )
        if event is not None:
            return event["id"]
        return None

    def get_chat_info_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve chat information by its ID.

        :param chat_id: The ID of the chat.
        :return: A dictionary with chat information if found, None otherwise.
        """
        return self._send_and_wait_for_response({"@type": "getChat", "chat_id": chat_id}, success_condition="chat")

    def get_chats(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve a list of all group chats.

        :return: A list of dictionaries, each containing chat ID and title, or None if no chats are found.
        """
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
            chat_type = chat_info["type"]["@type"]
            if chat_type != "chatTypeBasicGroup":
                continue
            chat = {"id": chat_id, "name": chat_info["title"]}
            chats.append(chat)
        return chats

    def get_chat_members(self, chat_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve all members from a basic group chat.

        :param chat_id: The ID of the group chat.
        :return: A list of member objects or None if unable to retrieve members.
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
        return full_info["members"]

    def get_common_groups_with_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve all common groups with a specified user.

        :param user_id: The user ID for which to find common groups.
        :return: A dictionary containing common group IDs or None if the operation fails.
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

    def get_name_by_user_id(self, user_id: int) -> Optional[str]:
        """
        Retrieve the username of a user by their ID.

        :param user_id: The ID of the user.
        :return: The username if found, None otherwise.
        """
        user = self._send_and_wait_for_response({"@type": "getUser", "user_id": user_id}, success_condition="user")
        if user is None:
            return None
        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        return f"{first_name} {last_name}"

    def get_users_common_chats_count_for_chat(self, chat_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        For each user in the specified chat, find how many common group chats are shared.
        If the user_id is the same as our own ID, skip or handle accordingly.

        :param chat_id: The ID of the group chat.
        :return: A list of dictionaries of the form {"user_id": int, "count_of_common_chats": int}, or None on failure.
        """
        members = self.get_chat_members(chat_id)
        if members is None:
            logger.error("Failed to get chat members.")
            return None

        results = []
        for member in members:
            member_id = member.get("member_id", {})
            if member_id.get("@type") == "messageSenderUser":
                user_id = member_id.get("user_id")
                if user_id is None:
                    continue

                if user_id == self.__my_user_id:
                    continue

                common_groups_response = self.get_common_groups_with_user(user_id)
                if common_groups_response is None:
                    logger.error(f"Failed to get common groups for user_id: {user_id}")
                    continue

                chat_ids = common_groups_response.get("chat_ids", [])
                result_item = {
                    "name": self.get_name_by_user_id(user_id),
                    "count": len(chat_ids),
                }
                results.append(result_item)

        return results
