from threading import Lock
from typing import Union

import cv2
import numpy as np
from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import relationship

from .base import Base
from .polysimplify import VWSimplifier

BigIntegerType = BigInteger().with_variant(sqlite.INTEGER(), "sqlite")


def bounding_rectangle(polygon: list) -> tuple:
    """
    Returns the polygon bounding rectangle as (left,top,width,height)
    """

    xmin = polygon[0][0]
    xmax = xmin
    ymin = polygon[0][1]
    ymax = ymin
    for p in polygon:
        xmin = min(xmin, p[0])
        xmax = max(xmax, p[0])
        ymin = min(ymin, p[1])
        ymax = max(ymax, p[1])
    return xmin, ymin, xmax - xmin + 1, ymax - ymin + 1


def polygon_is_rectangle(polygon: list) -> Union[tuple, None]:
    """
    Returns the rectangle (left,top,width,height) if given polygon is
    rectangular, None otherwise.
    """
    if len(polygon) < 4 or len(polygon) > 5:
        return None
    x = list()
    y = list()
    for p in polygon:
        if p[0] not in x:
            x.append(p[0])
        if p[1] not in y:
            y.append(p[1])
    if len(x) == 2 and len(y) == 2:
        left = min(x)
        top = min(y)
        width = max(x) - left + 1
        height = max(y) - top + 1
        return left, top, width, height
    return None


def polygon_to_string(polygon: Union[list, np.ndarray]) -> str:
    """Convert a polygon in a list in string format (x1 y1 ... xn yn).

    Args:
        polygon (list): The polygon as a list.

    Returns:
        str: The polygon in string format.
    """
    if isinstance(polygon, np.ndarray):
        polygon = polygon.tolist()

    res = str()
    for p in polygon:
        res += f"{p[0]} {p[1]} "
    return res


def string_to_polygon(string: str) -> list:
    """Convert a polygon in string format (x1 y1 ... xn yn) to a list.

    Args:
        string (str): The polygon in string format

    Returns:
        list: The polygon as a list
    """
    if string is None:
        return []

    flat = [int(x) for x in string.split(" ") if x != ""]
    return [flat[i : i + 2] for i in range(0, len(flat), 2)]


