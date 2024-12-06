import time
from typing import Dict, Optional, List, Any, Union, Callable

from loguru import logger

from app.service.client import TDLibClient


class ChatMemberService:
    RECEIVE_LOOP_TIMEOUT = 5
    MAX_COUNT_CHATS = 100000

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
        :return: The event dictionary if the condition is met, None if there's an error or timeout.
        """

        if isinstance(success_condition, str):

            def condition(event: Dict[str, Any]) -> bool:
                return event.get("@type") == success_condition

        elif isinstance(success_condition, list):

            def condition(event: Dict[str, Any]) -> bool:
                return event.get("@type") in success_condition

        elif isinstance(success_condition, Callable):
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
                    logger.error(f"Error: {event['message']}")
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
            {"@type": "getChats", "limit": self.MAX_COUNT_CHATS}, success_condition="chats"
        )

        if event is None:
            return None

        chat_ids = event["chat_ids"]
        chats = []
        for chat_id in chat_ids:
            chat_info = self.get_chat_info_by_id(chat_id)
            if chat_info is None:
                continue
            if "Group" not in chat_info["type"]["@type"]:
                continue
            chat = {"id": chat_id, "name": chat_info["title"]}
            chats.append(chat)
        return chats
