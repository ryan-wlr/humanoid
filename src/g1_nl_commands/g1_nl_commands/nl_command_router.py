from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .skills import parse_command


class NLCommandRouter(Node):
    def __init__(self) -> None:
        super().__init__("nl_command_router")

        self.declare_parameter("input_topic", "/nl_command")
        self.declare_parameter("output_topic", "/g1/task_plan")

        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter("output_topic").get_parameter_value().string_value

        self._pub = self.create_publisher(String, output_topic, 10)
        self._sub = self.create_subscription(String, input_topic, self._on_command, 10)

        self.get_logger().info(f"Listening: {input_topic}")
        self.get_logger().info(f"Publishing: {output_topic}")

    def _on_command(self, msg: String) -> None:
        text = msg.data
        plan = parse_command(text)
        if plan is None:
            return

        out = String()
        out.data = json.dumps(plan.to_dict())
        self._pub.publish(out)

        self.get_logger().info(f"cmd={text!r} -> {out.data}")


def main() -> None:
    rclpy.init()
    node = NLCommandRouter()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        # rclpy installs signal handlers which may call shutdown() on SIGINT.
        # Tolerate double-shutdown when ros2 run sends Ctrl-C / SIGINT.
        try:
            rclpy.shutdown()
        except Exception:
            pass
