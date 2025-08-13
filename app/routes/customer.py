import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.models.customer import CustomerCreate, CustomerResponse
from db.supabase import supabase

logger = logging.getLogger(__name__)

customer_router = APIRouter(
    prefix="/api/customers",
    tags=["customers"],
)


@customer_router.get("", response_model=List[CustomerResponse])
def get_all_customers():
    try:
        customers = supabase.from_("customers").select("*").execute()
        return customers.data
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get all customers")


# Search over first name and last name
@customer_router.get("/search", response_model=List[CustomerResponse])
def search_customers(search_query: str | None = None):
    try:
        # No query or all whitespace query
        if not search_query or not search_query.strip():
            customers = supabase.from_("customers").select("*").execute()
            return customers.data

        lower_query = search_query.lower()
        customers = (
            supabase.from_("customers")
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
def get_customer(customer_id: int):
    try:
        target_customer = (
            supabase.from_("customers")
            .select("*")
            .eq("id", customer_id)
            .limit(1)
            .execute()
        )

        if not target_customer.data:
            raise HTTPException(status_code=404, detail="Customer not found")

        return target_customer.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get single customer")


@customer_router.post("", status_code=201)
def create_customer(customer_data: CustomerCreate):
    try:
        create_details = customer_data.model_dump(mode="json")
        supabase.from_("customers").insert(create_details).execute()
        return "Customer successfully created"

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to create customer")
