#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point
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

        #
        # Arrow from camera -> tag
        #
        arrow = Marker()

        arrow.header.frame_id = "camera_rgb_optical_frame"
        arrow.header.stamp.sec = 0
        arrow.header.stamp.nanosec = 0

        arrow.ns = "distance_arrow"
        arrow.id = 0

        arrow.type = Marker.ARROW
        arrow.action = Marker.ADD

        arrow.scale.x = 0.01   # shaft diameter
        arrow.scale.y = 0.03   # head diameter
        arrow.scale.z = 0.05   # head length

        arrow.color.r = 1.0
        arrow.color.g = 0.0
        arrow.color.b = 0.0
        arrow.color.a = 1.0

        p1 = Point()
        p1.x = 0.0
        p1.y = 0.0
        p1.z = 0.0

        p2 = Point()
        p2.x = x
        p2.y = y
        p2.z = z

        arrow.points = [p1, p2]

        markers.markers.append(arrow)

        #
        # Cube at tag location
        #
        cube = Marker()

        cube.header.frame_id = "apriltag_42"
        cube.header.stamp.sec = 0
        cube.header.stamp.nanosec = 0

        cube.ns = "apriltag"
        cube.id = 1

        cube.type = Marker.CUBE
        cube.action = Marker.ADD

        cube.scale.x = 0.10
        cube.scale.y = 0.10
        cube.scale.z = 0.10

        cube.color.r = 0.0
        cube.color.g = 1.0
        cube.color.b = 0.0
        cube.color.a = 0.8

        markers.markers.append(cube)

        #
        # Distance text above cube
        #
        text = Marker()

        text.header.frame_id = "apriltag_42"
        text.header.stamp.sec = 0
        text.header.stamp.nanosec = 0

        text.ns = "distance"
        text.id = 2

        text.type = Marker.TEXT_VIEW_FACING
        text.action = Marker.ADD

        text.pose.position.z = 0.15

        text.scale.z = 0.15

        text.color.r = 1.0
        text.color.g = 1.0
        text.color.b = 1.0
        text.color.a = 1.0

        text.text = f"{distance:.2f} m"

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