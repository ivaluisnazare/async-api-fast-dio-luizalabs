from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal
from typing import Optional


class AccountBase(BaseModel):
    user_id: int = Field(..., description="user Id")
    balance: Decimal = Field(0, ge=0, description="account balance", max_digits=10, decimal_places=2)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    balance: Optional[Decimal] = Field(None, ge=0, description="account balance", max_digits=10, decimal_places=2)


class AccountResponse(AccountBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountBalanceResponse(BaseModel):
    account_id: int
    user_id: int
    balance: Decimal
    updated_at: datetime