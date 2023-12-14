from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested, RelatedList
from marshmallow import fields
from .thermal_event_instance import ThermalEventInstance
from .thermal_event import ThermalEvent
from .strike_line_descriptor import StrikeLineDescriptor


class ThermalEventInstanceSchema(SQLAlchemyAutoSchema):
    """Schema for the ThermalEventInstance model."""

    class Meta:
        model = ThermalEventInstance
        include_relationships = True
        include_fk = True
        load_instance = True
        transient = True

    _confidence = fields.Float(data_key="confidence")


class ThermalEventSchema(SQLAlchemyAutoSchema):
    """Schema for the ThermalEvent model."""

    instances = RelatedList(
        Nested(ThermalEventInstanceSchema), data_key="thermal_events_instances"
    )

    class Meta:
        model = ThermalEvent
        include_relationships = True
        include_fk = True
        load_instance = True
        transient = True


class StrikeLineDescriptorSchema(SQLAlchemyAutoSchema):
    """Schema for the StrikeLineDescriptor model."""

    class Meta:
        model = StrikeLineDescriptor
        include_relationships = True
        include_fk = True
        load_instance = True
        transient = True
