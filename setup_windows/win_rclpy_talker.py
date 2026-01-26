import os
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Talker(Node):
    def __init__(self):
        super().__init__("win_talker")
        self.pub = self.create_publisher(String, "/win_chatter", 10)


def main() -> None:
    print("ENV ROS_DISCOVERY_SERVER=", os.environ.get("ROS_DISCOVERY_SERVER"))
    print("ENV ROS_AUTOMATIC_DISCOVERY_RANGE=", os.environ.get("ROS_AUTOMATIC_DISCOVERY_RANGE"))
    print("ENV ROS_STATIC_PEERS=", os.environ.get("ROS_STATIC_PEERS"))
    print("ENV ROS_DOMAIN_ID=", os.environ.get("ROS_DOMAIN_ID"))
    print("ENV RMW_IMPLEMENTATION=", os.environ.get("RMW_IMPLEMENTATION"))

    rclpy.init()
    node = Talker()

    msg = String()
    start = time.time()
    i = 0
    while time.time() - start < 300:
        i += 1
        msg.data = f"hello {i}"
        node.pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.1)
        time.sleep(0.4)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
