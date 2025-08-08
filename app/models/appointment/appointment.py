from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import Field

from app.models._admin import BaseSchema


class AppointmentStatus(str, Enum):
    BOOKED = "Booked"
    CONFIRMED = "Confirmed"
    RESCHEDULE = "Reschedule"
    NO_SHOW = "No show"
    CANCELLED = "Cancelled"


class PaymentMethod(str, Enum):
    CREDITS = "Credits"
    CARD = "Card"
    CASH = "Cash"


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"


"""
    PUT
    1) /api/appointments/:id?
"""


class AppointmentUpsert(BaseSchema):
    customer_id: int = Field(..., gt=0, alias="customerId")
    staff_id: int = Field(..., gt=0, alias="staffId")
    service_id: int = Field(..., gt=0, alias="serviceId")
    outlet_id: int = Field(..., gt=0, alias="outletId")

    start_time: datetime = Field(..., alias="startTime")
    end_time: datetime = Field(..., alias="endTime")

    payment_method: PaymentMethod = Field(..., alias="paymentMethod")
    payment_status: PaymentStatus = Field(..., alias="paymentStatus")

    # Payment fields
    credits_paid: int = Field(..., ge=0, alias="creditsPaid")
    cash_paid: Decimal = Field(
        ..., ge=0, max_digits=10, decimal_places=2, alias="cashPaid"
    )

    notes: Optional[str] = None
    status: AppointmentStatus


"""
    GET
    1) /api/appointments
    2) /api/appointments/:id
    3) /api/appointments/:outletId/:date
"""


class AppointmentResponse(AppointmentUpsert):
    id: int = Field(..., gt=0)
    created_at: datetime
