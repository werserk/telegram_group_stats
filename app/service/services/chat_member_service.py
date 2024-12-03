# app/service/services/chat_member_service.py

import time
from typing import List, Dict, Optional

from app.service.client import TDLibClient


class ChatMemberService:
    RECEIVE_LOOP_TIMEOUT = 5

    def __init__(self, td_client: TDLibClient):
        self.td_client = td_client

    def get_chat_id_by_username(self, username: str) -> Optional[int]:
        # Отправляем запрос searchPublicChat
        self.td_client.send({
            "@type": "searchPublicChat",
            "username": username
        })

        while True:
            event = self.td_client.receive()
            if event:
                if event["@type"] == "chat":
                    chat_info = event
                    chat_id = chat_info["id"]
                    return chat_id
                elif event["@type"] == "error":
                    print(f"Ошибка: {event['message']}")
                    return None
            else:
                time.sleep(ChatMemberService.RECEIVE_LOOP_TIMEOUT)

    def get_chat_members(self, chat_id: int) -> List[Dict]:
        # First, get the chat information to determine the chat type
        self.td_client.send({
            "@type": "getChat",
            "chat_id": chat_id
        })

        chat_info = {}
        while True:
            event = self.td_client.receive()
            if event:
                if event["@type"] == "chat" and event["id"] == chat_id:
                    chat_info = event
                    break
                elif event["@type"] == "error":
                    print(f"Error: {event}")
                    return []
            else:
                time.sleep(ChatMemberService.RECEIVE_LOOP_TIMEOUT)

        members = []

        if chat_info["type"]["@type"] == "chatTypeSupergroup":
            supergroup_id = chat_info["type"]["supergroup_id"]
            offset = 0
            limit = 200  # Maximum allowed by Telegram

            while True:
                self.td_client.send({
                    "@type": "getSupergroupMembers",
                    "supergroup_id": supergroup_id,
                    "offset": offset,
                    "limit": limit,
                    "filter": {"@type": "supergroupMembersFilterRecent"}
                })

                while True:
                    event = self.td_client.receive()
                    if event:
                        if event["@type"] == "supergroupMembers":
                            members.extend(event["members"])
                            if len(event["members"]) < limit:
                                return members
                            else:
                                offset += limit
                                break
                        elif event["@type"] == "error":
                            print(f"Error: {event}")
                            return members
                    else:
                        time.sleep(ChatMemberService.RECEIVE_LOOP_TIMEOUT)

        elif chat_info["type"]["@type"] == "chatTypeBasicGroup":
            basic_group_id = chat_info["type"]["basic_group_id"]
            self.td_client.send({
                "@type": "getBasicGroupFullInfo",
                "basic_group_id": basic_group_id
            })

            while True:
                event = self.td_client.receive()
                if event:
                    if event["@type"] == "basicGroupFullInfo" and event["basic_group_id"] == basic_group_id:
                        members = event["members"]
                        return members
                    elif event["@type"] == "error":
                        print(f"Error: {event}")
                        return []
                else:
                    time.sleep(ChatMemberService.RECEIVE_LOOP_TIMEOUT)

        elif chat_info["type"]["@type"] == "chatTypePrivate":
            # For private chats, the chat is between the user and another person
            members.append({"user_id": chat_info["type"]["user_id"]})
            return members

        else:
            print(f"Unsupported chat type: {chat_info['type']['@type']}")
            return []
