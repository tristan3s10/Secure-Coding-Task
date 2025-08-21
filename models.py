
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.user)
    transactions = relationship("Transaction", back_populates="owner", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False, index=True)
    description = Column(String(255), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    owner = relationship("User", back_populates="transactions")

    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_transaction_id_user"),
        Index("ix_transactions_user_date", "user_id", "date"),
    )
