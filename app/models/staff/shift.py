from datetime import date, time

from pydantic import Field

from app.models._admin import BaseSchema

"""
    PUT
    1) /api/shifts/:staffId/:date
"""


class ShiftUpsert(BaseSchema):
    staff_id: int = Field(..., gt=0, alias="staffId")
    start_time: time = Field(..., alias="startTime")
    end_time: time = Field(..., alias="endTime")

    shift_date: date = Field(..., alias="shiftDate")


"""
    GET
    1) /api/shifts/:staffId/:date
    2) /api/shifts/staffs/:outletId/:date
  
"""


class ShiftResponse(ShiftUpsert):
    id: int = Field(..., gt=0)
