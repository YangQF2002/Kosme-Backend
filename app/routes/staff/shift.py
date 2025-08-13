import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models.staff.shift import ShiftResponse, ShiftUpsert
from app.utils.appointment import _get_appointments_by_staff_and_date
from app.utils.blocked_time import _get_blocked_times_by_staff_and_date
from app.utils.time_off import _get_time_offs_by_staff_and_date
from db.supabase import supabase

logger = logging.getLogger(__name__)

shift_router = APIRouter(
    prefix="/api/shifts",
    tags=["shifts"],
)


""" 
    [Date format]
    1) Dates are expected to be in YYYY-MM-DD format
"""


@shift_router.get("/staff/{staff_id}/{date}", response_model=ShiftResponse)
def get_shifts_by_staff_and_date(staff_id: int, date: str):
    try:
        shift = (
            supabase.from_("shifts")
            .select("*")
            .eq("staff_id", staff_id)
            .eq("shift_date", date)
            .limit(1)
            .execute()
        )

        if not shift.data:
            raise HTTPException(status_code=404, detail="Staff shift not found")

        return shift.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching shift for staff {staff_id} over date {date}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to get staff shift")


@shift_router.get("/outlet/{outlet_id}/{date}", response_model=List[ShiftResponse])
def get_shifts_by_outlet_and_date(outlet_id: int, date: str):
    if outlet_id not in [1, 2]:
        raise HTTPException(status_code=400, detail="Invalid outlet id")

    try:
        response = (
            supabase.from_("staff_outlet")
            .select("staff_id, shifts(*)")
            .eq("outlet_id", outlet_id)
            .eq("shifts.shift_date", date)
            .execute()
        )

        # Extract shifts from the joined response
        shifts = []
        for item in response.data:
            if item.get("shifts"):
                shifts.extend(item["shifts"])

        return shifts

    except Exception as e:
        logger.error(
            f"Error fetching shifts for outlet {outlet_id} over date {date}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to get outlet shifts")


# Create
@shift_router.put("", status_code=201)
def create_shift(shift_data: ShiftUpsert):
    return _upsert_shift(None, shift_data)


# Update
@shift_router.put("/{shift_id}")
def update_shift(shift_id: int, shift_data: ShiftUpsert):
    return _upsert_shift(shift_id, shift_data)


# Helper to handle both
def _upsert_shift(shift_id: Optional[int], shift_data: ShiftUpsert):
    # Construct payload
    payload = shift_data.model_dump(exclude_unset=True, by_alias=False)

    if shift_id is not None:
        payload["id"] = shift_id

    # Extract important info
    shift_date = shift_data.shift_date
    shift_staff_id = shift_data.staff_id

    shift_start_time = shift_data.start_time
    shift_end_time = shift_data.end_time

    try:
        # [CROSS CHECK 1]: Shift does not cause any staff appointments to fall out of range
        staff_appointments = _get_appointments_by_staff_and_date(shift_date)

        is_all_within_range = all(
            datetime.fromisoformat(appt["start_time"]).strftime("%H:%M")
            >= shift_start_time
            and datetime.fromisoformat(appt["end_time"]).strftime("%H:%M")
            <= shift_end_time
            for appt in staff_appointments
        )

        if not is_all_within_range:
            raise HTTPException(
                status_code=400, detail="Existing appointments fall outside new hours"
            )

        # [CROSS CHECK 2]: Shift does not cause any staff time offs to fall out of range
        staff_time_offs = _get_time_offs_by_staff_and_date(shift_staff_id, shift_date)

        is_all_within_range = all(
            time_off["start_time"] >= shift_start_time
            and time_off["end_time"] <= shift_end_time
            for time_off in staff_time_offs
        )

        if not is_all_within_range:
            raise HTTPException(
                status_code=400, detail="Existing time offs fall outside new hours"
            )

        # [CROSS CHECK 3]: Shift does not cause any staff blocked time to fall out of range
        staff_blocked_times = _get_blocked_times_by_staff_and_date(
            shift_staff_id, shift_date
        )

        is_all_within_range = all(
            blocked_time["from_time"] >= shift_start_time
            and blocked_time["to_time"] <= shift_end_time
            for blocked_time in staff_blocked_times
        )

        if not is_all_within_range:
            raise HTTPException(
                status_code=400, detail="Existing blocked times fall outside new hours"
            )

        # After passing the cross checks
        # Then only do we perform the upsert
        response = supabase.from_("shifts").upsert(payload).execute()

        if shift_id and not response.data:
            raise HTTPException(status_code=404, detail="Shift to be updated not found")

        return (
            "Shift successfully updated" if shift_id else "Shift successfully created"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting shift: {str(e)}", exc_info=True)

        action = "update" if shift_id else "create"
        raise HTTPException(status_code=500, detail=f"Failed to ${action} single shift")
