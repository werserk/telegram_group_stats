# main.py

import os

from dotenv import load_dotenv

from app.service.client import TDLibClient
from app.service.services.chat_member_service import ChatMemberService

load_dotenv()


def main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    tdlib_client = TDLibClient(api_id=api_id, api_hash=api_hash)
    chat_member_service = ChatMemberService(tdlib_client)

    # chat_tag = input("Enter the chat username: ")
    # chat_id = chat_member_service.get_chat_id_by_username(chat_tag)
    # print(f"Chat ID: {chat_id}")

    chat_id_input = input("Enter the chat ID: ")
    try:
        chat_id = int(chat_id_input)
    except ValueError:
        print("Invalid chat ID. Please enter a numeric chat ID.")
        return

    members = chat_member_service.get_chat_members(chat_id)

    print(f"Total members in chat {chat_id}: {len(members)}")
    for member in members:
        user_id = member["user_id"]
        print(f"User ID: {user_id}")


if __name__ == "__main__":
    main()
