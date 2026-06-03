import math
from enum import Enum

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener

from apriltag_msgs.msg import AprilTagDetectionArray
from geometry_msgs.msg import TwistStamped


class State(Enum):
    SEARCHING = 0
    TRACKING = 1


class FollowerNode(Node):

    CAMERA_FRAME = "camera_rgb_optical_frame"
    TAG_FRAME = "apriltag_42"

    def __init__(self):
        super().__init__("apriltag_follower")

        self.declare_parameters(
            namespace="",
            parameters=[
                ("min_detection_margin", 60.0),
                ("desired_distance_m", 0.8),
                ("linear_gain", 1.0),
                ("angular_gain", 1.2),
                ("max_linear_speed", 0.22),
                ("max_angular_speed", 1.0),
                ("search_turn_speed", 0.35),
                ("tracking_timeout", 1.0),
                ("control_rate_hz", 20.0),
                ("detections_topic", "/detections"),
                ("cmd_vel_topic", "/cmd_vel"),
            ],
        )

        self.min_detection_margin = self.get_parameter("min_detection_margin").value
        self.desired_distance = self.get_parameter("desired_distance_m").value
        self.linear_gain = self.get_parameter("linear_gain").value
        self.angular_gain = self.get_parameter("angular_gain").value
        self.max_linear_speed = self.get_parameter("max_linear_speed").value
        self.max_angular_speed = self.get_parameter("max_angular_speed").value
        self.search_turn_speed = self.get_parameter("search_turn_speed").value
        self.tracking_timeout = self.get_parameter("tracking_timeout").value
        self.control_rate = self.get_parameter("control_rate_hz").value
        self.detections_topic = self.get_parameter("detections_topic").value
        self.cmd_topic = self.get_parameter("cmd_vel_topic").value

        self.state = State.SEARCHING
        self.last_seen = None
        self.last_bearing = 0.0

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.cmd_pub = self.create_publisher(TwistStamped, self.cmd_topic, 10)

        self.create_subscription(AprilTagDetectionArray, self.detections_topic, self.detection_callback, 10)

        self.create_timer(1.0 / self.control_rate, self.control_loop)

        self.get_logger().info("AprilTag follower started")

    def detection_callback(self, msg):

        # Check if any detection is confident enough
        valid = False

        for det in msg.detections:
            if det.decision_margin >= self.min_detection_margin:
                valid = True
                break

        if not valid:
            return

        # Remember when the tag was last seen
        self.last_seen = self.get_clock().now()

        if self.state == State.SEARCHING:
            self.state = State.TRACKING
            self.get_logger().info("Tag acquired")

    def control_loop(self):

        if self.state == State.TRACKING:
            self.check_tracking_timeout()

        if self.state == State.SEARCHING:
            self.rotate_to_search()
            return

        self.follow_target()


    def rotate_to_search(self):

        # Turn toward the side where the tag was last seen
        turn_speed = self.search_turn_speed

        if self.last_bearing < 0:
            turn_speed *= -1

        self.publish_velocity(0.0, turn_speed)


    def follow_target(self):

        try:
            # Get tag position relative to the camera
            transform = self.tf_buffer.lookup_transform(
                self.CAMERA_FRAME,
                self.TAG_FRAME,
                rclpy.time.Time(),
            )
        except Exception:
            self.publish_velocity(0.0, 0.0)
            return

        t = transform.transform.translation

        # Horizontal angle from camera centre
        bearing = math.atan2(t.x, t.z)

        # Distance from camera to tag
        distance = math.hypot(t.x, t.y, t.z)

        self.last_bearing = bearing

        # Move toward the desired distance
        linear = self.linear_gain * (distance - self.desired_distance)

        # Turn to keep the tag centred
        angular = -self.angular_gain * bearing

        # Slow down if we're not facing the tag yet
        linear *= max(0.0, math.cos(bearing))

        linear = max(-self.max_linear_speed, min(self.max_linear_speed, linear))

        angular = max(-self.max_angular_speed, min(self.max_angular_speed, angular))

        self.publish_velocity(linear, angular)

    def check_tracking_timeout(self):

        if self.last_seen is None:
            return

        elapsed = (self.get_clock().now() - self.last_seen).nanoseconds / 1e9

        # Go back to searching If we haven't seen the tag for a while
        if elapsed > self.tracking_timeout:
            self.state = State.SEARCHING
            self.get_logger().info(
                "Lost tag, searching again"    )

    def publish_velocity(self, linear_x, angular_z):

        msg = TwistStamped()

        msg.header.stamp = (self.get_clock().now().to_msg())
        msg.header.frame_id = "base_link"

        msg.twist.linear.x = linear_x
        msg.twist.angular.z = angular_z

        self.cmd_pub.publish(msg)



def main(args=None):

    rclpy.init(args=args)

    node = FollowerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_velocity(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()