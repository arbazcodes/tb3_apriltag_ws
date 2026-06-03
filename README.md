# AprilTag Detection and Following
**ROS2 Jazzy · Gazebo Harmonic · TurtleBot3 Waffle**

A TurtleBot3 Waffle detects and follows an AprilTag marker moving randomly through a simulated environment. The system runs entirely in Gazebo Harmonic with real-time detection via `apriltag_ros`, TF-based pose estimation, and a proportional follow controller.


---

## 1. Overview

Four ROS2 packages:


`apriltag_sim`: Gazebo Harmonic world, TurtleBot3 spawn, AprilTag marker model \
`apriltag_perception`: Camera frame relay, `apriltag_ros` detection, distance visualizer, RViz \
`apriltag_mover`: Moves the AprilTag marker through random waypoints using Gazebo transport \
`apriltag_follower`: Pose-based proportional controller to control the TurtleBot3 \
`apriltag_bringup`: Single launch file that starts the complete system

The system starts with the Gazebo camera, whose image stream is forwarded by the `camera_frame_relay` node to the `apriltag_node`. The AprilTag detector processes the incoming images and publishes tag detections on the `/detections` topic while also broadcasting the corresponding TF frame (`apriltag_42`).

The `follower_node` subscribes to both the detection data and the tag's TF frame to estimate the relative position of the target. Based on this information, it generates velocity commands on the `/cmd_vel` topic, which are executed by the TurtleBot3.

The `distance_visualizer` uses the `apriltag_42` TF frame to compute and display the robot–tag distance in RViz.

The `mover_node` continuously updates the AprilTag marker's position in Gazebo through the Gazebo Transport `set_pose` service.


---

## 2. Dependencies

### ROS2 and Gazebo

