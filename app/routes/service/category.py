import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models.service.category import (
    ServiceCategoryResponse,
    ServiceCategoryUpsert,
    ServiceCategoryWithCountResponse,
)
from db.supabase import supabase

logger = logging.getLogger(__name__)

category_router = APIRouter(
    prefix="/api/service-categories",
    tags=["service-categories"],
)


@category_router.get("", response_model=List[ServiceCategoryWithCountResponse])
def get_all_categories():
    try:
        # LEFT JOIN with services FK table
        # GROUP BY service_category_id, then COUNT over each group
        # Each row is annotated with "services": [{"count": x}]
        response = (
            supabase.from_("service_categories").select("*, services(count)").execute()
        )

        # Process the response
        categories = []
        for category in response.data:
            # Extract the count from the nested structure
            service_count = 0
            if "services" in category and len(category["services"]) > 0:
                service_count = category["services"][0].get("count", 0)

            # Remove the services field and add count
            category_data = {k: v for k, v in category.items() if k != "services"}
            category_data["service_count"] = service_count
            categories.append(category_data)

        return categories

    except Exception as e:
        logger.error(f"Error fetching service categories: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get all categories")


@category_router.get("/{category_id}", response_model=ServiceCategoryResponse)
def get_single_category(category_id: int):
    try:
        response = (
            supabase.from_("service_categories")
            .select("*")
            .eq("id", category_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Service category not found")

        return response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching category {category_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get single category")


""" 
   [FastAPI and Upsert] 
   1) I don't think it supports optional path params (eg: /:category_id?)

   2) So, we need to split into two separate routes 
   3) However, they utilize the same upsert helper method

"""


# Create
@category_router.put("", status_code=201)
def create_service_category(category_data: ServiceCategoryUpsert):
    return _upsert_category(None, category_data)


# Update
@category_router.put("/{category_id}")
def update_service_category(category_id: int, category_data: ServiceCategoryUpsert):
    return _upsert_category(category_id, category_data)


# Helper to handle both
def _upsert_category(category_id: Optional[int], category_data: ServiceCategoryUpsert):
    # Construct payload
    payload = category_data.model_dump(exclude_unset=True, by_alias=False)

    if category_id is not None:
        payload["id"] = category_id

    try:
        response = supabase.from_("service_categories").upsert(payload).execute()

        if category_id and not response.data:
            raise HTTPException(
                status_code=404, detail="Category to be updated not found"
            )

        return (
            "Category successfully updated"
            if category_id
            else "Category successfully created"
        )

    except Exception as e:
        logger.error(f"Error upserting category: {str(e)}", exc_info=True)

        # If the error is something the user can ACT on
        # Then reveal it to them
        if "service_categories_title_key" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid title, '{category_data.title}' already exists.",
            )

        if "service_categories_color_fkey" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid color name, '{category_data.color}' does not exist.",
            )

        action = "update" if category_id else "create"
        raise HTTPException(
            status_code=500, detail=f"Failed to ${action} single category"
        )


@category_router.delete("/{category_id}")
def delete_category(category_id: int):
    try:
        response = (
            supabase.from_("service_categories")
            .delete()
            .eq("id", category_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Category not found")

        return "Category successfully deleted"

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {str(e)}", exc_info=True)

        if "services_category_id_fkey" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete single category with associated services",
            )

        raise HTTPException(status_code=500, detail="Failed to delete single category")
