from typing import Optional

from pydantic import Field

from app.models._admin import BaseSchema

"""
    PUT
    1) /api/service-categories/:id?
"""


class ServiceCategoryUpsert(BaseSchema):
    title: str = Field(..., max_length=100)
    color: str = Field(..., max_length=100)  # Color name
    description: Optional[str] = None


"""
    GET
    1) /api/service-categories
    2) /api/service-categories/:id
"""


class ServiceCategoryResponse(ServiceCategoryUpsert):
    id: int = Field(..., gt=0)
