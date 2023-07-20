import json
from typing import Union

import cv2
import numpy as np
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
)
from sqlalchemy.dialects.mysql import DOUBLE
from sqlalchemy.orm import relationship, make_transient

from .base import Base
from .hot_spot import BigIntegerType, HotSpot, polygon_to_string, string_to_polygon
from .polysimplify import VWSimplifier


class ThermalEvent(Base):
    """Represents a thermal event."""

    __tablename__ = "thermal_events"
    id = Column(
        BigIntegerType, primary_key=True, autoincrement=True, index=True, unique=True
    )
    pulse = Column(DOUBLE(asdecimal=False), nullable=False, comment="Pulse number")
    line_of_sight = Column(
        String(255),
        index=True,
        comment="Line of sight on which the thermal event occurs",
    )
    device = Column(
        String(255), ForeignKey("devices.name"), nullable=False, comment="Device name"
    )
    initial_timestamp = Column(
        BigInteger,
        nullable=False,
        default=0,
        index=True,
        comment="Timestamp when the thermal event begins, in nanosecond",
    )
    final_timestamp = Column(
        BigInteger,
        nullable=False,
        default=0,
        index=True,
        comment="Timestamp when the thermal event ends, in nanosecond",
    )
    duration = Column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Duration of the thermal event, in nanosecond",
    )
    thermal_event = Column(String(255), index=True, comment="The type of thermal event")
    is_automatic_detection = Column(
        Boolean,
        comment="Boolean indicating if the detection was automatic or manual (a "
        + "manual annotation)",
    )
    maximum = Column(
        Float,
        default=0,
        comment="Maximum apparent temperature in the hot spot, in degree celsius",
    )
    time_constant_increase = Column(
        Float,
        default=0,
        comment="Thermal time constant of the component, when heating, in nanosecond",
    )
    time_constant_decrease = Column(
        Float,
        default=0,
        comment="Thermal time constant of the component, when cooling, in nanosecond",
    )
    method = Column(String(255), comment="The detection or annotation method")
    polygon = Column(
        String(600),
        comment="Polygon x0, y0, ..., xn, yn encompassing all the hot spots "
        + "constituting the thermal event, with the coordinates in pixel",
    )
    user_polygon_proposal = Column(
        String(600),
        comment="Polygon x0, y0, ..., xn proposed by the annotator, when using "
        + "the semi-automatic annotation tool",
    )
    confidence = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Confidence in the detection or annotation, higher is better",
    )
    user = Column(
        String(255),
        ForeignKey("users.name"),
        index=True,
        comment="Name of the user who created the thermal event",
    )
    comments = Column(String(255), comment="Comments describing the thermal event")
    surname = Column(
        String(255),
        comment="Unique name given to the thermal event, for easier reference later",
    )
    roi_name = Column(
        String(255),
        comment="Name of the region of interest (RoI) on which the thermal event "
        + "occured",
    )
    dataset = Column(
        String(64),
        default="1",
        index=True,
        comment="Dataset to which the thermal event belongs, 1 is the catch-all "
        + "dataset",
    )
    analysis_status = Column(
        String(64),
        ForeignKey("analysis_status.name"),
        default="Not Analyzed",
        index=True,
        comment="Current status of analysis of the thermal event",
    )

    _computed = None

    __table_args__ = (
        ForeignKeyConstraint(
            ["thermal_event", "line_of_sight"],
            [
                "thermal_event_type_lines_of_sight.thermal_event_type",
                "thermal_event_type_lines_of_sight.line_of_sight",
            ],
        ),
        {},
    )

    hot_spots = relationship(
        "HotSpot",
        order_by=HotSpot.id,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="subquery",
        back_populates="thermal_event",
    )

    def __init__(
        self,
        pulse: float = 0,
        line_of_sight: str = str(),
        device: str = str(),
        event_name: str = str(),
        is_automatic_detection: bool = False,
        method: str = str(),
        user: str = str(),
        comments: str = str(),
        surname: str = str(),
        user_polygon_proposal: list = None,
        dataset: Union[str, list] = "1",
        analysis_status: str = "Not Analyzed",
        confidence: int = 1,
        **kwargs
    ) -> None:
        """
        Initialize a ThermalEvent object.

        Args:
            pulse (float): Pulse number.
            line_of_sight (str): Line of sight on which the thermal event occurs.
            device (str): Device name.
            event_name (str): The type of thermal event.
            is_automatic_detection (bool): Boolean indicating if the detection was
                automatic or manual.
            method (str): The detection or annotation method.
            user (str): Name of the user who created the thermal event.
            comments (str): Comments describing the thermal event.
            surname (str): Unique name given to the thermal event.
            user_polygon_proposal (list): Polygon proposed by the annotator.
            dataset (Union[str, list]): Dataset to which the thermal event belongs.
            analysis_status (str): Current status of analysis of the thermal event.
            confidence (int): Confidence in the detection or annotation.

        Keyword Args:
            hot_spots (list): List of HotSpot objects associated with the thermal event.

        Returns:
            None
        """
        if isinstance(user_polygon_proposal, list):
            # Simplify the polygon if its number of points is greater than the
            # maximum number of points that can be stored in the database
            max_points = 75
            nb_points = max_points
            if len(user_polygon_proposal) > nb_points:
                init_poly = np.array(user_polygon_proposal).astype(float)
                poly = init_poly

                while len(poly) > max_points:
                    simplifier = VWSimplifier(init_poly)
                    poly = simplifier.from_number(max_points)
                    nb_points -= 1
                user_polygon_proposal = np.array(np.round(poly), dtype=np.int32)

            user_polygon_proposal = polygon_to_string(user_polygon_proposal)

        self.pulse = float(pulse)
        self.line_of_sight = line_of_sight
        self.device = device
        self.thermal_event = event_name
        self.is_automatic_detection = is_automatic_detection
        self.method = method
        self.user = user
        self.comments = comments
        self.surname = surname
        self.user_polygon_proposal = user_polygon_proposal

        # If several datasets are provided in a list, order and convert them to a string
        if isinstance(dataset, list):
            dataset.sort()
            dataset = ", ".join([str(x) for x in dataset])
        self.dataset = str(dataset)

        self.analysis_status = analysis_status
        self.confidence = confidence

        self._computed = None

        # Handles magic to create object from dictionnary
        if kwargs:
            for key, value in kwargs.items():
                # If the key is a time, make sure the value is an int
                if "timestamp" in key or key == "duration":
                    value = int(value)

                if key == "hot_spots":
                    hot_spots = [HotSpot(**x) for x in value]
                    self.hot_spots = hot_spots
                else:
                    setattr(self, key, value)
            if "hot_spots" in kwargs:
                self.compute()

    @classmethod
    def from_json(cls, path_to_file):
        """
        Create a ThermalEvent object from a JSON file.

        Args:
            path_to_file (str): Path to the JSON file.

        Returns:
            ThermalEvent or list[ThermalEvent]: The created ThermalEvent object(s).
        """
        with open(path_to_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        out = []
        for key in data:
            out.append(ThermalEvent(**data[key]))

        if len(out) == 1:
            out = out[0]

        return out

    @classmethod
    def from_dict(cls, data):
        """
        Create a ThermalEvent object from a dictionary.

        Args:
            data (dict): The dictionary containing the ThermalEvent data.

        Returns:
            ThermalEvent: The created ThermalEvent object.
        """
        out = cls(**data)
        hot_spots = [HotSpot(**x) for x in data["hot_spots"]]
        out.hot_spots = hot_spots
        out.compute()
        return out

    def add_hot_spot(self, hot_spot: HotSpot) -> None:
        """
        Add a new hot_spot to an event.

        Args:
            hot_spot (HotSpot): The HotSpot object to be added.

        Returns:
            None
        """
        self.hot_spots.append(hot_spot)

    def compute_global_polygon(self) -> list:
        """
        Compute the global polygon of the thermal event.

        Returns:
            list: The computed global polygon.
        """
        return np.squeeze(
            cv2.convexHull(np.vstack([x.return_polygon() for x in self.hot_spots])),
            axis=1,
        )

    def compute(self) -> None:
        """
        Perform computation and update relevant attributes of the ThermalEvent object.

        Returns:
            None
        """
        if self._computed == len(self.hot_spots):
            # already done
            return

        # Sort hot_spots by timestamp
        d = {}
        for s in self.hot_spots:
            d[s.timestamp] = s
        # order by timestamp
        sort = sorted(d.items())
        self.hot_spots = []
        self.maximum = sort[0][1].max_intensity
        for s in sort:
            self.hot_spots.append(s[1])
            if s[1].max_intensity is not None:
                self.maximum = max(self.maximum, s[1].max_intensity)

        self.initial_timestamp = int(self.timestamps[0])
        self.final_timestamp = int(self.timestamps[-1])
        self.duration = self.final_timestamp - self.initial_timestamp
        poly = self.compute_global_polygon()

        # Simplify the polygon if its number of points is greater than the
        # maximum number of points that can be stored in the database
        max_points = 75
        nb_points = max_points
        if len(poly) > nb_points:
            init_poly = np.array(poly).astype(float)
            poly = init_poly

            while len(poly) > max_points:
                simplifier = VWSimplifier(init_poly)
                poly = simplifier.from_number(max_points)
                nb_points -= 1
            poly = np.array(np.round(poly), dtype=np.int32)

        self.polygon = polygon_to_string(poly)

        self._computed = len(self.hot_spots)

    def to_json(self, path_to_file):
        """
        Serialize the ThermalEvent object to a JSON file.

        Args:
            path_to_file (str): Path to the output JSON file.

        Returns:
            None
        """
        from .schemas import ThermalEventSchema

        dump_data = ThermalEventSchema().dump(self)

        with open(path_to_file, "w", encoding="utf-8") as file:
            json.dump(dump_data, file, ensure_ascii=False, indent=4)

    @property
    def timestamps(self) -> list:
        """
        Get the timestamps of all hot spots.

        Returns:
            list: The timestamps.
        """
        return [x.timestamp for x in self.hot_spots]

    @property
    def polygon_as_list(self) -> list:
        """
        Get the polygon as a list.

        Returns:
            list: The polygon as a list.
        """
        return string_to_polygon(self.polygon)

    @property
    def user_polygon_proposal_as_list(self) -> list:
        """
        Get the user's polygon proposal as a list.

        Returns:
            list: The user's polygon proposal as a list.
        """
        return string_to_polygon(self.user_polygon_proposal)

    @staticmethod
    def write_events_to_json(path_to_file: str, thermal_events: list):
        """
        Write a list of ThermalEvent objects to a JSON file.

        Args:
            path_to_file (str): Path to the output JSON file.
            thermal_events (list): List of ThermalEvent objects to be written.

        Returns:
            None
        """
        from .schemas import ThermalEventSchema

        if not isinstance(thermal_events, list):
            thermal_events = [thermal_events]

        out = {}
        for ind, event in enumerate(thermal_events):
            make_transient(event)
            [make_transient(x) for x in event.hot_spots]
            out[ind] = ThermalEventSchema().dump(event)

        with open(path_to_file, "w", encoding="utf-8") as file:
            json.dump(out, file, ensure_ascii=False, indent=4)
