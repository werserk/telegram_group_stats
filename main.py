import os

import streamlit as st
from dotenv import load_dotenv

from app.telegram.client import TDLibClient
from app.telegram.processor import ChatMemberService

load_dotenv()


@st.cache_resource
def init_services():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    tdlib_client = TDLibClient(api_id=api_id, api_hash=api_hash)
    chat_member_service = ChatMemberService(tdlib_client)
    return chat_member_service


def main():
    st.title("Telegram Group Stats")

    chat_member_service = init_services()

    @st.cache_data
    def load_chats():
        return chat_member_service.get_chats()

    chats = load_chats()
    if chats is None or len(chats) == 0:
        st.warning("No group chats found.")
        st.stop()

    search_query = st.text_input("Search group by name:")

    if search_query:
        filtered_chats = [c for c in chats if search_query.lower() in c["name"].lower()]
    else:
        filtered_chats = chats

    if not filtered_chats:
        st.warning("No groups match the search query.")
        st.stop()

    selected_chat_name = st.selectbox("Select a group chat:", options=[chat["name"] for chat in filtered_chats])

    selected_chat = next((c for c in filtered_chats if c["name"] == selected_chat_name), None)

    if st.button("Run Analysis"):
        with st.spinner("Analyzing..."):
            stats = chat_member_service.get_users_common_chats_count_for_chat(selected_chat["id"])
            if stats is None:
                st.error("Failed to get stats.")
                return
            sorted_stats = sorted(stats, key=lambda x: x["count_of_common_chats"], reverse=True)
            st.success("Analysis completed!")
            st.dataframe(sorted_stats)


if __name__ == "__main__":
    main()