- **ROS2 Jazzy** - [installation guide](https://docs.ros.org/en/jazzy/Installation.html)
- **Gazebo Harmonic** - [installation guide](https://gazebosim.org/docs/harmonic/install)
- **ros_gz** bridge packages for Jazzy/Harmonic

### Required ROS2 Packages

Install via `apt`:

```bash
sudo apt install -y \
  ros-jazzy-turtlebot3 \
  ros-jazzy-turtlebot3-gazebo \
  ros-jazzy-turtlebot3-description \
  ros-jazzy-apriltag-ros \
  ros-jazzy-apriltag-msgs \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-image \
  ros-jazzy-tf2-ros \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-rviz2
```

### Environment Variables

The TurtleBot3 packages require the robot model to be set:

```bash
echo "export TURTLEBOT3_MODEL=waffle" >> ~/.bashrc
source ~/.bashrc
```

---

## 3. Building

```bash
# Navigate to your workspace
cd ~/ros2_ws

# Copy or clone the repository into src/
# (packages should be under ~/ros2_ws/src/)

# Build all packages
colcon build --symlink-install

# Source the workspace
source install/setup.bash
```

---

## 4. Running the System

### Option A - Single command

```bash
ros2 launch apriltag_bringup tb3_apriltag_system.launch.py
```

### Option B - Step by step (four terminals)

```bash
# Terminal 1 - Simulation
ros2 launch apriltag_sim sim.launch.py

# Terminal 2 - Detection pipeline + RViz (wait for Gazebo to load)
ros2 launch apriltag_perception detection.launch.py

# Terminal 3 - Follower
ros2 launch apriltag_follower follower.launch.py

# Terminal 4 - Mover
ros2 launch apriltag_mover mover.launch.py
```

### NVIDIA GPU (Optimus / prime-select)

If your system requires NVIDIA prime render offload for Gazebo rendering:

```bash
ros2 launch apriltag_bringup tb3_apriltag_system.launch.py use_nvidia_prime:=true
```

This sets `__NV_PRIME_RENDER_OFFLOAD=1` and related environment variables only when explicitly requested. The default is `false` so non-NVIDIA systems are unaffected.

---

## 5. Key Configurations

**Follower controller (`follower.yaml`)**

* `desired_distance_m = 1.0` m: target distance maintained between the robot and the marker.
* `min_detection_margin = 60.0`: minimum detection confidence required before the robot begins tracking.
* `tracking_timeout = 1.0` s: time allowed without a valid detection before returning to SEARCHING mode.
* `max_linear_speed = 0.22` m/s and `max_angular_speed = 1.0` rad/s: limits on the robot's motion commands.

**Marker mover (`mover.yaml`)**

* `bounds = 5.0` m: defines the square area in which the marker moves.
* `speed = 0.15` m/s: marker movement speed.

**AprilTag detection (`apriltag.yaml`)**

* `family = 36h11`: matches the tag family used on the marker.
* `size = 0.16` m: physical tag size used for pose estimation.
* `max_hamming = 0`: disables error correction to reduce false detections.
* `tag.ids = [42]`: only detections of tag ID 42 are processed.

---

## 6. Running Tests

```bash
# Run all tests
colcon test --packages-select apriltag_follower apriltag_mover

# View results
colcon test-result --verbose
```

---

## 7. Design Choices

### Camera frame relay

Gazebo publishes camera images with `frame_id = camera_rgb_frame`, the robot body convention (x-forward, y-left, z-up). `apriltag_ros` expects optical convention (x-right, y-down, z-forward) and uses the frame_id from `CameraInfo` to express poses.

The detected tag appears above the robot in RViz. This relay republishes Image and CameraInfo messages with: frame_id = camera_rgb_optical_frame. Only the frame label is changed so that apriltag_ros uses the correct camera coordinate convention

---

### Mover: Gazebo transport

The marker is repositioned every 50ms using `gz.transport` `set_pose` directly rather than through `ros_gz_bridge`.

---

### Visualization

`distance_visualizer` publishes three markers: a red arrow from the camera origin to the tag (bearing and distance), a green cube at the tag position, and a live distance in metres. All three come from the same TF lookup the follower uses so the display reflects what the controller sees.

---

### Proportional controller

```
v  =  k_linear  × (distance − desired)
w  = −k_angular × bearing
v  ×= max(0.0, cos(bearing))
```

The `cos(bearing)` term scales forward speed by how aligned the robot is: full speed at 0 degrees, zero at 90 degree. With this, the robot aligns first, then approaches.

A PI, or PID was not used as P suffices for tracking a moving target at these speeds, and in this scope. PI/PID control could be inclueded in the future, where the integral may reduce steady-state error and the derivative may improve responsiveness and reduce overshoot for faster-moving targets or dynamic trajectories.


---

### Pose-based control with split responsibility

The detection callback has checks if any detection clears the confidence threshold (`decision_margin ≥ 60.0`) and update the tracking state.

`follow_target()` looks up `camera_rgb_optical_frame → apriltag_42` from TF and compute control directly from the translation vector:

```
bearing  = atan2(t.x, t.z)              # t.x right, t.z forward → horizontal angle
distance = sqrt(t.x² + t.y² + t.z²)    # 3D Euclidean distance
```

The quality gate and the pose source are kept separate. A high-confidence detection triggers tracking. The actual pose used for control comes from PnP-estimated TF. If the TF lookup fails, the controller publishes zero velocity rather than coasting.

### State machine

SEARCHING rotates toward the direction the tag was last seen `last_bearing`. TRACKING times out after 1 second without a valid detection above the margin threshold, then returns to SEARCHING.

---

### Alternate control:
Bypassed TF and computed bearing and distance directly from pixel data:

```
bearing  = atan2(centre_x − cx, fx)
distance = tag_size_m × fx / sqrt(bbox_w × bbox_h)
```

When multiple detections existed, it selected the one with the largest bounding-box pixel area, the most frontally-facing side. It worked well. With the current marker, multi-detection are very rare and TF-based pose gives a proper metric 3D position usable for downstream tasks, and doesn't require knowing the tag's physical size inside the controller.
