import os
import time
from typing import List, Tuple

import rclpy
from rclpy.node import Node


def _fmt_list(items: List[str], max_items: int = 200) -> str:
    if not items:
        return "(none)"
    shown = items[:max_items]
    suffix = "" if len(items) <= max_items else f" ... (+{len(items) - max_items} more)"
    return "\n".join(shown) + suffix


def main() -> None:
    print("ENV ROS_DOMAIN_ID=", os.environ.get("ROS_DOMAIN_ID"))
    print("ENV ROS_LOCALHOST_ONLY=", os.environ.get("ROS_LOCALHOST_ONLY"))
    print("ENV ROS_DISCOVERY_SERVER=", os.environ.get("ROS_DISCOVERY_SERVER"))
    print("ENV RMW_IMPLEMENTATION=", os.environ.get("RMW_IMPLEMENTATION"))
    print("ENV FASTDDS_BUILTIN_TRANSPORTS=", os.environ.get("FASTDDS_BUILTIN_TRANSPORTS"))

    rclpy.init()
    node = Node("win_graph_dump")

    # Give DDS discovery a moment and let rclpy process graph events.
    start = time.time()
    while time.time() - start < 2.0:
        rclpy.spin_once(node, timeout_sec=0.1)

    nodes: List[str] = []
    try:
        for name, namespace in node.get_node_names_and_namespaces():
            nodes.append(f"{namespace}{name}")
    except Exception as exc:  # noqa: BLE001
        nodes.append(f"(error reading nodes: {exc})")

    topics: List[Tuple[str, List[str]]] = []
    try:
        topics = node.get_topic_names_and_types()
    except Exception as exc:  # noqa: BLE001
        topics = [("(error reading topics)", [str(exc)])]

    nodes_sorted = sorted(set(nodes))
    topics_sorted = sorted(topics, key=lambda t: t[0])

    print("\n--- nodes ---")
    print(_fmt_list(nodes_sorted))

    print("\n--- topics ---")
    if not topics_sorted:
        print("(none)")
    else:
        lines: List[str] = []
        for topic_name, types in topics_sorted:
            type_str = ", ".join(types) if types else "(unknown)"
            lines.append(f"{topic_name} [{type_str}]")
        print(_fmt_list(lines))

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
