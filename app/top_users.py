from collections import defaultdict
from typing import List

from app.group_analyzer import GroupAnalyzer
from app.user_stats import UserStats


class TopUsers:
    def __init__(self, group_analyzer: GroupAnalyzer, user_stats: UserStats):
        self.group_analyzer = group_analyzer
        self.user_stats = user_stats

    def get_top_users(self, user_id: int, limit: int = 10) -> List[dict]:
        common_groups = self.group_analyzer.get_common_groups(user_id, limit=100)
        user_groups_count = defaultdict(int)

        for group in common_groups:
            chat_id = group["id"]
            members = self.user_stats.get_group_members(chat_id)
            for member_id in members:
                if member_id != user_id:
                    user_groups_count[member_id] += 1

        sorted_users = sorted(user_groups_count.items(), key=lambda x: x[1], reverse=True)
        return [{"user_id": user, "common_groups_count": count} for user, count in sorted_users[:limit]]
