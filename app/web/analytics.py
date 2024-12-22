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

        with st.spinner("Retrieving chat members..."):
            members = self.chat_member_service.get_chat_members(selected_chat["id"])

        if not members:
            st.warning("No members in this chat or failed to retrieve.")
            return

        # 2) Создаём прогресс-бар (анализ участников)
        progress_bar = st.progress(0, text="Analyzing chat members...")

        def progress_callback(current_index: int, total_count: int) -> None:
            """Колбэк для обновления прогресс-бара при анализе."""
            progress_bar.progress(
                current_index / total_count,
                text=f"Analyzing member {current_index}/{total_count}...",
            )

        # 3) Анализируем
        stats = self.chat_member_service.get_users_common_chats_count_for_chat(
            chat_id=selected_chat["id"], progress_callback=progress_callback
        )

        if stats is None:
            st.error("Failed to get stats.")
            return

        sorted_stats = sorted(stats, key=lambda x: x["count"], reverse=True)

        beautify_stats = {
            "name": "Name",
            "username": "Username",
            "count": "Count of Common Chats",
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
            st.warning("No relevant members or no access.")
