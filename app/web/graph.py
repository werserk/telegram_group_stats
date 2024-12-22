# Filepath: app/web/graph.py

import base64

from loguru import logger
from pyvis.network import Network

from app.telegram.service import ChatMemberService


class GraphVisualizer:
    def __init__(self, stats, service: ChatMemberService):
        """
        Инициализирует визуализатор графа.

        :param stats: Список словарей с информацией о пользователях и их общих группах.
        :param service: Экземпляр ChatMemberService для получения информации о группах.
        """
        self.stats = stats
        self.service = service

    def create_pyvis_graph(self):
        """
        Создаёт граф Pyvis на основе статистики.

        :return: Объект Network из Pyvis.
        """
        net = Network(height="600px", width="100%", directed=False)
        net.barnes_hut()  # Использует алгоритм расположения узлов

        user_nodes = {}
        group_nodes = {}
        group_connection_counts = {}

        # Считаем количество соединений для каждой группы
        for user in self.stats:
            for group_id in user.get("common_group_ids", []):
                if group_id in group_connection_counts:
                    group_connection_counts[group_id] += 1
                else:
                    group_connection_counts[group_id] = 1

        for user in self.stats:
            user_id = user["user_id"]
            name = user["name"]
            username = user["username"]

            # Получаем аватарку пользователя
            photo_bytes = self.service.get_user_profile_photo(user_id)
            if photo_bytes is not None:
                photo_base64 = base64.b64encode(photo_bytes).decode()
                image_data = f"data:image/jpeg;base64,{photo_base64}"
            else:
                # Использовать дефолтное изображение
                image_data = ""

            # Добавляем узел пользователя с изображением
            net.add_node(
                user_id,
                label=f"{name}\n{username}",
                color={
                    "background": "white",  # Цвет фона
                    "border": "black",  # Цвет границы
                    "highlight": {
                        "background": "orange",
                        "border": "orange",
                        "borderWidth": 2,
                    },
                },
                shape="circularImage",
                image=image_data,
                size=60 + user.get("count", 0) * 2,
                font={
                    "size": 40 + user.get("count", 0) * 2,  # Размер шрифта
                    "face": "Tahoma",  # Тип шрифта
                    "color": "black",  # Цвет шрифта
                    "strokeWidth": 0,  # Толщина обводки текста
                },
            )
            user_nodes[user_id] = user

            # Добавляем узлы групп и связи
            for group_id in user.get("common_group_ids", []):
                if group_id not in group_nodes:
                    chat_info = self.service.get_chat_info_by_id(group_id)
                    if chat_info:
                        group_name = chat_info.get("title", f"Group {group_id}")
                        # Получаем аватарку группы
                        group_photo_bytes = self.service.get_chat_photo(chat_info)
                        if group_photo_bytes:
                            group_photo_base64 = base64.b64encode(group_photo_bytes).decode()
                            group_image_data = f"data:image/jpeg;base64,{group_photo_base64}"
                        else:
                            group_image_data = ""
                    else:
                        group_name = f"Group {group_id}"
                        group_image_data = ""
                    # Размер группы пропорционален количеству соединений
                    group_size = 60 + group_connection_counts.get(group_id, 0) * 3
                    # Добавляем узел группы с изображением
                    net.add_node(
                        group_id,
                        label=group_name,
                        color="green",
                        shape="circularImage",
                        image=group_image_data,
                        size=group_size,
                        font={
                            "size": 60 + group_connection_counts.get(group_id, 0) * 2,  # Размер шрифта
                            "face": "Sans-Serif",  # Тип шрифта
                            "color": "black",  # Цвет шрифта
                            "strokeWidth": 0,  # Толщина обводки текста
                        },
                    )
                    group_nodes[group_id] = group_name
                # Добавляем связь между пользователем и группой
                net.add_edge(
                    user_id,
                    group_id,
                    color={
                        "color": "gray",  # Основной цвет ребра
                        "highlight": "orange",  # Цвет подсветки ребра
                    },
                    width=5,
                )

        return net

    def save_and_return_graph_html(self, output_path="graph.html"):
        """
        Сохраняет граф в HTML-файл и возвращает путь к нему.

        :param output_path: Путь для сохранения HTML-файла.
        :return: Путь к сохранённому HTML-файлу.
        """
        net = self.create_pyvis_graph()
        net.save_graph(output_path)
        logger.info(f"Граф успешно сохранён в {output_path}")
        return output_path
