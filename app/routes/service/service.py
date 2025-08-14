import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models.service.service import (
    ServiceUpsert,
    ServiceWithLocationsResponse,
    ServiceWithoutLocationsResponse,
)
from db.supabase import supabase

logger = logging.getLogger(__name__)

service_router = APIRouter(
    prefix="/api/services",
    tags=["services"],
)


@service_router.get("", response_model=List[ServiceWithLocationsResponse])
def get_all_services():
    try:
        # LEFT JOIN with service_outlet FK table
        # GROUP BY service_id, then grab all the outlet_ids
        # Each row is annotated with "service_outlet": [{"outlet_id": x}, ...]
        response = (
            supabase.from_("services").select("*, service_outlet(outlet_id)").execute()
        )

        # Process the response
        services = []
        for service in response.data:
            # Remove the annotation, replace with locations
            service["locations"] = [
                item["outlet_id"] for item in service.pop("service_outlet", [])
            ]
            services.append(service)

        return services

    except Exception as e:
        logger.error(f"Error fetching services: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get all services")


@service_router.get(
    "/outlet/{outlet_id}", response_model=List[ServiceWithoutLocationsResponse]
)
def get_all_services_from_outlet(outlet_id: int):
    if outlet_id not in [1, 2]:
        raise HTTPException(status_code=400, detail="Invalid outlet id")

    try:
        response = (
            supabase.from_("service_outlet")
            .select("service_id, services(*)")
            .eq("outlet_id", outlet_id)
            .execute()
        )

        # Extract service data from the joined response
        services = [item["services"] for item in response.data]
        return services

    except Exception as e:
        logger.error(
            f"Error fetching services from outlet {outlet_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to get services from outlet"
        )


@service_router.get("/{service_id}", response_model=ServiceWithLocationsResponse)
def get_single_service(service_id: int):
    try:
        response = (
            supabase.from_("services")
            .select("*, service_outlet(outlet_id)")
            .eq("id", service_id)
            .single()
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Service not found")

        # Process the response
        target_service = response.data
        target_service["locations"] = [
            item["outlet_id"] for item in target_service.pop("service_outlet", [])
        ]

        return target_service

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching service {service_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get single service")


# Create
@service_router.put("", status_code=201)
def create_service(service_data: ServiceUpsert):
    return _upsert_service(None, service_data)


# Update
@service_router.put("/{service_id}")
def update_service(service_id: int, service_data: ServiceUpsert):
    return _upsert_service(service_id, service_data)


# Helper to handle both
def _upsert_service(service_id: Optional[int], service_data: ServiceUpsert):
    # Construct payload
    payload = service_data.model_dump(exclude_unset=True, by_alias=False)

    if service_id is not None:
        payload["id"] = service_id

    locations: List[int] = payload.pop("locations")

    try:
        response = supabase.from_("services").upsert(payload).execute()

        if service_id and not response.data:
            raise HTTPException(
                status_code=404, detail="Service to be updated not found"
            )

        # Clear existing links (if any)
        if service_id is not None:
            supabase.from_("service_outlet").delete().eq(
                "service_id", service_id
            ).execute()

        # Update the service-outlet link table
        target_service = response.data[0]
        target_id: int = target_service["id"]

        for outlet_id in locations:
            supabase.from_("service_outlet").insert(
                {"service_id": target_id, "outlet_id": outlet_id}
            ).execute()

        return (
            "Service successfully updated"
            if service_id
            else "Service successfully created"
        )

    except Exception as e:
        logger.error(f"Error upserting service: {str(e)}", exc_info=True)

        # If the error is something the user can ACT on
        # Then reveal it to them
        if "services_name_key" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid name, '{service_data.name}' already exists.",
            )

        if "services_category_id_fkey" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category id, '{service_data.category_id}' does not exist.",
            )

        action = "update" if service_id else "create"
        raise HTTPException(
            status_code=500, detail=f"Failed to {action} single service"
        )


@service_router.delete("/{service_id}")
def delete_service(service_id: int):
    try:
        response = supabase.from_("services").delete().eq("id", service_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Service not found")

        return "Service successfully deleted"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service {service_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete single service")
