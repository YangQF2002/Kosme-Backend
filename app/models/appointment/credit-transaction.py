from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models._admin import BaseSchema

""" 
    PUT 
    1) /api/appointments/:id? (this is required internally)
"""


class CreditTransactionCreate(BaseSchema):
    customer_id: int = Field(..., gt=0, alias="customerId")
    appointment_id: int = Field(None, gt=0, alias="appointmentId")

    amount: int  # Positive for credits added, negative for credits used
    type: str
    description: Optional[str] = None

    created_at: datetime
