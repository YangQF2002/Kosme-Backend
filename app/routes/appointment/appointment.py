import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from supabase import AClient

from app.models.appointment.appointment import (
    AppointmentResponse,
    AppointmentStatus,
    AppointmentUpsert,
)
from app.models.appointment.credit_transaction import CreditTransactionCreate
from app.models.customer import CustomerResponse
from app.models.service.service import (
    ServiceWithoutLocationsResponse,
)
from app.utils.appointment import (
    HasOverlappingCustomerAppointmentsArgs,
    HasOverlappingStaffAppointmentsArgs,
    _get_appointments_by_outlet_and_date,
    _has_overlapping_customer_appointments,
    _has_overlapping_staff_appointments,
)
from app.utils.blocked_time import (
    HasOverlappingBlockedTimeArgs,
    _has_overlapping_blocked_times,
)
from app.utils.shift import IsWithinStaffShiftArgs, _is_within_staff_shift
from app.utils.time_off import HasOverlappingTimeOffsArgs, _has_overlapping_time_offs
from db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

appointment_router = APIRouter(
    prefix="/api/appointments",
    tags=["appointments"],
)


"""
    [FastAPI + Supbase Integration]

    1) I'll just write this once (@current maintainer)
    2) FastAPI, an async framework, requires supabase client as a dependency injection
    3) This prevents weird timeouts and disconnects

"""


@appointment_router.get("", response_model=List[AppointmentResponse])
async def get_all_appointments(supabase: AClient = Depends(get_supabase_client)):
    try:
        appointments = await supabase.from_("appointments").select("*").execute()
        return appointments.data

    except Exception as e:
        logger.error(f"Error fetching appointments: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get all appointments")


@appointment_router.get(
    "/outlet/{outlet_id}/{date}", response_model=List[AppointmentResponse]
)
async def get_appointments_by_outlet_and_date(
    outlet_id: int, date: str, supabase: AClient = Depends(get_supabase_client)
):
    if outlet_id not in [1, 2]:
        raise HTTPException(status_code=400, detail="Invalid outlet id")

    try:
        appointments = await _get_appointments_by_outlet_and_date(
            outlet_id, date, supabase
        )
        return appointments

    except Exception as e:
        logger.error(f"Error fetching outlet appointments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get appointments for the outlet"
        )


