from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested, RelatedList
from marshmallow import fields
from .hot_spot import HotSpot
from .thermal_event import ThermalEvent


class HotSpotSchema(SQLAlchemyAutoSchema):
    """Schema for the HotSpot model."""

    class Meta:
        model = HotSpot
        include_relationships = True
        include_fk = True
        load_instance = True
        transient = True

    _confidence = fields.Float(data_key="confidence")


class ThermalEventSchema(SQLAlchemyAutoSchema):
    """Schema for the ThermalEvent model."""

    hot_spots = RelatedList(Nested(HotSpotSchema))

    class Meta:
        model = ThermalEvent
        include_relationships = True
        include_fk = True
        load_instance = True
        transient = True
