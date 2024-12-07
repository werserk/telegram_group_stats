import os

from dotenv import load_dotenv

from app.telegram.client import TDLibClient
from app.telegram.processor import ChatMemberService

load_dotenv()


def main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    tdlib_client = TDLibClient(api_id=api_id, api_hash=api_hash)
    chat_member_service = ChatMemberService(tdlib_client)

    chat_id = chat_member_service.get_chat_id_by_username("@test_group_chat_werserk")
    print(chat_id)

    my_id = chat_member_service.get_my_user_id()
    print(my_id)

    member_id = chat_member_service.get_user_id_by_username("@sofya_salyaeva")
    print(member_id)


if __name__ == "__main__":
    main()
