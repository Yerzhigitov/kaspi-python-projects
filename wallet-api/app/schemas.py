from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

Amount = Field(gt=0, max_digits=18, decimal_places=2)


class AccountCreate(BaseModel):
    owner: str = Field(min_length=1, max_length=100)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner: str
    balance: Decimal


class DepositIn(BaseModel):
    amount: Decimal = Amount


class TransferIn(BaseModel):
    from_id: int
    to_id: int
    amount: Decimal = Amount


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    from_id: Optional[int]
    to_id: int
    amount: Decimal
    created_at: datetime
