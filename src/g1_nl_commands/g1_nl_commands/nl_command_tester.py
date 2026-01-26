from __future__ import annotations

import sys

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class NLCommandTester(Node):
    def __init__(self) -> None:
        super().__init__("nl_command_tester")
        self.declare_parameter("topic", "/nl_command")
        topic = self.get_parameter("topic").get_parameter_value().string_value
        self._pub = self.create_publisher(String, topic, 10)
        self.get_logger().info(f"Publishing commands to: {topic}")

    def send(self, text: str) -> None:
        msg = String()
        msg.data = text
        self._pub.publish(msg)
        self.get_logger().info(f"sent: {text!r}")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: ros2 run g1_nl_commands nl_command_tester 'pick up apple'")

    rclpy.init()
    node = NLCommandTester()
    try:
        node.send(" ".join(sys.argv[1:]))
        rclpy.spin_once(node, timeout_sec=0.2)
    finally:
        node.destroy_node()
        rclpy.shutdown()
