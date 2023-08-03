from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested, RelatedList
from marshmallow import fields
from .thermal_event_instance import ThermalEventInstance
from .thermal_event import ThermalEvent


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

    hot_spots = RelatedList(Nested(ThermalEventInstanceSchema))

    class Meta:
        model = ThermalEvent
        include_relationships = True
        include_fk = True
        load_instance = True
        transient = True
