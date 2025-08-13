from datetime import datetime
from typing import List, Literal, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from utils.general import has_overlap

from app.models.appointment.appointment import AppointmentResponse
from app.models.customer import CustomerResponse
from app.models.staff.staff import StaffBase
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


def _get_appointments_by_customer_and_date(
    customer_id: int, date: str
) -> List[AppointmentResponse]:
    start_of_day = f"{date}T00:00:00"
    end_of_day = f"{date}T23:59:59"

    # Query appointments for this date
    appointments = (
        supabase.from_("appointments")
        .select("*")
        .eq("customer_id", customer_id)
        .gte("start_time", start_of_day)
        .lte("start_time", end_of_day)
        .execute()
    ).data

    return appointments


CalendarForms = Literal["Appointment", "Blocked time", "Time off", "Shift"]


class HasOverlappingStaffAppointmentsArgs(BaseModel):
    # Only required when appointment checking against itself
    appointment_id: Optional[int] = None
    staff_id: int
    staff: StaffBase
    date_string: str  # YYYY-MM-DD
    target_start_time: str  # HH:mm
    target_end_time: str  # HH:mm
    type: CalendarForms


def _has_overlapping_staff_appointments(
    args: HasOverlappingStaffAppointmentsArgs,
) -> None:
    # Get apointments for the staff on the given date
    appointments = _get_appointments_by_staff_and_date(args.staff_id, args.date_string)

    # Filter out the current appointment if appointment_id is provided
    staff_appointments = [
        appt
        for appt in appointments
        if not args.appointment_id or appt["id"] != args.appointment_id
    ]

    # Check for overlaps
    has_overlapping = any(
        has_overlap(
            datetime.fromisoformat(appt["start_time"]).strftime("%H:%M"),
            datetime.fromisoformat(appt["end_time"]).strftime("%H:%M"),
            args.target_start_time,
            args.target_end_time,
        )
        for appt in staff_appointments
    )

    if has_overlapping:
        raise HTTPException(
            status_code=400,
            detail=f"{args.type} {args.target_start_time}-{args.target_end_time} "
            f"by staff {args.staff.first_name} has clashing appointments.",
        )


class HasOverlappingCustomerAppointmentsArgs(BaseModel):
    # This is SOLELY USED by appointment to check against others
    appointment_id: int
    customer_id: int
    customer: CustomerResponse
    date_string: str  # YYYY-MM-DD
    target_start_time: str  # HH:mm
    target_end_time: str  # HH:mm


def _has_overlapping_customer_appointments(
    args: HasOverlappingCustomerAppointmentsArgs,
) -> None:
    # Get all appointments for the customer on the given date
    appointments = _get_appointments_by_customer_and_date(
        args.customer_id, args.date_string
    )

    # Filter for customer appointments, excluding current appointment
    customer_appointments = [
        appt
        for appt in appointments
        if appt["customer_id"] == args.customer_id and appt["id"] != args.appointment_id
    ]

    # Check for overlaps
    has_overlapping = any(
        has_overlap(
            datetime.fromisoformat(appt["start_time"]).strftime("%H:%M"),
            datetime.fromisoformat(appt["end_time"]).strftime("%H:%M"),
            args.target_start_time,
            args.target_end_time,
        )
        for appt in customer_appointments
    )

    if has_overlapping:
        raise HTTPException(
            status_code=400,
            detail=f"Appointment {args.target_start_time}-{args.target_end_time} "
            f"by customer {args.customer.first_name} has clashing appointments.",
        )
