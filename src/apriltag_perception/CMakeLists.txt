cmake_minimum_required(VERSION 3.8)
project(apriltag_perception)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/camera_frame_relay
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()