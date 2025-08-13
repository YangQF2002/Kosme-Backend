from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from pydantic import Field

from app.models._admin import BaseSchema


class TimeOffType(str, Enum):
    ANNUAL_LEAVE = "Annual leave"
    SICK_LEAVE = "Sick leave"
    PERSONAL = "Personal"
    OTHER = "Other"


class FrequencyType(str, Enum):
    NONE = "None"
    REPEAT = "Repeat"


"""
    PUT
    1) /api/time-offs/:time_off_id?
"""


class TimeOffUpsert(BaseSchema):
    staff_id: int = Field(..., gt=0, alias="staffId")
    duration: float

    type: TimeOffType
    start_date: date = Field(..., alias="startDate")
    start_time: time = Field(..., alias="startTime")
    end_time: time = Field(..., alias="endTime")

    frequency: FrequencyType
    ends_date: Optional[date] = Field(None, alias="endsDate")

    description: Optional[str] = Field(None, max_length=255)
    approved: bool = False


"""
    GET
    1) /api/time-offs/:time_off_id
    2) /api/time-offs/outlet/:outlet_id/:date
"""


class TimeOffResponse(TimeOffUpsert):
    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime
