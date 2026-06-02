#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray

from tf2_ros import Buffer
from tf2_ros import TransformListener


class DistanceVisualizer(Node):

    def __init__(self):

        super().__init__("distance_visualizer")

        self.pub = self.create_publisher(
            MarkerArray,
            "/apriltag_markers",
            10
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer,
            self
        )

        self.create_timer(
            0.1,
            self.timer_callback
        )

        self.get_logger().info(
            "Distance visualizer started"
        )

    def timer_callback(self):

        try:

            tf = self.tf_buffer.lookup_transform(
                "camera_rgb_optical_frame",
                "apriltag_42",
                rclpy.time.Time()
            )

        except Exception:
            return

        x = tf.transform.translation.x
        y = tf.transform.translation.y
        z = tf.transform.translation.z

        distance = math.sqrt(
            x * x +
            y * y +
            z * z
        )

        markers = MarkerArray()

        text = Marker()

        text.header.frame_id = "apriltag_42"
        text.header.stamp.sec = 0
        text.header.stamp.nanosec = 0

        text.ns = "distance"
        text.id = 0

        text.type = Marker.TEXT_VIEW_FACING
        text.action = Marker.ADD

        # Slightly above the cube
        text.pose.position.z = 0.15

        # Larger text
        text.scale.z = 0.15

        text.color.r = 1.0
        text.color.g = 1.0
        text.color.b = 1.0
        text.color.a = 1.0

        text.text = f"{distance:.2f}m"

        markers.markers.append(text)

        self.pub.publish(markers)


def main(args=None):

    rclpy.init(args=args)

    node = DistanceVisualizer()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()