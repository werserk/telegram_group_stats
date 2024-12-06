# main.py

import os

from dotenv import load_dotenv

from app.service.client import TDLibClient
from app.service.chat_member_service import ChatMemberService

load_dotenv()


def main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    tdlib_client = TDLibClient(api_id=api_id, api_hash=api_hash)
    chat_member_service = ChatMemberService(tdlib_client)

    # chat_tag = input("Enter the chat username: ")
    # chat_id = chat_member_service.get_chat_id_by_username(chat_tag)
    # print(f"Chat ID: {chat_id}")
    # try:
    #     chat_id = int(chat_id)
    # except ValueError:
    #     print("Invalid chat ID. Please enter a numeric chat ID.")
    #     return

    chat_list = chat_member_service.get_chats()
    print(chat_list)


if __name__ == "__main__":
    main()
