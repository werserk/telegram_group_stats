# Filepath: app/web/graph.py

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

            # Добавляем узел пользователя
            net.add_node(
                user_id,
                label=f"{name} ({username})",
                color="blue",
                shape="dot",
                size=15 + user.get("count", 0) * 2,  # Можно увеличить размер на основе количества
            )
            user_nodes[user_id] = user

            # Добавляем узлы групп и связи
            for group_id in user.get("common_group_ids", []):
                if group_id not in group_nodes:
                    chat_info = self.service.get_chat_info_by_id(group_id)
                    if chat_info:
                        group_name = chat_info.get("title", f"Group {group_id}")
                    else:
                        group_name = f"Group {group_id}"
                    # Размер группы пропорционален количеству соединений
                    group_size = 20 + group_connection_counts.get(group_id, 0)
                    # Добавляем узел группы
                    net.add_node(
                        group_id,
                        label=group_name,
                        color="green",
                        shape="square",
                        size=group_size,
                    )
                    group_nodes[group_id] = group_name
                # Добавляем связь между пользователем и группой
                net.add_edge(user_id, group_id, color="gray", width=1)

        return net

    def save_and_return_graph_html(self, output_path="graph.html"):
        """
        Сохраняет граф в HTML-файл и возвращает путь к нему.

        :param output_path: Путь для сохранения HTML-файла.
        :return: Путь к сохранённому HTML-файлу.
        """
        try:
            net = self.create_pyvis_graph()
            net.save_graph(output_path)
            logger.info(f"Граф успешно сохранён в {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Ошибка при сохранении графа: {e}")
            return None