@appointment_router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_single_appointment(
    appointment_id: int, supabase: AClient = Depends(get_supabase_client)
):
    try:
        appointment = (
            await supabase.from_("appointments")
            .select("*")
            .eq("id", appointment_id)
            .single()
            .execute()
        )

        if not appointment.data:
            raise HTTPException(status_code=404, detail="Appointment not found")

        return appointment.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching appointment {appointment_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get appointment")


# Update status
@appointment_router.put("/status/{appointment_id}")
async def update_appointment_status(
    appointment_id: int,
    status: AppointmentStatus,
    supabase: AClient = Depends(get_supabase_client),
):
    try:
        response = (
            await supabase.from_("appointments")
            .update({"status": status})
            .eq("id", appointment_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Appointment not found")

        return "Appointment status successfully updated"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating appointment {appointment_id} status: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to update appointment status"
        )


# Create
@appointment_router.put("", status_code=201)
async def create_appointment(
    appointment_data: AppointmentUpsert,
    supabase: AClient = Depends(get_supabase_client),
):
    return await _upsert_appointment(None, appointment_data, supabase)


# Update
@appointment_router.put("/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpsert,
    supabase: AClient = Depends(get_supabase_client),
):
    return await _upsert_appointment(appointment_id, appointment_data, supabase)


# Helper to handle both
async def _upsert_appointment(
    appointment_id: Optional[int],
    appointment_data: AppointmentUpsert,
    supabase: AClient,
):
    # Construct payload
    payload = appointment_data.model_dump(exclude_unset=True, by_alias=False)

    if appointment_id is not None:
        payload["id"] = appointment_id

    # Extract important info
    staff_id = appointment_data.staff_id

    staff_response = (
        await supabase.from_("staffs").select("*").eq("id", staff_id).single().execute()
    )

    staff = staff_response.data
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    start_time = appointment_data.start_time
    end_time = appointment_data.end_time

    date_string = start_time.date().isoformat()  # YYYY-MM-DD
    is_weekday = 0 <= start_time.weekday() <= 4

    appointment_start_time = start_time.strftime("%H:%M")
    appointment_end_time = end_time.strftime("%H:%M")

    # Extra info for cross check 5
    customer_id = appointment_data.customer_id
    customer: CustomerResponse = (
        await supabase.from_("customers")
        .select("*")
        .eq("id", customer_id)
        .single()
        .execute()
    ).data

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    """ 
        [Cross check error handling]
        1) If cross check fails, it raises a HTTPException
        2) Hence, we just propogate the HTTPException back up 
    """

    try:
        # [CROSS CHECK 1]: Appointment falls within staff shift hours
        args = IsWithinStaffShiftArgs(
            staff_id=staff_id,
            staff=staff,
            date_string=date_string,
            target_start_time=appointment_start_time,
            target_end_time=appointment_end_time,
            is_weekday=is_weekday,
            type="Appointment",
        )

        await _is_within_staff_shift(args, supabase)

        # [CROSS CHECK 2]: Appointment does not clash with time-offs
        args = HasOverlappingTimeOffsArgs(
            staff_id=staff_id,
            staff=staff,
            date_string=date_string,
            target_start_time=appointment_start_time,
            target_end_time=appointment_end_time,
            type="Appointment",
        )

        await _has_overlapping_time_offs(args, supabase)

        # [CROSS CHECK 3]: Appointment does not clash with blocked-times
        args = HasOverlappingBlockedTimeArgs(
            staff_id=staff_id,
            staff=staff,
            date_string=date_string,
            target_start_time=appointment_start_time,
            target_end_time=appointment_end_time,
            type="Appointment",
        )

        await _has_overlapping_blocked_times(args, supabase)

        # [CROSS CHECK 4]: Appointment does not clash with other staff appointments
        args = HasOverlappingStaffAppointmentsArgs(
            staff_id=staff_id,
            staff=staff,
            date_string=date_string,
            target_start_time=appointment_start_time,
            target_end_time=appointment_end_time,
            type="Appointment",
            appointment_id=appointment_id,  # Exclude itself
        )

        await _has_overlapping_staff_appointments(args, supabase)

        # [CROSS CHECK 5]: Appointment does not clash with other customer appointments
        args = HasOverlappingCustomerAppointmentsArgs(
            appointment_id=appointment_id,  # Exclude itself
            customer_id=customer_id,
            customer=customer,
            date_string=date_string,
            target_start_time=appointment_start_time,
            target_end_time=appointment_end_time,
        )

        await _has_overlapping_customer_appointments(args, supabase)

        # After passing the cross checks
        # Then only do we perform the upsert

        # Appointment start and end needs to be converted to ISO string
        # To be JSON-serializable
        payload["start_time"] = payload["start_time"].now().isoformat()
        payload["end_time"] = payload["end_time"].now().isoformat()

        response = await supabase.from_("appointments").upsert(payload).execute()

        if appointment_id and not response.data:
            raise HTTPException(
                status_code=404, detail="Appointment to be updated not found"
            )

        # For both create and update intentions
        target_appointment_id = response.data[0]["id"]

        # Handle credit payment
        payment_method = appointment_data.payment_method

        if payment_method == "credits":
            # First, establish some basic info
            service_id = appointment_data.service_id
            service: ServiceWithoutLocationsResponse = (
                await supabase.from_("service")
                .select("*")
                .eq("id", service_id)
                .single()
                .execute()
            ).data

            if not service:
                raise HTTPException(status_code=404, detail="Service not found")

            current_cost = service.credit_cost
            previous_credits_paid = appointment_data.credits_paid or 0
            credit_diff = current_cost - previous_credits_paid

            # Need to charge more
            if credit_diff > 0:
                # Insufficient funds
                if customer.credit_balance < credit_diff:
                    raise HTTPException(
                        status_code=400,
                        detail="Insufficient credits for updated appointment"
                        if appointment_id
                        else "Insufficient credits for new appointment",
                    )

                # Deduct credits
                new_balance = customer.credit_balance - credit_diff
                await (
                    supabase.from_("customers")
                    .update({"credit_balance": new_balance})
                    .eq("id", customer.id)
                    .execute()
                )

                # Record deduction
                transaction_info = {
                    "customer_id": customer.id,
                    "appointment_id": target_appointment_id,
                    "amount": -credit_diff,  # Negative for credits used
                    "type": "usage",
                    "description": f"Extra {credit_diff} credits used for updated appointment"
                    if appointment_id
                    else f"Used {current_cost} credits for new appointment",
                }
                await (
                    supabase.from_("credit_transactions")
                    .insert(transaction_info)
                    .execute()
                )

            # Refund surplus credits
            # ONLY possible on UPDATE
            elif credit_diff < 0:
                refund_amount = abs(credit_diff)
                new_balance = customer.credit_balance + refund_amount

                # Perform refund
                await (
                    supabase.from_("customers")
                    .update({"credit_balance": new_balance})
                    .eq("id", customer.id)
                    .execute()
                )

                # Record refund
                transaction_info = {
                    "customer_id": customer.id,
                    "appointment_id": appointment_id,
                    "amount": refund_amount,  # Positive for credits added
                    "type": "refund",
                    "description": f"Refunded {refund_amount} credits after service change",
                }
                await (
                    supabase.from_("credit_transactions")
                    .insert(transaction_info)
                    .execute()
                )

            # Safety, may not necessarily need
            await (
                supabase.from_("appointments")
                .update({"credits_paid": current_cost, "payment_status": "Paid"})
                .eq("id", target_appointment_id)
                .execute()
            )

        else:
            # Handle refund if switching from credits to cash/card
            # ONLY possible on UPDATE
            if appointment_id and appointment_data.credits_paid > 0:
                previous_credits_paid = appointment_data.credits_paid
                new_balance = customer.credit_balance + previous_credits_paid

                # Perform refund
                await (
                    supabase.from_("customers")
                    .update({"credit_balance": new_balance})
                    .eq("id", customer.id)
                    .execute()
                )

                # Record refund
                transaction_info = {
                    "customer_id": customer.id,
                    "appointment_id": appointment_id,
                    "amount": previous_credits_paid,
                    "type": "refund",
                    "description": f"Refunded {previous_credits_paid} credits after switching to card/cash payment",
                }
                await (
                    supabase.from_("credit_transactions")
                    .insert(transaction_info)
                    .execute()
                )

            # Safety, may not necessarily need
            await (
                supabase.from_("appointments")
                .update({"credits_paid": 0, "payment_status": "Pending"})
                .eq("id", target_appointment_id)
                .execute()
            )

        return (
            "Appointment successfully updated"
            if appointment_id
            else "Appointment successfully created"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upserting appointment: {str(e)}", exc_info=True)

        action = "update" if appointment_id else "create"
        raise HTTPException(
            status_code=500, detail=f"Failed to {action} single appointment"
        )


@appointment_router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int, supabase: AClient = Depends(get_supabase_client)
):
    try:
        response = (
            await supabase.from_("appointments")
            .delete()
            .eq("id", appointment_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Appointment not found")

        # If customer paid by credits
        # Refund the credits
        deleted_appointment: AppointmentResponse = response.data[0]
        payment_method = deleted_appointment.payment_method
        credits_paid = deleted_appointment.credits_paid

        customer_id = deleted_appointment.customer_id
        customer: CustomerResponse = (
            await supabase.from_("customers")
            .select("*")
            .eq("id", customer_id)
            .single()
            .execute()
        ).data

        if payment_method == "Credits" and credits_paid > 0:
            # Perform the refund
            new_credit_balance = customer.credit_balance + credits_paid

            await (
                supabase.from_("customers")
                .update({"credit_balance": new_credit_balance})
                .eq("id", customer_id)
                .execute()
            )

            # Record refund down via a credit transaction
            transaction_info: CreditTransactionCreate = {
                "customer_id": customer_id,
                "appointment_id": appointment_id,
                "amount": credits_paid,
                "type": "refund",
                "description": f"Refunded {credits_paid} credits for cancelled appointment",
            }
            await (
                supabase.from_("credit_transactions").insert(transaction_info).execute()
            )

        return "Appointment successfully deleted"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting appointment {appointment_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to delete single appointment"
        )
