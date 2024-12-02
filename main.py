from app.group_analyzer import GroupAnalyzer
from app.tdlib_client import TDLibClient
from app.top_users import TopUsers
from app.user_stats import UserStats


def main():
    tdlib_client = TDLibClient("libtdjson.so", api_id=123456, api_hash="your_api_hash")
    group_analyzer = GroupAnalyzer(tdlib_client)
    user_stats = UserStats(tdlib_client)
    top_users = TopUsers(group_analyzer, user_stats)

    user_id = 123456789  # Your user ID
    top_users_list = top_users.get_top_users(user_id)

    for user in top_users_list:
        print(f"User ID: {user['user_id']}, Common Groups: {user['common_groups_count']}")


if __name__ == "__main__":
    main()
