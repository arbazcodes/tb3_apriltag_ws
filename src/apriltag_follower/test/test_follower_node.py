import rclpy
import pytest
from unittest.mock import MagicMock
from apriltag_follower.follower_node import FollowerNode, State


@pytest.fixture(scope="session", autouse=True)
def ros_init():
    rclpy.init()
    yield
    rclpy.shutdown()


def test_detection_starts_tracking():
    node = FollowerNode()

    node.state = State.SEARCHING
    node.min_detection_margin = 60.0

    msg = MagicMock()
    det = MagicMock()
    det.decision_margin = 100.0
    msg.detections = [det]

    node.detection_callback(msg)

    assert node.state == State.TRACKING


def test_tracking_timeout_resets_to_searching():
    node = FollowerNode()

    node.state = State.TRACKING
    node.tracking_timeout = 1.0

    now = node.get_clock().now()

    # simulate old timestamp by subtracting duration 
    old_time = now - rclpy.duration.Duration(seconds=2)

    node.last_seen = old_time

    node.check_tracking_timeout()

    assert node.state == State.SEARCHING


def test_follow_target_publishes_velocity():
    node = FollowerNode()

    node.publish_velocity = MagicMock()

    transform = MagicMock()
    transform.transform.translation.x = 0.0
    transform.transform.translation.y = 0.0
    transform.transform.translation.z = 1.5

    node.tf_buffer.lookup_transform = MagicMock(return_value=transform)

    node.follow_target()

    node.publish_velocity.assert_called_once()

    linear, angular = node.publish_velocity.call_args[0]

    assert linear > 0.0
    assert angular == pytest.approx(0.0, abs=1e-6)