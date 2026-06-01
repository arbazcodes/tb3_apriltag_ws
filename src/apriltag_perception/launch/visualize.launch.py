import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('apriltag_perception')

    detection = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg, 'launch', 'detection.launch.py')
        )
    )

    visualizer = Node(
        package='apriltag_perception',
        executable='visualize_detections',
        name='visualize_detections',
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(pkg, 'config', 'apriltag.rviz')],
        output='screen',
    )

    return LaunchDescription([detection, visualizer, rviz])