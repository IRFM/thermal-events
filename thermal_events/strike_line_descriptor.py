from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
)
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.mysql import DOUBLE
from sqlalchemy.orm import relationship

from .base import Base
from .thermal_event_instance import (
    BigIntegerType,
    ThermalEventInstance,
    polygon_to_string,
    string_to_polygon,
)

DoubleType = DOUBLE(asdecimal=False).with_variant(sqlite.REAL(), "sqlite")


class StrikeLineDescriptor(Base):
    """Represents a strike line descriptor."""

    __tablename__ = "strike_line_descriptors"
    id = Column(
        BigIntegerType, primary_key=True, autoincrement=True, index=True, unique=True
    )

    thermal_event_instance_id = Column(
        BigIntegerType,
        ForeignKey("thermal_events_instances.id"),
        index=True,
        comment="The id of the thermal event instance described by the descriptor",
    )

    segmented_points = Column(
        String(256),
        nullable=False,
        comment="The segmented points in the cropped image of the strike line",
    )
    angle = Column(
        DoubleType, nullable=False, comment="The angle of the strike line, in degrees"
    )
    curve = Column(
        DoubleType,
        nullable=False,
        comment="The curvature of the strike line (categorical)",
    )
    comments = Column(String(255), comment="Comments describing the thermal event")
    flag_RT = Column(
        Boolean,
        comment="A boolean flag indicating if the object has been computed in real time or not",
    )

    instance = relationship(
        "ThermalEventInstance",
        lazy="subquery",
        back_populates="strike_line_descriptor",
    )

    def __init__(
        self,
        instance: ThermalEventInstance = None,
        segmented_points: list = [],
        angle: float = 0.0,
        curve: float = 0.0,
        comments: str = str(),
        flag_RT: bool = False,
        **kwargs
    ) -> None:
        self.instance = instance
        if not isinstance(segmented_points, str):
            segmented_points = polygon_to_string(segmented_points)
        self.segmented_points = segmented_points
        self.angle = angle
        self.curve = curve
        self.comments = comments
        self.flag_RT = flag_RT

        # Handles magic to create object from dictionnary
        if kwargs:
            for key, value in kwargs.items():
                if key == "instance":
                    self.instance = ThermalEventInstance(**value)
                elif key == "segmented_points" and not isinstance(value, str):
                    self.segmented_points = polygon_to_string(value)
                else:
                    setattr(self, key, value)

    def return_segmented_points(self) -> list:
        """Returns the segmented points as a list.

        Returns:
            list: The segmented points as a list.
        """
        return self.segmented_points_as_list

    @property
    def segmented_points_as_list(self) -> list:
        """Return the segmented points as a list.

        Returns:
            list: The segmented points as a list.
        """
        return string_to_polygon(self.segmented_points)
