from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import EmailStr, Field

from app.models._admin import BaseSchema


class ReminderEnum(str, Enum):
    EMAIL_SMS = "Email + SMS"
    SMS_ONLY = "SMS only"
    EMAIL_ONLY = "Email only"


class MembershipStatusEnum(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


"""
    POST
    1) /api/customers
"""


class CustomerCreate(BaseSchema):
    # The ... says that the field is required
    first_name: str = Field(..., max_length=100, alias="firstName")
    last_name: str = Field(..., max_length=100, alias="lastName")
    email: EmailStr = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    birthday: Optional[datetime] = None

    membership_type: Optional[str] = Field(None, max_length=50, alias="membershipType")
    membership_status: MembershipStatusEnum = Field(
        default=MembershipStatusEnum.INACTIVE, alias="membershipStatus"
    )

    # Preferences
    preferred_therapist_id: Optional[int] = Field(
        None, alias="preferredTherapistId", gt=0
    )
    preferred_outlet_id: Optional[int] = Field(None, alias="preferredOutletId", gt=0)
    allergies: List[str] = Field(default_factory=list)
    reminders: ReminderEnum = Field(default=ReminderEnum.EMAIL_SMS)


"""
    GET
    1) /api/customers
    2) /api/customers/search
    3) /api/customers/:id
"""


class CustomerResponse(CustomerCreate):
    id: int = Field(..., gt=0)

    credit_balance: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)

    stripe_customer_id: Optional[str] = Field(None, max_length=255)
    stripe_subscription_id: Optional[str] = Field(None, max_length=255)
