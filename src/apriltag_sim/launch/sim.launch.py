import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_sim    = get_package_share_directory("apriltag_sim")
    pkg_tb3_gz = get_package_share_directory("turtlebot3_gazebo")
    pkg_ros_gz = get_package_share_directory("ros_gz_sim")

    use_sim_time     = LaunchConfiguration("use_sim_time",     default="true")
    use_nvidia_prime = LaunchConfiguration("use_nvidia_prime", default="false")
    world_file       = os.path.join(pkg_sim, "worlds", "simple_world.sdf")

    declare_nvidia = DeclareLaunchArgument(
        "use_nvidia_prime",
        default_value="false",
        description=(
            "Enable NVIDIA prime render offload. "
            "Set true on laptops with a discrete NVIDIA GPU (Optimus/prime-select)."
        ),
    )

    nvidia_env = GroupAction(
        condition=IfCondition(use_nvidia_prime),
        actions=[
            SetEnvironmentVariable("__NV_PRIME_RENDER_OFFLOAD",      "1"),
            SetEnvironmentVariable("__GLX_VENDOR_LIBRARY_NAME",       "nvidia"),
            SetEnvironmentVariable(
                "__EGL_VENDOR_LIBRARY_FILENAMES",
                "/usr/share/glvnd/egl_vendor.d/10_nvidia.json",
            ),
        ],
    )

    resource_paths = [
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            os.path.join(pkg_tb3_gz, "models"),
        ),
        AppendEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH",
            os.path.join(pkg_sim, "models"),
        ),
    ]

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz, "launch", "gz_sim.launch.py"),
        ),
        launch_arguments={
            "gz_args":        ["-r -s -v2 ", world_file],
            "on_exit_shutdown": "true",
        }.items(),
    )

    gz_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz, "launch", "gz_sim.launch.py"),
        ),
        launch_arguments={"gz_args": "-g -v2"}.items(),
    )

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_tb3_gz, "launch", "robot_state_publisher.launch.py"),
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    spawn_robot = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_tb3_gz, "launch", "spawn_turtlebot3.launch.py"),
                ),
                launch_arguments={"x_pose": "0.0", "y_pose": "0.0"}.items(),
            ),
        ],
    )

    spawn_cube = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_ros_gz, "launch", "gz_spawn_model.launch.py"),
                ),
                launch_arguments={
                    "file": os.path.join(
                        pkg_sim, "models", "apriltag_marker", "cube_model.sdf"
                    ),
                    "name": "apriltag_marker",
                    "x":    "1.0",
                    "y":    "0.0",
                    "z":    "0.0",
                }.items(),
            ),
        ],
    )

    return LaunchDescription([
        declare_nvidia,
        nvidia_env,
        *resource_paths,
        gz_server,
        gz_client,
        robot_state_publisher,
        spawn_robot,
        spawn_cube,
    ])