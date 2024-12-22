import streamlit as st

from app.telegram.service import ChatMemberService


class AnalyticsPage:
    def __init__(self, chat_member_service: ChatMemberService):
        self.chat_member_service = chat_member_service

        @st.cache_data
        def _load_chats():
            return self.chat_member_service.get_chats()

        self._load_chats = _load_chats

    def show(self):
        st.title("Telegram Group Stats")

        chats = self._load_chats()
        if not chats:
            st.warning("No group chats found.")
            return

        search_query = st.text_input("Search group by name:")
        filtered_chats = [c for c in chats if search_query.lower() in c["name"].lower()] if search_query else chats

        if not filtered_chats:
            st.warning("No groups match the search query.")
            return

        selected_chat_name = st.selectbox(
            "Select a group chat:",
            options=[chat["name"] for chat in filtered_chats],
        )
        selected_chat = next((c for c in filtered_chats if c["name"] == selected_chat_name), None)

        if st.button("Run Analysis"):
            with st.spinner("Analyzing..."):
                stats = self.chat_member_service.get_users_common_chats_count_for_chat(
                    selected_chat["id"], show_progress=True
                )
                if stats is None:
                    st.error("Failed to get stats.")
                else:
                    sorted_stats = sorted(stats, key=lambda x: x["count"], reverse=True)

                    beautify_stats = {
                        "name": "Name",
                        "username": "Username",
                        "count": "Count of common chats",
                    }

                    prepared_stats = [{beautify_stats[k]: v for k, v in s.items()} for s in sorted_stats]

                    if len(prepared_stats) != 0:
                        st.success(f"Complete! Total members analyzed: {len(prepared_stats)}")
                        for i, prep_stat in enumerate(prepared_stats):
                            prep_stat["ID"] = str(i + 1)
                        st.dataframe(
                            prepared_stats,
                            column_order=[
                                "ID",
                                beautify_stats["username"],
                                beautify_stats["name"],
                                beautify_stats["count"],
                            ],
                        )
                    else:
                        st.warning("No member in group or does not have access.")
