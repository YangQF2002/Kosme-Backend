from typing import Optional

from pydantic import Field

from app.models._admin import BaseSchema

"""
    Currently, the two (active) Kosme outlets are hardcoded
    ID 1 -> Orchard 
    ID 2 -> PLQ 
"""


"""
    GET
    1) /api/outlets
"""


class OutletResponse(BaseSchema):
    id: int = Field(..., gt=0)
    name: str
    address: str
    phone: Optional[str] = None
    active: bool
