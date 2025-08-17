import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from supabase import AClient

from app.models.appointment.appointment import AppointmentResponse
from app.models.customer import CustomerCreate, CustomerResponse
from db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

customer_router = APIRouter(
    prefix="/api/customers",
    tags=["customers"],
)


@customer_router.get("", response_model=List[CustomerResponse])
async def get_all_customers(supabase: AClient = Depends(get_supabase_client)):
    try:
        customers = await supabase.from_("customers").select("*").execute()
        return customers.data
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get all customers")


# Search over first name and last name
@customer_router.get("/search", response_model=List[CustomerResponse])
async def search_customers(
    search_query: str | None = None, supabase: AClient = Depends(get_supabase_client)
):
    try:
        # No query or all whitespace query
        if not search_query or not search_query.strip():
            customers = await supabase.from_("customers").select("*").execute()
            return customers.data

        lower_query = search_query.lower()
        customers = (
            await supabase.from_("customers")
            .select("*")
            .or_(f"first_name.ilike.%{lower_query}%,last_name.ilike.%{lower_query}%")
            .execute()
        )

        return customers.data
    except Exception as e:
        logger.error(
            f"Error searching customers over query {search_query}': {str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to search for customers")


@customer_router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, supabase: AClient = Depends(get_supabase_client)):
    try:
        target_customer = (
            await supabase.from_("customers")
            .select("*")
            .eq("id", customer_id)
            .single()
            .execute()
        )

        if not target_customer.data:
            raise HTTPException(status_code=404, detail="Customer not found")

        return target_customer.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get single customer")


@customer_router.get(
    "/{customer_id}/appointments", response_model=List[AppointmentResponse]
)
async def get_customer_appointments(
    customer_id: int, supabase: AClient = Depends(get_supabase_client)
):
    try:
        target_customer = (
            await supabase.from_("customers")
            .select("*")
            .eq("id", customer_id)
            .single()
            .execute()
        )

        if not target_customer.data:
            raise HTTPException(status_code=404, detail="Customer not found")

        target_customer_appointments = (
            await supabase.from_("appointments")
            .select("*")
            .eq("customer_id", customer_id)
            .execute()
        )

        return target_customer_appointments.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching customer {customer_id} appointments: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to fetch appointments for customer"
        )


@customer_router.post("", status_code=201)
async def create_customer(
    customer_data: CustomerCreate, supabase: AClient = Depends(get_supabase_client)
):
    try:
        create_details = customer_data.model_dump(mode="json")
        await supabase.from_("customers").insert(create_details).execute()
        return "Customer successfully created"

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to create customer")
