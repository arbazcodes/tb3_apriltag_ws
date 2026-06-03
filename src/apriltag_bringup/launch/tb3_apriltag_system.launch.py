import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_sim        = get_package_share_directory("apriltag_sim")
    pkg_perception = get_package_share_directory("apriltag_perception")
    pkg_follower   = get_package_share_directory("apriltag_follower")
    pkg_mover      = get_package_share_directory("apriltag_mover")

    use_nvidia_prime = LaunchConfiguration("use_nvidia_prime", default="false")

    declare_nvidia = DeclareLaunchArgument(
        "use_nvidia_prime",
        default_value="false",
        description="Enable NVIDIA prime render offload.",
    )


    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_sim, "launch", "sim.launch.py"),
        ),
        launch_arguments={"use_nvidia_prime": use_nvidia_prime}.items(),
    )

    # Perception: start after robot camera is publishing
    detection = TimerAction(
        period=8.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_perception, "launch", "detection.launch.py"),
                ),
            ),
        ],
    )

    # Follower: start after detection pipeline is running
    follower = TimerAction(
        period=10.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_follower, "launch", "follower.launch.py"),
                ),
            ),
        ],
    )

    # Mover: start after cube is spawned, detection is running, and robot is following
    mover = TimerAction(
        period=12.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_mover, "launch", "mover.launch.py"),
                ),
            ),
        ],
    )


    return LaunchDescription([
        declare_nvidia,
        sim,
        mover,
        detection,
        follower,
    ])