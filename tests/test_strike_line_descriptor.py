import pytest
from thermal_events import StrikeLineDescriptor, ThermalEventInstance


@pytest.fixture
def rectangle():
    return [100, 200, 25, 50]


@pytest.fixture
def segmented_points():
    return [[0, 0], [2, 0], [4, 2], [1, 3], [0, 1]]


def test_strike_line_descriptor(rectangle, segmented_points):
    thermal_event_instance = ThermalEventInstance.from_rectangle(
        rectangle, timestamp_ns=100
    )
    strike_line_descriptor = StrikeLineDescriptor(
        thermal_event_instance, segmented_points, 45, 2, flag_RT=True
    )

    assert strike_line_descriptor.instance.bbox_x == rectangle[0]
    assert strike_line_descriptor.instance.bbox_y == rectangle[1]
    assert strike_line_descriptor.instance.bbox_width == rectangle[2]
    assert strike_line_descriptor.instance.bbox_height == rectangle[3]
    assert strike_line_descriptor.instance.timestamp_ns == 100

    assert strike_line_descriptor.segmented_points_as_list == segmented_points
    assert strike_line_descriptor.angle == 45
    assert strike_line_descriptor.curve == 2
    assert strike_line_descriptor.flag_RT


def test_segmented_points_as_list(rectangle, segmented_points):
    thermal_event_instance = ThermalEventInstance.from_rectangle(
        rectangle, timestamp_ns=100
    )
    strike_line_descriptor = StrikeLineDescriptor(
        thermal_event_instance, segmented_points, 45, 2, flag_RT=True
    )

    assert strike_line_descriptor.return_segmented_points() == segmented_points
