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


class HotSpot(Base):
    __tablename__ = "hot_spots"

    id = Column(
        BigIntegerType, primary_key=True, autoincrement=True, index=True, unique=True
    )
    timestamp = Column(
        BigInteger, nullable=False, comment="Current timestamp, in nanosecond"
    )
    id_thermal_event = Column(
        BigInteger,
        ForeignKey("thermal_events.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        comment="ID of the thermal event to which the hot spot belongs",
    )
    left_box = Column(
        Integer,
        nullable=False,
        default=0,
        comment="x coordinate of the upper left corner of the bounding box, in pixel",
    )
    top_box = Column(
        Integer,
        nullable=False,
        default=0,
        comment="y coordinate of the upper left corner of the bounding box, in pixel",
    )
    width_box = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Width of the bounding box, in pixel",
    )
    height_box = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Height of the bounding box, in pixel",
    )
    max_intensity = Column(
        Float,
        default=0,
        comment="Maximum apparent temperature in the hot spot, in degree celsius",
    )
    max_location_x = Column(
        Integer,
        default=0,
        comment="x coordinate of the maximum apparent temperature, in pixel",
    )
    max_location_y = Column(
        Integer,
        default=0,
        comment="y coordinate of the maximum apparent temperature, in pixel",
    )
    min_intensity = Column(
        Float,
        default=0,
        comment="Minimum apparent temperature in the hot spot, in degree celsius",
    )
    min_location_x = Column(
        Integer,
        default=0,
        comment="x coordinate of the minimum apparent temperature, in pixel",
    )
    min_location_y = Column(
        Integer,
        default=0,
        comment="y coordinate of the minimum apparent temperature, in pixel",
    )
    mean_intensity = Column(
        Float,
        default=0,
        comment="Average apparent temperature in the hot spot, in degree celsius",
    )
    std_intensity = Column(
        Float,
        default=0,
        comment="Standard deviation of the apparent temperature in the hot spot, in "
        + "degree celsius",
    )
    area = Column(Integer, default=0, comment="The area of the hot spot, in pixel")
    centroid_x = Column(
        Float,
        default=0,
        comment="x coordinate of the centroid of the hot spot, in pixel",
    )
    centroid_y = Column(
        Float,
        default=0,
        comment="y coordinate of the centroid of the hot spot, in pixel",
    )
    polygon = Column(
        String(256),
        comment="Polygon x0, y0, ..., xn, yn encompassing the hot spot, with the "
        + "coordinates in pixel",
    )
    quantile_5 = Column(
        String(20),
        comment="Bounding box x0, y0, w, h of the 5% hottest pixels in the hot spot, "
        + "with the coordinates in pixel",
    )
    quantile_10 = Column(
        String(20),
        comment="Bounding box x0, y0, w, h of the 10% hottest pixels in the hot spot, "
        + "with the coordinates in pixel",
    )
    quantile_25 = Column(
        String(20),
        comment="Bounding box x0, y0, w, h of the 25% hottest pixels in the hot spot, "
        + "with the coordinates in pixel",
    )
    quantile_50 = Column(
        String(20),
        comment="Bounding box x0, y0, w, h of the 50% hottest pixels in the hot spot, "
        + "with the coordinates in pixel",
    )

    thermal_event = relationship(
        "ThermalEvent", back_populates="hot_spots", uselist=False
    )

    _buffer = None  # image bugger used to draw polygons
    _mutex = Lock()

    _compute_quantiles = False

    def __init__(
        self,
        timestamp: Union[int, None] = None,
        compute_quantiles: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize a HotSpot instance.

        Args:
            timestamp (Union[int, None], optional): The timestamp. Defaults to None.
            compute_quantiles (bool, optional): Whether to compute quantiles. Defaults
                to False.
            **kwargs: Additional keyword arguments for the HotSpot instance.
        """
        self.timestamp = int(timestamp)
        self._compute_quantiles = compute_quantiles
        self._confidence = None

        for key, value in kwargs.items():
            if key == "polygon" and not isinstance(value, str):
                value = polygon_to_string(value)

            if key != "thermal_event":
                setattr(self, key, value)

    @classmethod
    def from_mask(
        cls,
        mask: np.ndarray,
        mask_value: int,
        timestamp: int = None,
        ir_image: np.ndarray = None,
        compute_quantiles: bool = False,
        max_polygon_length: int = 256,
    ) -> "HotSpot":
        """
        Create a HotSpot instance from a binary mask.

        Args:
            mask (np.ndarray): The binary mask.
            mask_value (int): The value in the mask that corresponds to the hot spot.
            timestamp (int, optional): The timestamp. Defaults to None.
            ir_image (np.ndarray, optional): The infrared image. Defaults to None.
            compute_quantiles (bool, optional): Whether to compute quantiles. Defaults
                to False.
            max_polygon_length (int, optional): The maximum number of characters used
                to encode the polygon in the form "x0 y0 x1 y1 ...". Defaults to 256.

        Returns:
            HotSpot: The instantiated hot spot.
        """

        hot_spot = cls(timestamp=timestamp, compute_quantiles=compute_quantiles)

        # Keep only the largest blob in the mask (to extract the main polygon)
        cnts, _ = cv2.findContours(
            np.array(mask == mask_value, dtype=np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )
        # Retain the polygon with the largest area
        polygon = np.squeeze(max(cnts, key=cv2.contourArea), axis=1)

        # If needed, simplify the polygon
        nb_points = len(polygon) - 1
        simplifier = VWSimplifier(np.array(polygon, dtype=float))
        while len(polygon_to_string(polygon)) > max_polygon_length:
            polygon = simplifier.from_number(nb_points).astype(int)
            nb_points -= 1

        polygon = np.array(np.round(polygon), dtype=np.int32)

        # Remove duplicate rows in the polygon
        _, idx = np.unique(polygon, axis=0, return_index=True)
        polygon = polygon[np.sort(idx)]

        hot_spot.polygon = polygon_to_string(polygon)
        rect = polygon_is_rectangle(polygon)
        if rect is None:
            rect = bounding_rectangle(polygon)
            hot_spot.left_box = int(rect[0])
            hot_spot.top_box = int(rect[1])
            hot_spot.width_box = int(rect[2])
            hot_spot.height_box = int(rect[3])
        else:
            hot_spot.left_box = int(rect[0])
            hot_spot.top_box = int(rect[1])
            hot_spot.width_box = int(rect[2])
            hot_spot.height_box = int(rect[3])

        if timestamp is not None:
            hot_spot.timestamp = int(timestamp)
        if ir_image is not None:
            # get polygon covered pixels
            coords = np.unravel_index(np.where(mask.ravel() == mask_value), mask.shape)
            ir_polygon = ir_image[coords]
            hot_spot.area = int(ir_polygon.shape[0])
            hot_spot.max_intensity = float(ir_polygon.max())
            hot_spot.min_intensity = float(ir_polygon.min())
            hot_spot.mean_intensity = float(ir_polygon.mean())
            hot_spot.std_intensity = float(np.std(ir_polygon))
            hot_spot.centroid_x = float(np.mean(coords[1]))
            hot_spot.centroid_y = float(np.mean(coords[0]))
            posmax = np.argmax(ir_polygon)
            posmin = np.argmin(ir_polygon)
            hot_spot.max_location_x = int(coords[1][0][posmax])
            hot_spot.max_location_y = int(coords[0][0][posmax])
            hot_spot.min_location_x = int(coords[1][0][posmin])
            hot_spot.min_location_y = int(coords[0][0][posmin])

            if hot_spot._compute_quantiles:
                quantile_list = [50, 25, 10, 5]
                quantiles = np.quantile(
                    ir_polygon, [1 - q / 100 for q in quantile_list]
                )
                for cnt, quantile in enumerate(quantiles):
                    ind = np.squeeze(ir_polygon >= quantile)
                    coords_x = coords[1][0][ind]
                    coords_y = coords[0][0][ind]

                    x0 = np.min(coords_x)
                    x1 = np.max(coords_x)
                    y0 = np.min(coords_y)
                    y1 = np.max(coords_y)

                    # Add the bounding box (left, top, width, height) to the
                    # associated attribute
                    setattr(
                        hot_spot,
                        f"quantile_{quantile_list[cnt]}",
                        f"{x0} {y0} {x1 - x0 + 1} {y1 - y0 + 1}",
                    )
        return hot_spot

    @classmethod
    def from_polygon(
        cls,
        polygon: Union[list, np.ndarray],
        timestamp: int = None,
        ir_image: np.ndarray = None,
        compute_quantiles: bool = False,
        max_polygon_length: int = 256,
    ) -> "HotSpot":
        """
        Create a HotSpot instance from a polygon.

        Args:
            polygon (Union[list, np.ndarray]): The polygon.
            timestamp (int, optional): The timestamp. Defaults to None.
            ir_image (np.ndarray, optional): The infrared image. Defaults to None.
            compute_quantiles (bool, optional): Whether to compute quantiles. Defaults
                to False.
            max_polygon_length (int, optional): The maximum number of characters used
                to encode the polygon in the form "x0 y0 x1 y1 ...". Defaults to 256.

        Returns:
            HotSpot: The instantiated hot spot.
        """
        hot_spot = cls(timestamp=timestamp, compute_quantiles=compute_quantiles)

        # If needed, simplify the polygon
        nb_points = len(polygon) - 1
        simplifier = VWSimplifier(np.array(polygon, dtype=float))
        while len(polygon_to_string(polygon)) > max_polygon_length:
            polygon = simplifier.from_number(nb_points).astype(int)
            nb_points -= 1

        polygon = np.array(np.round(polygon), dtype=np.int32)

        # Remove duplicate rows in the polygon
        _, idx = np.unique(polygon, axis=0, return_index=True)
        polygon = polygon[np.sort(idx)]

        hot_spot.polygon = polygon_to_string(polygon)
        rect = polygon_is_rectangle(polygon)
        if rect is None:
            rect = bounding_rectangle(polygon)
            hot_spot.left_box = int(rect[0])
            hot_spot.top_box = int(rect[1])
            hot_spot.width_box = int(rect[2])
            hot_spot.height_box = int(rect[3])
        else:
            hot_spot.left_box = int(rect[0])
            hot_spot.top_box = int(rect[1])
            hot_spot.width_box = int(rect[2])
            hot_spot.height_box = int(rect[3])

        if timestamp is not None:
            hot_spot.timestamp = int(timestamp)
        if ir_image is not None:
            hot_spot.set_image(ir_image)

        return hot_spot

    @classmethod
    def from_rectangle(
        cls,
        rect: Union[list, np.ndarray],
        timestamp: int = None,
        ir_image: np.ndarray = None,
        compute_quantiles: bool = False,
    ) -> "HotSpot":
        """Set the hot spot polygon from a rectangle (x, y, w, h) and fill hot spot
        related members.

        Args:
            polygon (Union[list, np.ndarray]): The rectangle (x, y, w, h) from which to
                create the hot spot.
            timestamp (int, optional): The current timestamp. Defaults to None.
            ir_image (np.ndarray, optional): The infrared image. Defaults to None.

        Returns:
            HotSpot: The instantiated hot spot.
        """
        hot_spot = cls(timestamp=timestamp, compute_quantiles=compute_quantiles)

        hot_spot.left_box = int(rect[0])
        hot_spot.top_box = int(rect[1])
        hot_spot.width_box = int(rect[2])
        hot_spot.height_box = int(rect[3])
        poly = np.array(
            [
                [hot_spot.left_box, hot_spot.top_box],
                [hot_spot.left_box + hot_spot.width_box, hot_spot.top_box],
                [
                    hot_spot.left_box + hot_spot.width_box,
                    hot_spot.top_box + hot_spot.height_box,
                ],
                [hot_spot.left_box, hot_spot.top_box + hot_spot.height_box],
                [hot_spot.left_box, hot_spot.top_box],
            ]
        )
        hot_spot.polygon = polygon_to_string(poly)
        if timestamp is not None:
            hot_spot.timestamp = int(timestamp)
        if ir_image is not None:
            hot_spot.set_image(ir_image)

        return hot_spot

    def set_image(self, ir_image: np.ndarray) -> None:
        """Set the infrared image and update temperature-related members.

        Args:
            ir_image (np.ndarray): The infrared image.
        """
        poly = self.polygon_as_list

        # LEGACY
        if len(poly) == 0:
            # use the rectangle as polygon
            poly = [
                [self.left_box, self.top_box],
                [self.left_box + self.width_box - 1, self.top_box],
                [
                    self.left_box + self.width_box - 1,
                    self.top_box + self.height_box - 1,
                ],
                [self.left_box, self.top_box + self.height_box - 1],
            ]

        x_0, y_0 = np.min(poly, 0)
        x_1, y_1 = np.max(poly, 0)
        poly = np.array(poly) - [x_0, y_0]
        ir_image = ir_image[y_0 : y_1 + 1, x_0 : x_1 + 1]

        mask = cv2.fillPoly(np.zeros(ir_image.shape), [np.array(poly)], color=1)
        coords = np.where(mask)
        ir_polygon = ir_image[coords]

        self.area = int(ir_polygon.size)
        self.max_intensity = float(ir_polygon.max())
        self.min_intensity = float(ir_polygon.min())
        self.mean_intensity = float(ir_polygon.mean())
        self.std_intensity = float(np.std(ir_polygon))
        self.centroid_x = x_0 + float(np.mean(coords[1]))
        self.centroid_y = y_0 + float(np.mean(coords[0]))
        posmax = np.argmax(ir_polygon)
        posmin = np.argmin(ir_polygon)
        self.max_location_x = x_0 + int(coords[1][posmax])
        self.max_location_y = y_0 + int(coords[0][posmax])
        self.min_location_x = x_0 + int(coords[1][posmin])
        self.min_location_y = y_0 + int(coords[0][posmin])

        if self._compute_quantiles:
            # TODO Check if fix with x0, y0 OK
            quantile_list = [50, 25, 10, 5]
            quantiles = np.quantile(ir_polygon, [1 - q / 100 for q in quantile_list])
            for cnt, quantile in enumerate(quantiles):
                ind = np.squeeze(ir_polygon >= quantile)
                coords_x = coords[1][ind]
                coords_y = coords[0][ind]

                x_0_q = np.min(coords_x)
                x_1_q = np.max(coords_x)
                y_0_q = np.min(coords_y)
                y_1_q = np.max(coords_y)

                # Add the bounding box (left, top, width, height) to the
                # associated attribute
                setattr(
                    self,
                    f"quantile_{quantile_list[cnt]}",
                    f"{x_0 + x_0_q} {y_0 + y_0_q} {x_1_q - x_0_q + 1} "
                    + f"{y_1_q - y_0_q + 1}",
                )

    def return_polygon(self) -> list:
        """Returns the hot spot closed polygon as a list.

        Returns:
            list: The hot spot closed polygon as a list.
        """
        poly = self.polygon_as_list
        if len(poly) > 0:
            if poly[0] != poly[-1]:
                poly.append(poly[0])
            return poly

        # compute polygon from rect
        res = [
            [self.left_box, self.top_box],
            [self.left_box + self.width_box - 1, self.top_box],
            [
                self.left_box + self.width_box - 1,
                self.top_box + self.height_box - 1,
            ],
            [self.left_box, self.top_box + self.height_box - 1],
            [self.left_box, self.top_box],
        ]
        return res

    @property
    def polygon_as_list(self) -> list:
        """Return the polygon as a list.

        Returns:
            list: The polygon as a list.
        """
        return string_to_polygon(self.polygon)
