import json
import pathlib

import cv2
import numpy as np
import pytest

from thermal_events import ThermalEventInstance
from thermal_events.thermal_event_instance import (
    bounding_rectangle,
    polygon_is_rectangle,
    polygon_to_string,
    string_to_polygon,
)


@pytest.fixture
def polygon():
    return [[0, 0], [2, 0], [4, 2], [1, 3], [0, 1]]


@pytest.fixture
def polygon_string():
    return "0 0 2 0 4 2 1 3 0 1 "


def test_bounding_rectangle(polygon):
    expected = (0, 0, 5, 4)
    actual = bounding_rectangle(polygon)

    assert actual == expected


@pytest.mark.parametrize(
    "polygon, result",
    [
        ([[0, 0], [1, 1]], None),
        ([[0, 0], [1, 1], [2, 1], [3, 1], [1, 2]], None),
        ([[5, 3], [10, 3], [10, 6], [5, 6]], (5, 3, 6, 4)),
        ([[0, 0], [2, 0], [4, 2], [1, 3], [0, 1]], None),
    ],
)
def test_polygon_is_rectangle(polygon, result):
    assert polygon_is_rectangle(polygon) == result


def test_polygon_to_string(polygon, polygon_string):
    expected = polygon_string
    actual = polygon_to_string(polygon)
    assert actual == expected


def test_string_to_polygon(polygon, polygon_string):
    expected = polygon
    actual = string_to_polygon(polygon_string)

    assert actual == expected

    assert string_to_polygon(None) == []


def test_thermal_event_instance(polygon):
    timestamp = 1000
    for poly in [polygon, polygon_to_string(polygon)]:
        instance = ThermalEventInstance(timestamp, polygon=poly)

        assert instance.timestamp_ns == timestamp

        assert instance.bbox_x == 0
        assert instance.bbox_y == 0
        assert instance.bbox_width == 5
        assert instance.bbox_height == 4
        if not isinstance(poly, str):
            poly = polygon_to_string(poly)
        assert instance.polygon == poly


def test_from_mask():
    path = pathlib.Path(__file__).parent / "long_polygon.json"
    with open(path, "r") as file:
        polygon = json.load(file)

    # Offset the polygon
    polygon = [[200 + x[0], 100 + x[1]] for x in polygon]

    timestamp = 1000
    mask = np.zeros((512, 640))
    cv2.fillPoly(mask, pts=np.array([polygon]), color=1)

    instance = ThermalEventInstance.from_mask(
        mask, mask_value=1, timestamp_ns=timestamp
    )

    assert instance.timestamp_ns == timestamp

    assert instance.bbox_x == min([x[0] for x in polygon])
    assert instance.bbox_y == min([x[1] for x in polygon])
    # Because of the way the polygon extraction from a mask works, the width
    # and height of the bounding box do not follow the convention of being
    # offset by 1. The consequence is that we lose one pixel on the width and height
    assert instance.bbox_width == max([x[0] for x in polygon]) - instance.bbox_x
    assert instance.bbox_height == max([x[1] for x in polygon]) - instance.bbox_y


def test_from_polygon(polygon):
    timestamp = 1000
    instance = ThermalEventInstance.from_polygon(polygon, timestamp_ns=timestamp)

    assert instance.timestamp_ns == timestamp

    assert instance.bbox_x == 0
    assert instance.bbox_y == 0
    assert instance.bbox_width == 5
    assert instance.bbox_height == 4

    assert instance.polygon == polygon_to_string(polygon)


def test_polygon_simplification():
    path = pathlib.Path(__file__).parent / "long_polygon.json"
    with open(path, "r") as file:
        polygon = json.load(file)

    max_polygon_string_length = 256

    instance = ThermalEventInstance.from_polygon(
        polygon, timestamp_ns=100, max_polygon_string_length=max_polygon_string_length
    )

    assert len(instance.polygon) <= max_polygon_string_length

    sim_poly = instance.polygon_as_list

    hull = cv2.convexHull(np.array(sim_poly + polygon))

    similarity = min(
        cv2.contourArea(np.array(polygon)), cv2.contourArea(np.array(sim_poly))
    ) / cv2.contourArea(hull)

    assert similarity > 0.99


def test_from_rectangle():
    rectangle = [5, 3, 10, 2]
    timestamp = 1000
    instance = ThermalEventInstance.from_rectangle(rectangle, timestamp_ns=timestamp)

    assert instance.timestamp_ns == timestamp

    assert instance.bbox_x == rectangle[0]
    assert instance.bbox_y == rectangle[1]
    assert instance.bbox_width == rectangle[2]
    assert instance.bbox_height == rectangle[3]

    assert instance.polygon == "5 3 14 3 14 4 5 4 "


def test_set_image(polygon):
    image = np.abs(100 + 50 * np.random.randn(512, 640))
    image = image.astype(np.uint16)

    timestamp = 1000
    instance = ThermalEventInstance.from_polygon(polygon, timestamp_ns=timestamp)

    instance.set_image(image)

    mask = np.zeros_like(image)
    cv2.fillPoly(mask, pts=np.array([polygon]), color=1)
    coords = np.where(mask)
    ir_polygon = image[coords]

    assert instance.max_temperature_C == np.max(ir_polygon)
    assert instance.min_temperature_C == np.min(ir_polygon)
    assert instance.average_temperature_C == np.mean(ir_polygon)

    pos_max = np.argmax(ir_polygon)
    assert instance.max_T_image_position_x == coords[1][pos_max]
    assert instance.max_T_image_position_y == coords[0][pos_max]

    pos_min = np.argmin(ir_polygon)
    assert instance.min_T_image_position_x == coords[1][pos_min]
    assert instance.min_T_image_position_y == coords[0][pos_min]

    assert instance.centroid_image_position_x == np.mean(coords[1])
    assert instance.centroid_image_position_y == np.mean(coords[0])

    assert instance.pixel_area == np.sum(mask)


def test_return_polygon(polygon):
    instance = ThermalEventInstance.from_polygon(polygon, timestamp_ns=1000)
    assert instance.return_polygon() == polygon

    rect_polygon = [[5, 3], [10, 3], [10, 6], [5, 6]]
    instance = ThermalEventInstance.from_polygon(rect_polygon, timestamp_ns=1000)
    instance.polygon = ""
    assert instance.return_polygon() == rect_polygon


def test_polygon_as_list(polygon):
    instance = ThermalEventInstance.from_polygon(polygon, timestamp_ns=1000)

    assert instance.return_polygon() == polygon
