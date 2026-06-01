cmake_minimum_required(VERSION 3.8)
project(apriltag_perception)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install Python module
ament_python_install_package(${PROJECT_NAME})

# Install entry-point script
install(PROGRAMS scripts/detection_viz_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()