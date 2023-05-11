from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from .base import Base


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


class ThermalEventType(Base):
    """Model class representing a type of thermal event entity."""

    __tablename__ = "thermal_event_types"

    name = Column(
        String(255),
        primary_key=True,
        index=True,
        unique=True,
        comment="Name of the type of thermal event",
    )
    description = Column(
        String(255), comment="Description of the type of thermal event"
    )


class ThermalEventTypeLineOfSight(Base):
    """Model class representing the relationship between thermal event types and
    lines of sight."""

    __tablename__ = "thermal_event_type_lines_of_sight"

    thermal_event_type = Column(
        String(255),
        ForeignKey("thermal_event_types.name"),
        primary_key=True,
        index=True,
        comment="Name of the type of thermal event",
    )
    line_of_sight = Column(
        String(255),
        ForeignKey("lines_of_sight.name"),
        primary_key=True,
        index=True,
        comment="Name of the line of sight",
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
