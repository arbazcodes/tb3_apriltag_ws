import math
import random

import rclpy
from rclpy.node import Node

from gz.transport13 import Node as GzNode
from gz.msgs10.pose_pb2 import Pose as GzPose
from gz.msgs10.boolean_pb2 import Boolean as GzBoolean


class AprilTagMover(Node):
    def __init__(self):
        super().__init__("apriltag_mover")

        # Configuration parameters        
        self.declare_parameter("world_name", "simple_world")
        self.declare_parameter("model_name", "apriltag_marker")
        self.declare_parameter("bounds", 3.0)
        self.declare_parameter("speed", 0.35)

        self.world_name = self.get_parameter("world_name").value
        self.model_name = self.get_parameter("model_name").value
        self.bounds = self.get_parameter("bounds").value
        self.speed = self.get_parameter("speed").value

        self.dt = 0.05  # 20 Hz update rate

        # Initial position and first target
        self.x = 2.0
        self.y = 0.0
        self.target_x, self.target_y = self.random_waypoint()

        # Gazebo transport setup
        self.gz = GzNode()
        self.service = f"/world/{self.world_name}/set_pose"

        self.pose = GzPose()
        self.pose.name = self.model_name
        self.pose.orientation.w = 1.0

        self.create_timer(self.dt, self.update)

        self.get_logger().info("AprilTag mover started")

    def random_waypoint(self):
        # Random target position within the allowed area
        return (
            random.uniform(-self.bounds, self.bounds),
            random.uniform(-self.bounds, self.bounds),
        )

    def update(self):
        # Direction from current position to target
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)

        # Pick new target when close to the current
        if dist < 0.1:
            self.target_x, self.target_y = self.random_waypoint()
            return

        # Move toward the target with constant speed
        step = self.speed * self.dt
        self.x += (dx / dist) * step
        self.y += (dy / dist) * step

        # Update model pose in Gazebo
        self.pose.position.x = self.x
        self.pose.position.y = self.y
        self.pose.position.z = 0.0

        self.gz.request(
            self.service,
            self.pose,
            GzPose,
            GzBoolean,
            100,
        )


def main(args=None):
    rclpy.init(args=args)

    node = AprilTagMover()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()