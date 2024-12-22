# Filepath: app/web/analytics.py

import os
from typing import Any, Dict, List

import streamlit as st

from app.telegram.service import ChatMemberService, UserInfo
from app.web.graph import GraphVisualizer


class AnalyticsPage:
    def __init__(self, chat_member_service: ChatMemberService):
        self.chat_member_service = chat_member_service

        @st.cache_data
        def _load_chats():
            return self.chat_member_service.get_chats()

        self._load_chats = _load_chats
        self._stats: List[UserInfo] = []

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

        if st.button("Analyze chat"):
            self.analyze_chat(selected_chat)

        with st.expander("Members", expanded=True):
            self.visualize_chat_members(self._stats)

        with st.expander("Graph", expanded=False):
            self.visualize_graph(self._stats)

    @staticmethod
    def visualize_chat_members(stats: List[UserInfo]) -> None:
        sorted_stats = sorted(stats, key=lambda x: x.count, reverse=True)

        prepared_stats = [
            {
                "Name": stat.name,
                "Username": stat.username,
                "Count of Common Chats": stat.count,
            }
            for stat in sorted_stats
        ]
        # Добавляем "ID" для нумерации
        if len(prepared_stats) != 0:
            for i, prep_stat in enumerate(prepared_stats):
                prep_stat["ID"] = str(i + 1)
            # Изменяем порядок столбцов для отображения ID
            st.dataframe(
                prepared_stats,
                column_order=[
                    "ID",
                    "Username",
                    "Name",
                    "Count of Common Chats",
                ],
            )
        else:
            st.warning("No relevant members or no access.")

    def analyze_chat(self, chat: Dict[str, Any]) -> None:
        # Создаём прогресс-бар (анализ участников)
        progress_bar = st.progress(0, text="Analyzing chat members...")

        def progress_callback(current_index: int, total_count: int) -> None:
            """Колбэк для обновления прогресс-бара при анализе."""

            progress_text = f"Analyzing member {current_index}/{total_count - 1}..."  # -1 для исключения себя
            progress_bar.progress(
                current_index / total_count,
                text=progress_text,
            )
            if current_index == total_count:
                progress_bar.empty()

        # Анализируем
        response = self.chat_member_service.get_users_common_chats_count_for_chat(
            chat_id=chat["id"], progress_callback=progress_callback
        )

        if response is None:
            st.error("Failed to get stats.")
            return

        self._stats = response
        st.success("Chat members analyzed.")

    def visualize_graph(self, stats: List[UserInfo]):
        with st.spinner("Generating graph..."):
            graph_visualizer = GraphVisualizer(stats, self.chat_member_service)
            graph_path = graph_visualizer.save_and_return_graph_html()
            if graph_path and os.path.exists(graph_path):
                html_file = open(graph_path, "r", encoding="utf-8")
                source_code = html_file.read()
                st.components.v1.html(source_code, height=600, scrolling=True)
            else:
                st.error("Failed to generate graph.")
