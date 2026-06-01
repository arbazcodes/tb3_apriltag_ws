import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("apriltag_perception"),
        "config", "apriltag.yaml",
    )
    return LaunchDescription([
        Node(
            package="apriltag_ros",
            executable="apriltag_node",
            name="apriltag_node",
            parameters=[config],
            
            remappings=[
                ("image_rect",  "/camera/image_raw"),
                ("camera_info", "/camera/camera_info"),
            ],
            output="screen",
        )
    ])