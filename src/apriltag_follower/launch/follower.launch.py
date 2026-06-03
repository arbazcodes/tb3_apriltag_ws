import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("apriltag_follower"),
        "config",
        "follower.yaml",
    )

    follower = Node(
        package="apriltag_follower",
        executable="follower_node",
        name="apriltag_follower",
        parameters=[config],
        output="screen",
    )

    return LaunchDescription([follower])