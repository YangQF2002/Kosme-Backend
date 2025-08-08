from pydantic import EmailStr, Field

from app.models._admin import BaseSchema

"""
    PUT
    1) /api/staff/:id?
"""


class StaffUpsert(BaseSchema):
    first_name: str = Field(..., max_length=100, alias="firstName")
    last_name: str = Field(..., max_length=100, alias="lastName")
    email: EmailStr = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    role: str = Field(..., max_length=100)

    # Filter fields
    bookable: bool
    active: bool


"""
    GET
    1) /api/staff
    2) /api/staff/:id
    3) /api/staff/outlet/:outledId
"""


class StaffResponse(StaffUpsert):
    id: int = Field(..., gt=0)
