import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("apriltag_perception"),
        "config",
        "apriltag.yaml",
    )

    relay = Node(
        package="apriltag_perception",
        executable="camera_frame_relay",
        name="camera_frame_relay",
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    apriltag = Node(
        package="apriltag_ros",
        executable="apriltag_node",
        name="apriltag_node",
        parameters=[config, {"use_sim_time": True}],
        remappings=[
            ("image_rect", "/camera/image_raw_optical"),
            ("camera_info", "/camera/camera_info_optical"),
            ("/camera/camera_info",  "/camera/camera_info_optical"),
        ],
        output="screen",
    )

    distance_visualizer = Node(
    package="apriltag_perception",
    executable="distance_visualizer",
    name="distance_visualizer",
    parameters=[{"use_sim_time": True}],
    output="screen",
    )

    rviz_config = os.path.join(
    get_package_share_directory("apriltag_perception"),
    "config",
    "visualize.rviz",
    )
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([relay, apriltag, distance_visualizer, rviz])