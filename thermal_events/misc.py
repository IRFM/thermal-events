from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from .base import Base
from .thermal_event_instance import BigIntegerType


class Device(Base):
    """Model class representing a fusion device."""

    __tablename__ = "devices"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the device",
    )
    description = Column(String(255), comment="Description of the device")


class LineOfSight(Base):
    """Model class representing a line of sight entity."""

    __tablename__ = "lines_of_sight"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the line of sight",
    )
    description = Column(String(255), comment="Description of the line of sight")


class Category(Base):
    """Model class representing a category of thermal event entity."""

    __tablename__ = "thermal_event_categories"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the category of thermal event",
    )
    description = Column(
        String(255), comment="Description of the category of thermal event"
    )


class ThermalEventCategoryLineOfSight(Base):
    """Model class representing the relationship between thermal event categories and
    lines of sight."""

    __tablename__ = "thermal_event_category_lines_of_sight"

    thermal_event_category = Column(
        String(255),
        ForeignKey("thermal_event_categories.name"),
        primary_key=True,
        index=True,
        comment="Name of the category of thermal event",
    )
    line_of_sight = Column(
        String(255),
        ForeignKey("lines_of_sight.name"),
        primary_key=True,
        index=True,
        comment="Name of the line of sight",
    )


class Severity(Base):
    """Model class representing the severity of a thermal event."""

    __tablename__ = "severity_types"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the severity type",
    )
    description = Column(String(255), comment="Description of the severity type")


class Method(Base):
    """Model class representing a detection or annotation method."""

    __tablename__ = "methods"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the method",
    )
    description = Column(
        String(255), comment="Description of the detection or annotation method"
    )


class User(Base):
    """Model class representing a user entity."""

    __tablename__ = "users"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the user",
    )
    email = Column(String(64), comment="The email address of the user")


class Dataset(Base):
    """Model class representing a dataset entity."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, unique=True)
    creation_date = Column(
        DateTime, nullable=False, comment="Date of creation of the dataset"
    )
    annotation_type = Column(
        String(32),
        nullable=False,
        comment="Type of annotations containted in the dataset",
    )
    description = Column(String(255), comment="Description of the dataset")


class AnalysisStatus(Base):
    """Model class representing an analysis status entity."""

    __tablename__ = "analysis_status"

    name = Column(
        String(64),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the analysis status",
    )
    description = Column(String(255), comment="Description of the analysis status")


class ParentChildRelationship(Base):
    """Model class representing the relationship between a parent thermal event and
    a child thermal event."""

    __tablename__ = "thermal_events_genealogy"

    parent = Column(
        BigIntegerType,
        ForeignKey("thermal_events.id"),
        primary_key=True,
        index=True,
        comment="Parent thermal event id",
    )

    child = Column(
        BigIntegerType,
        ForeignKey("thermal_events.id"),
        primary_key=True,
        index=True,
        comment="Child thermal event id",
    )

    timestamp_ns = Column(
        BigIntegerType,
        primary_key=True,
        index=True,
        comment="Timestamp after which the splitting or merging happened, "
        + "in nanosecond",
    )


PARAMETERS_LIMIT = 1024


class ProcessedMovie(Base):
    """Represents a processed infrared movie."""

    __tablename__ = "processed_movies"
    id = Column(
        BigIntegerType, primary_key=True, autoincrement=True, index=True, unique=True
    )

    experiment_id = Column(BigIntegerType, nullable=False, comment="Experiment id")
    line_of_sight = Column(
        String(255),
        ForeignKey("lines_of_sight.name"),
        index=True,
        comment="Line of sight",
    )
    method = Column(
        String(255),
        nullable=False,
        comment="The detection method",
    )
    parameters = Column(
        String(PARAMETERS_LIMIT), nullable=False, comment="Parameters of the method"
    )
    processing_date = Column(
        DateTime, nullable=False, comment="Date of processing of the movie"
    )
    comments = Column(String(255), comment="Comments describing the thermal event")

    def __init__(
        self,
        experiment_id: int,
        line_of_sight: str,
        method: str,
        parameters: str,
        comments: str = "",
    ) -> None:
        """
        Initialize a ProcessedMovie.

        """
        if len(parameters) > PARAMETERS_LIMIT:
            print(
                f"Warning: the provided parameters are too long, truncating them to {PARAMETERS_LIMIT} characters"
            )
            parameters = parameters[:PARAMETERS_LIMIT]

        self.experiment_id = experiment_id
        self.line_of_sight = line_of_sight
        self.method = method
        self.parameters = parameters
        self.comments = comments
        self.processing_date = datetime.now()