class ThermalEventInstance(Base):
    __tablename__ = "thermal_events_instances"

    id = Column(
        BigIntegerType, primary_key=True, autoincrement=True, index=True, unique=True
    )
    thermal_evend_id = Column(
        BigIntegerType,
        ForeignKey("thermal_events.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        comment="id of the thermal event to which the instance belongs",
    )

    timestamp_ns = Column(
        BigIntegerType,
        nullable=False,
        comment="Timestamp of the instance, in nanosecond",
    )

    bbox_x = Column(
        Integer,
        nullable=False,
        comment="x coordinate of the upper left corner of the bounding box, in pixel",
    )
    bbox_y = Column(
        Integer,
        nullable=False,
        comment="y coordinate of the upper left corner of the bounding box, in pixel",
    )
    bbox_width = Column(
        Integer,
        nullable=False,
        comment="Width of the bounding box, in pixel",
    )
    bbox_height = Column(
        Integer,
        nullable=False,
        comment="Height of the bounding box, in pixel",
    )
    polygon = Column(
        String(256),
        comment="Polygon x0, y0, ..., xn, yn encompassing the instance, with the "
        + "coordinates in pixel",
    )

    pfc_id = Column(
        BigIntegerType,
        comment="The id of the plasma facing component on which the instance appears",
    )

    max_temperature_C = Column(
        Integer,
        comment="Maximum temperature of the instance, in degree celsius",
    )
    min_temperature_C = Column(
        Integer,
        comment="Minimum temperature of the instance, in degree celsius",
    )
    average_temperature_C = Column(
        Float,
        comment="Average temperature of the instance, in degree celsius",
    )

    overheating_factor = Column(
        Float,
        comment="The overheating factor, defined as the maximum temperature in "
        + "the instance divided by the maximum temperature allowed on the component",
    )

    max_T_world_position_x_m = Column(
        Float,
        comment="x coordinate of the maximum temperature in 3D space, in meter",
    )
    max_T_world_position_y_m = Column(
        Float,
        comment="y coordinate of the maximum temperature in 3D space, in meter",
    )
    max_T_world_position_z_m = Column(
        Float,
        comment="z coordinate of the maximum temperature in 3D space, in meter",
    )

    max_T_image_position_x = Column(
        Integer,
        comment="x coordinate of the maximum temperature in the image, in pixel",
    )
    max_T_image_position_y = Column(
        Integer,
        comment="y coordinate of the maximum temperature in the image, in pixel",
    )

    min_T_world_position_x_m = Column(
        Float,
        comment="x coordinate of the minimum temperature in 3D space, in meter",
    )
    min_T_world_position_y_m = Column(
        Float,
        comment="y coordinate of the minimum temperature in 3D space, in meter",
    )
    min_T_world_position_z_m = Column(
        Float,
        comment="z coordinate of the minimum temperature in 3D space, in meter",
    )

    min_T_image_position_x = Column(
        Integer,
        comment="x coordinate of the minimum temperature in the image, in pixel",
    )
    min_T_image_position_y = Column(
        Integer,
        comment="y coordinate of the minimum temperature in the image, in pixel",
    )

    max_overheating_world_position_x_m = Column(
        Float,
        comment="x coordinate of the maximum overheating factor in 3D space, in meter",
    )
    max_overheating_world_position_y_m = Column(
        Float,
        comment="y coordinate of the maximum overheating factor in 3D space, in meter",
    )
    max_overheating_world_position_z_m = Column(
        Float,
        comment="z coordinate of the maximum overheating factor in 3D space, in meter",
    )

    max_overheating_image_position_x = Column(
        Integer,
        comment="x coordinate of the maximum overheating factor in the image, in pixel",
    )
    max_overheating_image_position_y = Column(
        Integer,
        comment="y coordinate of the maximum overheating factor in the image, in pixel",
    )

    centroid_world_position_x_m = Column(
        Float,
        comment="x coordinate of the centroid of the instance, in 3D space, in meter",
    )
    centroid_world_position_y_m = Column(
        Float,
        comment="y coordinate of the centroid of the instance, in 3D space, in meter",
    )
    centroid_world_position_z_m = Column(
        Float,
        comment="z coordinate of the centroid of the instance, in 3D space, in meter",
    )

    centroid_image_position_x = Column(
        Float,
        comment="x coordinate of the centroid of the instance, in 3D space, in meter",
    )
    centroid_image_position_y = Column(
        Float,
        comment="y coordinate of the centroid of the instance, in 3D space, in meter",
    )

    pixel_area = Column(
        Integer, comment="The area of the instance in the image space, in pixel"
    )
    physical_area = Column(
        Float, comment="The area of the instance in 3D space, in square meter"
    )

    thermal_event = relationship(
        "ThermalEvent", back_populates="instances", uselist=False
    )

    _buffer = None  # image bugger used to draw polygons
    _mutex = Lock()

    def __init__(
        self,
        timestamp_ns: int,
        **kwargs,
    ) -> None:
        """
        Initialize a ThermalEventInstance.

        Args:
            timestamp_ns (int): The timestamp, in nanosecond.
            **kwargs: Additional keyword arguments for the ThermalEventInstance.
        """
        self.timestamp_ns = int(timestamp_ns)
        self._confidence = None

        for key, value in kwargs.items():
            if key == "polygon" and value != "":
                if not isinstance(value, str):
                    rect = bounding_rectangle(value)
                    value = polygon_to_string(value)
                else:
                    rect = bounding_rectangle(string_to_polygon(value))

                self.bbox_x = int(rect[0])
                self.bbox_y = int(rect[1])
                self.bbox_width = int(rect[2])
                self.bbox_height = int(rect[3])

            if key != "thermal_event":
                setattr(self, key, value)

    @classmethod
    def from_mask(
        cls,
        mask: np.ndarray,
        mask_value: int,
        timestamp_ns: int,
        ir_image: np.ndarray = None,
        max_polygon_string_length: int = 256,
    ) -> "ThermalEventInstance":
        """
        Create a ThermalEventInstance from a binary mask.

        Args:
            mask (np.ndarray): The binary mask.
            mask_value (int): The value in the mask that corresponds to the instance.
            timestamp_ns (int): The timestamp of the instance, in nanosecond.
            ir_image (np.ndarray, optional): The infrared image. Defaults to None.
            max_polygon_string_length (int, optional): The maximum number of
                characters used to encode the polygon in the form "x0 y0 x1 y1 ...".
                Defaults to 256.

        Returns:
            ThermalEventInstance: The instantiated thermal event instance.
        """

        # Keep only the largest blob in the mask (to extract the main polygon)
        cnts, _ = cv2.findContours(
            np.array(mask == mask_value, dtype=np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )
        # Retain the polygon with the largest area
        polygon = np.squeeze(max(cnts, key=cv2.contourArea), axis=1)

        return ThermalEventInstance.from_polygon(
            polygon, timestamp_ns, ir_image, max_polygon_string_length
        )

    @classmethod
    def from_polygon(
        cls,
        polygon: Union[list, np.ndarray],
        timestamp_ns: int,
        ir_image: np.ndarray = None,
        max_polygon_string_length: int = 256,
    ) -> "ThermalEventInstance":
        """
        Create a ThermalEventInstance instance from a polygon.

        Args:
            polygon (Union[list, np.ndarray]): The polygon.
            timestamp_ns (int): The timestamp of the instance, in nanosecond.
            ir_image (np.ndarray, optional): The infrared image. Defaults to None.
            max_polygon_string_length (int, optional): The maximum number of
                characters used to encode the polygon in the form "x0 y0 x1 y1 ...".
                Defaults to 256.

        Returns:
            ThermalEventInstance: The instantiated thermal event instance.
        """
        instance = cls(timestamp_ns=timestamp_ns)

        # If needed, simplify the polygon
        nb_points = len(polygon) - 1
        simplifier = VWSimplifier(np.array(polygon, dtype=float))
        while len(polygon_to_string(polygon)) > max_polygon_string_length:
            polygon = simplifier.from_number(nb_points).astype(int)
            nb_points -= 1

        polygon = np.array(np.round(polygon), dtype=np.int32)

        # Remove duplicate rows in the polygon
        _, idx = np.unique(polygon, axis=0, return_index=True)
        polygon = polygon[np.sort(idx)]

        instance.polygon = polygon_to_string(polygon)
        rect = polygon_is_rectangle(polygon)
        if rect is None:
            rect = bounding_rectangle(polygon)

        instance.bbox_x = int(rect[0])
        instance.bbox_y = int(rect[1])
        instance.bbox_width = int(rect[2])
        instance.bbox_height = int(rect[3])

        if ir_image is not None:
            instance.set_image(ir_image)

        # TODO Perform specific calculations if the scene model is available

        return instance

    @classmethod
    def from_rectangle(
        cls,
        rect: Union[list, np.ndarray],
        timestamp_ns: int = None,
        ir_image: np.ndarray = None,
    ) -> "ThermalEventInstance":
        """Set the instance polygon from a rectangle (x, y, w, h) and fill instance
        related members.

        Args:
            polygon (Union[list, np.ndarray]): The rectangle (x, y, w, h) from which to
                create the instance.
            timestamp_ns (int): The timestamp of the instance, in nanosecond.
            ir_image (np.ndarray, optional): The infrared image. Defaults to None.

        Returns:
            ThermalEventInstance: The instantiated thermal event instance.
        """
        instance = cls(timestamp_ns=timestamp_ns)

        instance.timestamp_ns = int(timestamp_ns)

        instance.bbox_x = int(rect[0])
        instance.bbox_y = int(rect[1])
        instance.bbox_width = int(rect[2])
        instance.bbox_height = int(rect[3])
        polygon = np.array(
            [
                [instance.bbox_x, instance.bbox_y],
                [instance.bbox_x + instance.bbox_width - 1, instance.bbox_y],
                [
                    instance.bbox_x + instance.bbox_width - 1,
                    instance.bbox_y + instance.bbox_height - 1,
                ],
                [instance.bbox_x, instance.bbox_y + instance.bbox_height - 1],
            ]
        )
        instance.polygon = polygon_to_string(polygon)

        if ir_image is not None:
            instance.set_image(ir_image)

        # TODO Perform specific calculations if the scene model is available

        return instance

    def set_image(self, ir_image: np.ndarray) -> None:
        """Update temperature-related members using an infrared image.

        Args:
            ir_image (np.ndarray): The infrared image.
        """
        polygon = self.polygon_as_list

        x_0, y_0 = np.min(polygon, 0)
        x_1, y_1 = np.max(polygon, 0)
        polygon = np.array(polygon) - [x_0, y_0]
        ir_image = ir_image[y_0 : y_1 + 1, x_0 : x_1 + 1]

        mask = cv2.fillPoly(np.zeros(ir_image.shape), [np.array(polygon)], color=1)
        coords = np.where(mask)
        ir_polygon = ir_image[coords]

        self.pixel_area = int(ir_polygon.size)

        self.max_temperature_C = int(ir_polygon.max())
        self.min_temperature_C = int(ir_polygon.min())
        self.average_temperature_C = float(ir_polygon.mean())

        self.centroid_image_position_x = float(x_0 + np.mean(coords[1]))
        self.centroid_image_position_y = float(y_0 + np.mean(coords[0]))

        posmax = np.argmax(ir_polygon)
        self.max_T_image_position_x = int(x_0 + coords[1][posmax])
        self.max_T_image_position_y = int(y_0 + coords[0][posmax])

        posmin = np.argmin(ir_polygon)
        self.min_T_image_position_x = int(x_0 + coords[1][posmin])
        self.min_T_image_position_y = int(y_0 + coords[0][posmin])

    def return_polygon(self) -> list:
        """Returns the instance closed polygon as a list.

        Returns:
            list: The instance closed polygon as a list.
        """
        poly = self.polygon_as_list
        if len(poly) > 0:
            return poly

        # compute polygon from rect
        res = [
            [self.bbox_x, self.bbox_y],
            [self.bbox_x + self.bbox_width - 1, self.bbox_y],
            [
                self.bbox_x + self.bbox_width - 1,
                self.bbox_y + self.bbox_height - 1,
            ],
            [self.bbox_x, self.bbox_y + self.bbox_height - 1],
        ]
        return res

    @property
    def polygon_as_list(self) -> list:
        """Return the polygon as a list.

        Returns:
            list: The polygon as a list.
        """
        return string_to_polygon(self.polygon)
