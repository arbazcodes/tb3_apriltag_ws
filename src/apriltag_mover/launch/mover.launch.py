import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("apriltag_mover"),
        "config", "mover.yaml",
    )
    return LaunchDescription([
        Node(
            package="apriltag_mover",
            executable="mover_node",
            name="apriltag_mover",
            parameters=[config],
            output="screen",
        )
    ])