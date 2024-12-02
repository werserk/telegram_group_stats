from typing import List

from app.tdlib_client import TDLibClient


class UserStats:
    def __init__(self, client: TDLibClient):
        self.client = client

    def get_group_members(self, chat_id: int) -> List[int]:
        query = {
            "@type": "getChatMembers",
            "chat_id": chat_id
        }
        response = self.client.execute(query)
        return [member['user_id'] for member in response.get("members", [])]
