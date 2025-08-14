from typing import Optional

from pydantic import Field

from app.models._admin import BaseSchema

""" 
    PUT 
    1) /api/appointments/:appointment_id? (this is required internally)

    DELETE 
    1) /api/appointments/:appointment_id (this is required internally)
"""


class CreditTransactionCreate(BaseSchema):
    customer_id: int = Field(..., gt=0, alias="customerId")
    appointment_id: int = Field(None, gt=0, alias="appointmentId")

    # Positive for credits added to customer, negative for credits deducted from customer
    amount: int
    type: str
    description: Optional[str] = None
