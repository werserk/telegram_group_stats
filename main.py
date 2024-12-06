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
    chat_example = chat_list[0]
    print(f"Chat example: {chat_example}")
    print(chat_list[:50])

    stats = chat_member_service.get_users_common_chats_count_for_chat(chat_example["id"])
    print(stats)


if __name__ == "__main__":
    main()
