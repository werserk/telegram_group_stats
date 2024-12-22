import base64
from typing import Dict, List

from loguru import logger
from pyvis.network import Network

from app.constants import (
    COLOR_BLACK,
    COLOR_GRAY,
    COLOR_GREEN,
    COLOR_ORANGE,
    COLOR_WHITE,
    FONT_FACE_SANS,
    FONT_FACE_TAHOMA,
    GRAPH_DEFAULT_HEIGHT,
    GRAPH_DEFAULT_WIDTH,
    GRAPH_EDGE_WIDTH,
    GRAPH_FONT_SIZE_BASE,
    GRAPH_FONT_SIZE_FACTOR,
    GRAPH_GROUP_SIZE_FACTOR,
    GRAPH_NODE_SIZE_BASE,
    GRAPH_NODE_SIZE_FACTOR,
    SHAPE_CIRCULAR_IMAGE,
)
from app.telegram.service import ChatMemberService, UserInfo


class GraphVisualizer:
    """Builds and saves an interactive PyVis graph of user-group relationships."""

    def __init__(self, stats: List[UserInfo], service: ChatMemberService):
        self.stats = stats
        self.service = service

    def create_pyvis_graph(self) -> Network:
        net = Network(height=GRAPH_DEFAULT_HEIGHT, width=GRAPH_DEFAULT_WIDTH, directed=False)
        net.barnes_hut()
        user_nodes = {}
        group_nodes = {}
        group_connection_counts: Dict[int, int] = {}

        for user_info in self.stats:
            for group_id in user_info.common_group_ids:
                group_connection_counts[group_id] = group_connection_counts.get(group_id, 0) + 1

        for user_info in self.stats:
            user_id = user_info.user_id
            photo_bytes = self.service.get_user_profile_photo(user_id)
            if photo_bytes:
                photo_base64 = base64.b64encode(photo_bytes).decode()
                user_image_data = f"data:image/jpeg;base64,{photo_base64}"
            else:
                user_image_data = ""
            net.add_node(
                user_id,
                label=f"{user_info.name}\n{user_info.username}",
                color={
                    "background": COLOR_WHITE,
                    "border": COLOR_BLACK,
                    "highlight": {
                        "background": COLOR_ORANGE,
                        "border": COLOR_ORANGE,
                        "borderWidth": 2,
                    },
                },
                shape=SHAPE_CIRCULAR_IMAGE,
                image=user_image_data,
                size=GRAPH_NODE_SIZE_BASE + user_info.count * GRAPH_NODE_SIZE_FACTOR,
                font={
                    "size": GRAPH_FONT_SIZE_BASE + user_info.count * GRAPH_FONT_SIZE_FACTOR,
                    "face": FONT_FACE_TAHOMA,
                    "color": COLOR_BLACK,
                    "strokeWidth": 0,
                },
            )
            user_nodes[user_id] = user_info

            for group_id in user_info.common_group_ids:
                if group_id not in group_nodes:
                    chat_info = self.service.get_chat_info_by_id(group_id)
                    if chat_info:
                        group_name = chat_info.get("title", f"Group {group_id}")
                        group_photo_bytes = self.service.get_chat_photo(chat_info)
                        if group_photo_bytes:
                            group_photo_base64 = base64.b64encode(group_photo_bytes).decode()
                            group_image_data = f"data:image/jpeg;base64,{group_photo_base64}"
                        else:
                            group_image_data = ""
                    else:
                        group_name = f"Group {group_id}"
                        group_image_data = ""
                    group_size = (
                        GRAPH_NODE_SIZE_BASE + group_connection_counts.get(group_id, 0) * GRAPH_GROUP_SIZE_FACTOR
                    )
                    net.add_node(
                        group_id,
                        label=group_name,
                        color=COLOR_GREEN,
                        shape=SHAPE_CIRCULAR_IMAGE,
                        image=group_image_data,
                        size=group_size,
                        font={
                            "size": GRAPH_FONT_SIZE_BASE
                            + group_connection_counts.get(group_id, 0) * GRAPH_FONT_SIZE_FACTOR,
                            "face": FONT_FACE_SANS,
                            "color": COLOR_BLACK,
                            "strokeWidth": 0,
                        },
                    )
                    group_nodes[group_id] = group_name
                net.add_edge(
                    user_id,
                    group_id,
                    color={"color": COLOR_GRAY, "highlight": COLOR_ORANGE},
                    width=GRAPH_EDGE_WIDTH,
                )
        return net

    def save_and_return_graph_html(self, output_path: str = "graph.html") -> str:
        net = self.create_pyvis_graph()
        net.save_graph(output_path)
        logger.info(f"Graph saved to {output_path}")
        return output_path
