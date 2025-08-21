
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date
from typing import Optional, List
from enum import Enum

class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.user

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    model_config = ConfigDict(from_attributes=True)

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str
    role: RoleEnum

# Transaction Schemas
class TransactionBase(BaseModel):
    amount: float = Field(gt=0, description="Must be positive")
    description: str = Field(max_length=255)
    date: date

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None

class TransactionOut(TransactionBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)
