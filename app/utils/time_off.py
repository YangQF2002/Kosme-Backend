from typing import List

from app.models.staff.time_off import TimeOffResponse
from db.supabase import supabase

""" 
    [Date format]
    1) Dates are expected to be in YYYY-MM-DD format
"""


def _get_time_offs_by_staff_and_date(staff_id: int, date: str) -> List[TimeOffResponse]:
    all_time_offs: List[TimeOffResponse] = (
        supabase.from_("time_offs").select("*").eq("staff_id", staff_id).execute()
    ).data

    # Filter based on frequency type
    valid_time_offs = []
    for time_off in all_time_offs:
        if time_off["frequency"] == "none":
            # Single day - check exact date match
            if time_off["start_date"] == date:
                valid_time_offs.append(time_off)
        else:
            # Recurring - check if date is in range
            if time_off["start_date"] <= date <= time_off["ends_date"]:
                valid_time_offs.append(time_off)

    return valid_time_offs
