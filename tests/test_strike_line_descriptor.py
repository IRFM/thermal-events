import random

from tests.test_thermal_event import random_instance
from thermal_events import StrikeLineDescriptor


def random_strike_line_descriptor(return_parameters=False):
    instance = random_instance()

    segmented_points = [
        [random.randint(1, 100), random.randint(1, 100)]
        for _ in range(random.randint(5, 10))
    ]
    angle = random.randrange(90)
    curve = random.randrange(5)
    flag_RT = random.choice([True, False])

    strike_line_descriptor = StrikeLineDescriptor(
        instance, segmented_points, angle, curve, flag_RT=flag_RT
    )
    if return_parameters:
        return strike_line_descriptor, instance, segmented_points, angle, curve, flag_RT
    return strike_line_descriptor


def test_strike_line_descriptor():
    (
        strike_line_descriptor,
        instance,
        segmented_points,
        angle,
        curve,
        flag_RT,
    ) = random_strike_line_descriptor(True)

    assert strike_line_descriptor.instance.bbox_x == instance.bbox_x
    assert strike_line_descriptor.instance.bbox_y == instance.bbox_y
    assert strike_line_descriptor.instance.bbox_width == instance.bbox_width
    assert strike_line_descriptor.instance.bbox_height == instance.bbox_height
    assert strike_line_descriptor.instance.timestamp_ns == instance.timestamp_ns

    assert strike_line_descriptor.segmented_points_as_list == segmented_points
    assert strike_line_descriptor.angle == angle
    assert strike_line_descriptor.curve == curve
    assert strike_line_descriptor.flag_RT == flag_RT


def test_segmented_points_as_list():
    (strike_line_descriptor, _, segmented_points, *_) = random_strike_line_descriptor(
        True
    )

    assert strike_line_descriptor.return_segmented_points() == segmented_points
