from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal

PositiveDecimal = condecimal(ge=0, max_digits=10, decimal_places=2)


class AccountBase(BaseModel):
    user_id: int = Field(..., description="user Id")
    balance: PositiveDecimal = 0


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    balance: Optional[PositiveDecimal] = None


class AccountResponse(AccountBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountBalanceResponse(BaseModel):
    account_id: int
    user_id: int
    balance: Decimal
    updated_at: datetime