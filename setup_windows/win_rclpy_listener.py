import os
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Listener(Node):
    def __init__(self):
        super().__init__("win_listener")
        self.sub = self.create_subscription(String, "/win_chatter", self._on_msg, 10)
        self._count = 0

    def _on_msg(self, msg: String) -> None:
        self._count += 1
        print(f"[{self._count}] {msg.data}")


def main() -> None:
    print("ENV ROS_DISCOVERY_SERVER=", os.environ.get("ROS_DISCOVERY_SERVER"))
    print("ENV ROS_AUTOMATIC_DISCOVERY_RANGE=", os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE"))
    print("ENV ROS_STATIC_PEERS=", os.environ.get("ROS_STATIC_PEERS"))
    print("ENV ROS_DOMAIN_ID=", os.environ.get("ROS_DOMAIN_ID"))
    print("ENV ROS_LOCALHOST_ONLY=", os.environ.get("ROS_LOCALHOST_ONLY"))
    print("ENV RMW_IMPLEMENTATION=", os.environ.get("RMW_IMPLEMENTATION"))

    rclpy.init()
    node = Listener()

    deadline = time.time() + 30.0
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.2)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
