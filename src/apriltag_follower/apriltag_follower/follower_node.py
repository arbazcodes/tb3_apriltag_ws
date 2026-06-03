"""
Proportional controller, pixel-based control instead of TF
------
apriltag_ros publishes one TF frame per tag ID (apriltag_42). 
When two faces of the cube are simultaneously visible the detector reports two detections of ID 42 and overwrites the TF twice per frame. 

This causes jitter that a TF-based follower would chase and produce oscillatory steering.

Working directly with detection pixel data:

  bearing   = atan2(centre_x - cx, fx) -> horizontal angle, rad
  distance  = tag_size_m * fx / tag_pixels -> from apparent tag size, m

When multiple detections exist we pick the one with the largest pixel area (the most front face and stable). This gives us the best bearing estimate.
"""

import math
from enum import Enum, auto

import rclpy
from rclpy.node import Node

from apriltag_msgs.msg import AprilTagDetectionArray
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import CameraInfo


class State(Enum):
    SEARCHING = auto()
    TRACKING = auto()


class FollowerNode(Node):

    def __init__(self):
        super().__init__("apriltag_follower")

        self.declare_parameters(
            namespace="",
            parameters=[
                ("acquire_margin", 60.0),
                ("tag_size", 0.16),
                ("target_distance", 0.8),

                ("k_linear", 0.5),
                ("k_angular", 1.2),

                ("max_linear_speed", 0.20),
                ("max_angular_speed", 1.0),

                ("search_turn_speed", 0.35),
                ("detection_timeout", 1.0),
                ("control_hz", 20.0),

                ("camera_info_topic", "/camera/camera_info"),
                ("detections_topic", "/detections"),
                ("cmd_vel_topic", "/cmd_vel"),
            ],
        )

        # parameters
        self.acquire_margin = self.get_parameter("acquire_margin").value
        self.tag_size = self.get_parameter("tag_size").value
        self.target_distance = self.get_parameter("target_distance").value

        self.k_linear = self.get_parameter("k_linear").value
        self.k_angular = self.get_parameter("k_angular").value

        self.max_linear_speed = self.get_parameter("max_linear_speed").value
        self.max_angular_speed = self.get_parameter("max_angular_speed").value

        self.search_turn_speed = self.get_parameter("search_turn_speed").value
        self.detection_timeout = self.get_parameter("detection_timeout").value
        self.control_hz = self.get_parameter("control_hz").value

        self.camera_topic = self.get_parameter("camera_info_topic").value
        self.detections_topic = self.get_parameter("detections_topic").value
        self.cmd_topic = self.get_parameter("cmd_vel_topic").value

        # camera
        self.fx = None
        self.cx = None

        # state
        self.state = State.SEARCHING
        self.best_detection = None
        self.last_seen = None
        self.last_bearing = 0.0

        # ros
        self.cmd_pub = self.create_publisher(TwistStamped, self.cmd_topic, 10)

        self.create_subscription(CameraInfo,
                                 self.camera_topic,
                                 self.camera_info_callback,
                                 10)

        self.create_subscription(AprilTagDetectionArray,
                                 self.detections_topic,
                                 self.detection_callback,
                                 10)

        self.create_timer(1.0 / self.control_hz, self.control_loop)

        self.get_logger().info("AprilTag follower running")

    #  camera 

    def camera_info_callback(self, msg):
        if self.fx is not None:
            return
        self.fx = msg.k[0]
        self.cx = msg.k[2]

    #  detections 

    def detection_callback(self, msg):

        valid = [
            d for d in msg.detections
            if d.decision_margin >= self.acquire_margin
        ]

        if not valid:
            return

        self.best_detection = max(valid, key=self.pixel_area)
        self.last_seen = self.get_clock().now()

        if self.state == State.SEARCHING:
            self.state = State.TRACKING
            self.get_logger().info("Tag acquired")

    #  control loop 

    def control_loop(self):

        if self.state == State.TRACKING:
            self.check_timeout()

        if self.state == State.SEARCHING:
            self.search()
        else:
            self.track()

    #  search 

    def search(self):
        direction = 1.0 if self.last_bearing >= 0.0 else -1.0
        self.publish_cmd(0.0, direction * self.search_turn_speed)

    #  tracking 

    def track(self):

        if self.fx is None or self.best_detection is None:
            return

        det = self.best_detection

        bearing = math.atan2(det.centre.x - self.cx, self.fx)

        xs = [c.x for c in det.corners]
        ys = [c.y for c in det.corners]

        tag_px = math.sqrt((max(xs) - min(xs)) *
                           (max(ys) - min(ys)))

        distance = self.tag_size * self.fx / max(tag_px, 1.0)

        self.last_bearing = bearing

        v = self.k_linear * (distance - self.target_distance)
        w = -self.k_angular * bearing

        v *= max(0.0, math.cos(bearing))

        v = max(-self.max_linear_speed,
                min(self.max_linear_speed, v))

        w = max(-self.max_angular_speed,
                min(self.max_angular_speed, w))

        self.publish_cmd(v, w)

    #  timeout 

    def check_timeout(self):

        if self.last_seen is None:
            return

        dt = (self.get_clock().now() - self.last_seen).nanoseconds / 1e9

        if dt > self.detection_timeout:
            self.state = State.SEARCHING
            self.best_detection = None
            self.get_logger().info("Tag lost")

    #  utils 

    def pixel_area(self, det):
        xs = [c.x for c in det.corners]
        ys = [c.y for c in det.corners]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    def publish_cmd(self, v, w):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x = v
        msg.twist.angular.z = w
        self.cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = FollowerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_cmd(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()