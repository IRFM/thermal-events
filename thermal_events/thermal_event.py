import json
from copy import deepcopy
from os.path import isfile
from typing import Union

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
)
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.mysql import DOUBLE
from sqlalchemy.orm import make_transient, relationship

from .base import Base
from .thermal_event_instance import (
    BigIntegerType,
    ThermalEventInstance,
)

DoubleType = DOUBLE(asdecimal=False).with_variant(sqlite.REAL(), "sqlite")


class ThermalEvent(Base):
    """Represents a thermal event."""

    __tablename__ = "thermal_events"
    id = Column(
        BigIntegerType, primary_key=True, autoincrement=True, index=True, unique=True
    )

    experiment_id = Column(BigIntegerType, nullable=False, comment="The experiment id")
    line_of_sight = Column(
        String(255),
        index=True,
        comment="Line of sight on which the thermal event occurs",
    )
    device = Column(
        String(255), ForeignKey("devices.name"), nullable=False, comment="Device name"
    )

    category = Column(
        String(255), index=True, comment="The category (class) of the thermal event"
    )

    initial_timestamp_ns = Column(
        BigIntegerType,
        nullable=False,
        index=True,
        comment="Timestamp when the thermal event begins, in nanosecond",
    )
    final_timestamp_ns = Column(
        BigIntegerType,
        nullable=False,
        index=True,
        comment="Timestamp when the thermal event ends, in nanosecond",
    )
    duration_ns = Column(
        BigIntegerType,
        nullable=False,
        comment="Duration of the thermal event, in nanosecond",
    )

    severity = Column(
        String(64),
        ForeignKey("severity_types.name"),
        index=True,
        comment="The severity of the thermal event",
    )

    is_automatic_detection = Column(
        Boolean,
        comment="Boolean indicating if the event was an automatic detection or a manual"
        + " annotation)",
    )
    method = Column(
        String(255),
        ForeignKey("methods.name"),
        nullable=False,
        comment="The detection or annotation method",
    )
    confidence = Column(
        DoubleType,
        nullable=False,
        default=0,
        comment="Confidence in the detection or annotation, between 0 and 1, "
        + "higher is better",
    )

    max_temperature_C = Column(
        Integer,
        comment="Maximum apparent temperature in the thermal event, in degree celsius",
    )
    max_T_timestamp_ns = Column(
        BigIntegerType,
        comment="Timestamp of the instance with the maximum apparent temperature, "
        + "in nanosecond. If several instances share the same global maximum, "
        + "only the timestamp of the first one is stored",
    )

    user = Column(
        String(255),
        ForeignKey("users.name"),
        index=True,
        comment="Name of the user who created the thermal event",
    )

    dataset = Column(
        String(64),
        default="1",
        index=True,
        comment="Dataset to which the thermal event belongs, 1 is the catch-all "
        + "dataset",
    )

    comments = Column(String(255), comment="Comments describing the thermal event")
    name = Column(
        String(255),
        comment="Unique name given to the thermal event, for easier reference later",
    )

    analysis_status = Column(
        String(64),
        ForeignKey("analysis_status.name"),
        default="not analyzed",
        index=True,
        comment="Current status of analysis of the thermal event",
    )

    _computed = False

    __table_args__ = (
        ForeignKeyConstraint(
            ["category", "line_of_sight"],
            [
                "thermal_event_category_lines_of_sight.thermal_event_category",
                "thermal_event_category_lines_of_sight.line_of_sight",
            ],
        ),
        {},
    )

    instances = relationship(
        "ThermalEventInstance",
        order_by=ThermalEventInstance.id,
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="subquery",
        back_populates="thermal_event",
    )

    def __init__(
        self,
        experiment_id: int = 0,
        line_of_sight: str = str(),
        device: str = str(),
        category: str = str(),
        is_automatic_detection: bool = False,
        confidence: float = 0.0,
        severity: str = None,
        method: str = str(),
        user: str = str(),
        comments: str = str(),
        surname: str = str(),
        dataset: Union[str, list] = "1",
        analysis_status: str = "not analyzed",
        **kwargs
    ) -> None:
        """
        Initialize a ThermalEvent object.

        Args:
            experiment_id (int): The experiment id.
            line_of_sight (str): Line of sight on which the thermal event occurs.
            device (str): Device name.
            category (str): The category (class) of thermal event.
            is_automatic_detection (bool): Boolean indicating if the detection was
                automatic or manual.
            confidence (float, optional): Confidence in the detection or annotation,
                between 0 and 1. Higher is better.
            severity (str, optional): The severity of the thermal event.
            method (str): The detection or annotation method.
            user (str): Name of the user who created the thermal event.
            comments (str): Comments describing the thermal event.
            surname (str): Unique name given to the thermal event.
            dataset (Union[str, list]): Dataset to which the thermal event belongs.
            analysis_status (str): Current status of analysis of the thermal event.

        Keyword Args:
            instances (list): List of ThermalEventInstance objects associated with
                the thermal event.

        Returns:
            None
        """
        # If several datasets are provided in a list, order and convert them to a string
        if isinstance(dataset, list):
            dataset.sort()
            dataset = ", ".join([str(x) for x in dataset])

        self.experiment_id = int(experiment_id)
        self.line_of_sight = line_of_sight
        self.device = device
        self.category = category
        self.is_automatic_detection = is_automatic_detection
        self.confidence = confidence
        self.severity = severity
        self.method = method
        self.user = user
        self.comments = comments
        self.name = surname
        self.dataset = str(dataset)
        self.analysis_status = analysis_status

        self._computed = False

        # Handles magic to create object from dictionnary
        if kwargs:
            for key, value in kwargs.items():
                # If the key is a time, make sure the value is an int
                if value is not None and ("timestamp" in key or key == "duration"):
                    value = int(value)

                if key == "thermal_events_instances":
                    instances = [ThermalEventInstance(**x) for x in value]
                    self.instances = instances
                else:
                    setattr(self, key, value)
            if "instances" in kwargs:
                self.compute()

    @classmethod
    def from_json(cls, string_or_path_to_file):
        """
        Create a ThermalEvent object from a JSON file.

        Args:
            string_or_path_to_file (str): JSON string or path to the JSON file.

        Returns:
            ThermalEvent or list[ThermalEvent]: The created ThermalEvent object(s).
        """

        is_path = isfile(string_or_path_to_file)

        if is_path:
            with open(string_or_path_to_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = json.loads(string_or_path_to_file)

        out = []
        for key in data:
            out.append(cls(**data[key]))

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
        return cls(**data)

    def add_instance(self, instance: ThermalEventInstance) -> None:
        """
        Add a new instance to an event.

        Args:
            instance (ThermalEventInstance): The ThermalEventInstance object to add.

        Returns:
            None
        """
        self.instances.append(instance)

    def compute(self) -> None:
        """
        Perform computation and update relevant attributes of the ThermalEvent object.

        Returns:
            None
        """
        if self._computed:
            return

        # Sort instances by timestamp
        d = {}
        for s in self.instances:
            d[s.timestamp_ns] = s
        # order by timestamp
        sort = sorted(d.items())
        self.instances = []
        if sort[0][1].max_temperature_C is not None:
            self.max_temperature_C = sort[0][1].max_temperature_C
            self.max_T_timestamp_ns = sort[0][1].timestamp_ns
        for s in sort:
            self.instances.append(s[1])
            if s[1].max_temperature_C is not None and (
                self.max_temperature_C is None
                or s[1].max_temperature_C > self.max_temperature_C
            ):
                self.max_temperature_C = s[1].max_temperature_C
                self.max_T_timestamp_ns = s[1].timestamp_ns

        self.initial_timestamp_ns = int(self.timestamps_ns[0])
        self.final_timestamp_ns = int(self.timestamps_ns[-1])
        self.duration_ns = self.final_timestamp_ns - self.initial_timestamp_ns

        self._computed = True

    def to_dict(self, use_id_as_key=False):
        from .schemas import ThermalEventSchema

        out = deepcopy(self)
        make_transient(out)
        [make_transient(x) for x in out.instances]
        if use_id_as_key:
            key = str(self.id)
        else:
            key = "0"
        return {key: ThermalEventSchema().dump(out)}

    def to_json(self, path_to_file):
        """
        Serialize the ThermalEvent object to a JSON file.

        Args:
            path_to_file (str): Path to the output JSON file.

        Returns:
            None
        """
        ThermalEvent.write_events_to_json(path_to_file, self)

    @property
    def timestamps_ns(self) -> list:
        """
        Get the timestamps of all the thermal event's instances.

        Returns:
            list: The timestamps, in nanosecond.
        """
        return [x.timestamp_ns for x in self.instances]

    @staticmethod
    def write_events_to_json(
        path_to_file: str, thermal_events: list, use_id_as_key=False
    ):
        """
        Write a list of ThermalEvent objects to a JSON file.

        Args:
            path_to_file (str): Path to the output JSON file. If equal to "str",
                return instead the string that would have been written to the file.
            thermal_events (list): List of ThermalEvent objects to be written.
            use_id_as_key (bool): Indicates whether to use a simple counter or
                the id of each event as keys for the dictionnary. Defaults to False.

        Returns:
            None
        """
        from .schemas import ThermalEventSchema

        if not isinstance(thermal_events, list):
            thermal_events = [thermal_events]

        out = {}
        for ind, event in enumerate(thermal_events):
            if use_id_as_key:
                ind = event.id

            make_transient(event)
            [make_transient(x) for x in event.instances]
            out[ind] = ThermalEventSchema().dump(event)

        if path_to_file == "str":
            return json.dumps(out)

        with open(path_to_file, "w", encoding="utf-8") as file:
            json.dump(out, file, ensure_ascii=False, separators=(",", ":"))
