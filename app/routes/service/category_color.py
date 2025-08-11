import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.models.service.category_color import CategoryColorResponse
from db.supabase import supabase

logger = logging.getLogger(__name__)

category_color_router = APIRouter(
    prefix="/api/category-colors",
    tags=["category-colors"],
)


@category_color_router.get("", response_model=List[CategoryColorResponse])
async def get_all_category_colors():
    try:
        category_colors = (
            supabase.from_("service_categories_colors").select("*").execute()
        )
        return category_colors.data
    except Exception as e:
        logger.error(f"Error fetching category colors: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get all category colors")
