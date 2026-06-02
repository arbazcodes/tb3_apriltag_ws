
import math
import random
import pytest


def test_waypoints_always_in_bounds():
    bounds = 3.0
    for _ in range(1000):
        x = random.uniform(-bounds, bounds)
        y = random.uniform(-bounds, bounds)
        assert -bounds <= x <= bounds
        assert -bounds <= y <= bounds


def test_hypotenuse_correct():
    assert math.hypot(3, 4) == pytest.approx(5.0)


def test_arrival_when_close():
    target_x, target_y = 1.0, 1.0
    x, y = 0.95, 0.97
    dist = math.hypot(target_x - x, target_y - y)
    assert dist < 0.1


def test_not_arrived_when_far():
    target_x, target_y = 1.0, 1.0
    x, y = 0.0, 0.0
    dist = math.hypot(target_x - x, target_y - y)
    assert dist > 0.1


def test_direction_vector_correct():
    dx, dy = 3.0, 4.0
    dist = math.hypot(dx, dy)
    dir_x = dx / dist
    dir_y = dy / dist
    assert dir_x == pytest.approx(0.6)
    assert dir_y == pytest.approx(0.8)
