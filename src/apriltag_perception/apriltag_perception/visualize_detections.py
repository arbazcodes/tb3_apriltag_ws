#!/usr/bin/env python3
"""
pose_visualizer.py
==================
Subscribes to /detections (AprilTagDetectionArray) and for every detected tag:
  • publishes an orange sphere + distance label to /apriltag_markers
  • broadcasts a TF frame so RViz shows the tag's full pose as axes
"""
import math

import rclpy
from rclpy.node import Node
from apriltag_msgs.msg import AprilTagDetectionArray
from geometry_msgs.msg import TransformStamped
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import TransformBroadcaster

_ORANGE = (1.0, 0.5, 0.0)
_WHITE  = (1.0, 1.0, 1.0)

def euclidean(pos) -> float:
    return math.sqrt(pos.x**2 + pos.y**2 + pos.z**2) # Euclidean distance from camera origin to a geometry_msgs point


def make_sphere(header, tag_id: int, pose) -> Marker:
    m = Marker()
    m.header   = header
    m.ns, m.id = 'tag_sphere', tag_id
    m.type     = Marker.SPHERE
    m.action   = Marker.ADD
    m.pose     = pose
    m.scale.x  = m.scale.y = m.scale.z = 0.05
    m.color.r, m.color.g, m.color.b, m.color.a = *_ORANGE, 1.0
    return m


def make_label(header, tag_id: int, pose, dist: float) -> Marker:
    m = Marker()
    m.header   = header
    m.ns, m.id = 'tag_text', tag_id
    m.type     = Marker.TEXT_VIEW_FACING
    m.action   = Marker.ADD
    m.pose.position.x  = pose.position.x
    m.pose.position.y  = pose.position.y
    m.pose.position.z  = pose.position.z + 0.12   # float above sphere
    m.pose.orientation = pose.orientation
    m.scale.z  = 0.06
    m.color.r, m.color.g, m.color.b, m.color.a = *_WHITE, 1.0
    m.text = f'ID {tag_id}  {dist:.2f} m'
    return m


def make_tf(header, child_frame: str, pose) -> TransformStamped:
    tf = TransformStamped()
    tf.header         = header
    tf.child_frame_id = child_frame
    tf.transform.translation.x = pose.position.x
    tf.transform.translation.y = pose.position.y
    tf.transform.translation.z = pose.position.z
    tf.transform.rotation      = pose.orientation
    return tf



class PoseVisualizer(Node):

    def __init__(self):
        super().__init__('pose_visualizer')
        self.create_subscription(
            AprilTagDetectionArray, '/detections', self._on_detections, 10)
        self._pub   = self.create_publisher(MarkerArray, '/apriltag_markers', 10)
        self._tf_br = TransformBroadcaster(self)
        self.get_logger().info('pose_visualizer ready — listening on /detections')

    def _on_detections(self, msg: AprilTagDetectionArray) -> None:
        array = MarkerArray()

        # clear every stale marker from the previous frame
        wipe = Marker()
        wipe.action = Marker.DELETEALL
        array.markers.append(wipe)

        for det in msg.detections:
            pose = det.pose.pose.pose
            dist = euclidean(pose.position)

            array.markers.append(make_sphere(msg.header, det.id, pose))
            array.markers.append(make_label(msg.header, det.id, pose, dist))
            self._tf_br.sendTransform(
                make_tf(msg.header, f'apriltag_{det.id}', pose))

        if msg.detections:
            self._pub.publish(array)
            summary = ', '.join(
                f'ID {d.id} @ {euclidean(d.pose.pose.pose.position):.2f} m'
                for d in msg.detections
            )
            self.get_logger().info(f'{len(msg.detections)} tag(s): {summary}')


def main(args=None):
    rclpy.init(args=args)
    node = PoseVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()