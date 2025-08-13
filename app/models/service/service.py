from enum import Enum
from typing import List, Literal, Optional

from pydantic import Field

from app.models._admin import BaseSchema


class PriceType(str, Enum):
    FIXED = "Fixed"
    FREE = "Free"


class ServiceBase(BaseSchema):
    name: str = Field(..., max_length=255)
    category_id: int = Field(..., gt=0, alias="categoryId")
    description: Optional[str] = None
    duration: int = Field(..., gt=0)  # minutes

    # Pricing
    price_type: PriceType = Field(..., alias="priceType")
    credit_cost: int = Field(..., ge=0, alias="creditCost")
    cash_price: int = Field(..., ge=0, alias="cashPrice")

    # Others
    active: bool
    online_bookings: bool = Field(..., alias="onlineBookings")
    comissions: bool


""" 
    PUT 
    1) /api/services/:service_id?
"""


class ServiceUpsert(ServiceBase):
    # Locations
    locations: List[Literal[1, 2]] = Field(..., min_length=1)  # outlet_id


"""
    GET 
    1) /api/services
    2) /api/services/:service_id
"""


class ServiceWithLocationsResponse(ServiceUpsert):
    id: int = Field(..., gt=0)


"""
    GET
    1) /api/services/outlet/:outlet_id
"""


class ServiceWithoutLocationsResponse(ServiceBase):
    id: int = Field(..., gt=0)
