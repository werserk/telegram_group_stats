import os
from typing import Any, Dict, List

import streamlit as st

from app.telegram.service import ChatMemberService, UserInfo
from app.web.graph import GraphVisualizer


class AnalyticsPage:
    def __init__(self, chat_member_service: ChatMemberService) -> None:
        self.chat_member_service = chat_member_service

        @st.cache_data
        def _load_chats():
            return self.chat_member_service.get_chats()

        self._load_chats = _load_chats
        self._stats: List[UserInfo] = []

    def show(self) -> None:
        st.title("Telegram Group Stats")
        chats = self._load_chats()
        if not chats:
            st.warning("No group chats found.")
            return

        if not chats:
            st.warning("No groups match the search query.")
            return

        selected_chat_name = st.selectbox(
            "Select a group chat:",
            options=[chat["name"] for chat in chats],
        )
        selected_chat = next((c for c in chats if c["name"] == selected_chat_name), None)
        if not selected_chat:
            st.warning("No groups match the search query.")
            return
        with st.spinner("Retrieving chat members..."):
            members = self.chat_member_service.get_chat_members(selected_chat["id"])
        if not members:
            st.warning("Don't have permission to members of this chat. Can't analyze.")
            return

        if st.button("Analyze chat"):
            self.analyze_chat(selected_chat)

        if not self._stats:
            return

        with st.expander("Members", expanded=True):
            self.visualize_chat_members(self._stats)

        with st.expander("Graph", expanded=False):
            self.visualize_graph(self._stats)

    @staticmethod
    def visualize_chat_members(stats: List[UserInfo]) -> None:
        sorted_stats = sorted(stats, key=lambda x: x.count, reverse=True)
        rows = []
        for user_stat in sorted_stats:
            rows.append(
                {"Name": user_stat.name, "Username": user_stat.username, "Count of Common Chats": user_stat.count}
            )
        if rows:
            for index, row in enumerate(rows):
                row["ID"] = str(index + 1)
            st.dataframe(rows, column_order=["ID", "Username", "Name", "Count of Common Chats"])

    def analyze_chat(self, chat: Dict[str, Any]) -> None:
        progress_bar = st.progress(0, text="Analyzing chat members...")

        def progress_callback(current_index: int, total_count: int) -> None:
            progress_text = f"Analyzing member {current_index}/{total_count - 1}..."
            progress_bar.progress(current_index / total_count, text=progress_text)
            if current_index == total_count:
                progress_bar.empty()

        result = self.chat_member_service.get_users_common_chats_count_for_chat(
            chat_id=chat["id"], progress_callback=progress_callback
        )
        if result is None:
            st.error("Failed to get stats.")
            return
        self._stats = result
        st.success("Chat members analyzed.")

    def visualize_graph(self, stats: List[UserInfo]) -> None:
        with st.spinner("Generating graph..."):
            graph_visualizer = GraphVisualizer(stats, self.chat_member_service)
            graph_path = graph_visualizer.save_and_return_graph_html()
            if graph_path and os.path.exists(graph_path):
                with open(graph_path, "r", encoding="utf-8") as file_obj:
                    source_code = file_obj.read()
                st.components.v1.html(source_code, height=600, scrolling=True)
            else:
                st.error("Failed to generate graph.")
