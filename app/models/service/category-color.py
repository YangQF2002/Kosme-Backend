from pydantic import Field, field_validator

from app.models._admin import BaseSchema

""" 
    Currently hardcoded
    With sufficient variety and similar color palette to Fresha 

    GET 
    1) /api/category-colors
"""


class CategoryColorResponse(BaseSchema):
    name: str = Field(..., max_length=100)
    hex: str = Field(..., min_length=7, max_length=7)

    @field_validator("hex")
    @classmethod
    def validate_hex_format(cls, v: str) -> str:
        import re

        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Hex must be in format #RRGGBB")
        return v.upper()
