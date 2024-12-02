from typing import List

from app.tdlib_client import TDLibClient


class GroupAnalyzer:
    def __init__(self, client: TDLibClient):
        self.client = client

    def get_common_groups(self, user_id: int, limit: int = 100) -> List[dict]:
        return self.client.get_groups_in_common(user_id, limit=limit)
