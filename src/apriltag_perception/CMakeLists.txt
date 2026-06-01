cmake_minimum_required(VERSION 3.8)
project(apriltag_perception)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install Python module
ament_python_install_package(${PROJECT_NAME})


install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()