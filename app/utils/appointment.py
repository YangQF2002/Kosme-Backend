from typing import List

from app.models.appointment.appointment import AppointmentResponse
from db.supabase import supabase

""" 
    [Date format]
    1) Dates are expected to be in YYYY-MM-DD format
"""


def _get_appointments_by_staff_and_date(
    staff_id: int, date: str
) -> List[AppointmentResponse]:
    start_of_day = f"{date}T00:00:00"
    end_of_day = f"{date}T23:59:59"

    # Query appointments for this date
    appointments = (
        supabase.from_("appointments")
        .select("*")
        .eq("staff_id", staff_id)
        .gte("start_time", start_of_day)
        .lte("start_time", end_of_day)
        .execute()
    ).data

    return appointments
