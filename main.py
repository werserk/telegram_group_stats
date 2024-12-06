# main.py

import os

from dotenv import load_dotenv

from app.service.chat_member_service import ChatMemberService
from app.service.client import TDLibClient

load_dotenv()


def main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    tdlib_client = TDLibClient(api_id=api_id, api_hash=api_hash)
    chat_member_service = ChatMemberService(tdlib_client)

    chat_list = chat_member_service.get_chats()
    chat_example = chat_list[1]
    print(f"Chat example: {chat_example}")

    members = chat_member_service.get_chat_members(chat_example["id"])
    print(f"Members: {members}")

    for member in members:
        common_groups = chat_member_service.get_common_groups_with_user(member["member_id"]["user_id"])
        if common_groups is None:
            print(f"Failed to get common groups with user {member['member_id']['user_id']}")
            continue
        print(f"{member['member_id']['user_id']} - {common_groups['total_count']}")


if __name__ == "__main__":
    main()
