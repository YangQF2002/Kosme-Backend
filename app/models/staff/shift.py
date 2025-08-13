from datetime import date, time

from pydantic import Field

from app.models._admin import BaseSchema

"""
    PUT
    1) /api/shifts/:shift_id? 
"""


class ShiftUpsert(BaseSchema):
    staff_id: int = Field(..., gt=0, alias="staffId")

    start_time: time = Field(..., alias="startTime")
    end_time: time = Field(..., alias="endTime")

    shift_date: date = Field(..., alias="shiftDate")


"""
    GET
    1) /api/shifts/staff/:staff_id/:date
    2) /api/shifts/outlet/:outlet_id/:date
  
"""


class ShiftResponse(ShiftUpsert):
    id: int = Field(..., gt=0)
