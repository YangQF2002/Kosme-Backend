from typing import Literal

from pydantic import BaseModel

from app.constants import (
    WEEKDAY_CLOSING,
    WEEKDAY_OPENING,
    WEEKEND_CLOSING,
    WEEKEND_OPENING,
)
from app.models.staff.staff import StaffBase
from db.supabase import supabase

CalendarFormsWithoutShift = Literal["Appointment", "Blocked time", "Time off"]


class IsWithinStaffShiftArgs(BaseModel):
    staff_id: int
    staff: StaffBase
    date_string: str  # YYYY-MM-DD
    target_start_time: str  # HH:mm
    target_end_time: str  # HH:mm
    is_weekday: bool
    type: CalendarFormsWithoutShift


def _is_within_staff_shift(args: IsWithinStaffShiftArgs) -> None:
    # Get staff shift for the specific date
    staff_shift_response = (
        supabase.from_("shifts")
        .select("*")
        .eq("staff_id", args.staff_id)
        .eq("shift_date", args.date_string)
        .maybe_single()  # At most one row
        .execute()
    )
    staff_shift = staff_shift_response.data

    # Determine shift hours (use defaults if no shift found)
    if staff_shift:
        shift_start_time = staff_shift.get("start_time")
        shift_end_time = staff_shift.get("end_time")
    else:
        shift_start_time = WEEKDAY_OPENING if args.is_weekday else WEEKEND_OPENING
        shift_end_time = WEEKDAY_CLOSING if args.is_weekday else WEEKEND_CLOSING

    # Check if target times are within shift hours
    is_within_hours = (
        args.target_end_time <= shift_end_time
        and args.target_start_time >= shift_start_time
    )

    if not is_within_hours:
        raise ValueError(
            f"{args.type} {args.target_start_time}-{args.target_end_time} "
            f"by staff {args.staff.first_name} is outside shift hours."
        )
