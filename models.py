"""
Модели базы данных для Traffk MVP
"""
from sqlalchemy import (
    BigInteger, String, Text, Numeric, Integer, 
    DateTime, Enum as SQLEnum, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import enum
from database import Base


class UserRole(PyEnum):
    """Роли пользователей"""
    ADVERTISER = "advertiser"
    TRAFFIC = "traffic"
    BOTH = "both"


class TaskStatus(PyEnum):
    """Статусы заданий"""
    DRAFT = "draft"
    PUBLISHED = "published"
    TAKEN = "taken"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class TransactionType(PyEnum):
    """Типы транзакций"""
    DEPOSIT = "deposit"
    PAYOUT = "payout"
    COMMISSION = "commission"
    REFUND = "refund"


class TransactionStatus(PyEnum):
    """Статусы транзакций"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DisputeStatus(PyEnum):
    """Статусы споров"""
    OPEN = "open"
    RESOLVED = "resolved"


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = BigInteger().with_variant(Integer, "sqlite").primary_key()
    telegram_id = BigInteger().unique().nullable(False, index=True)
    username = String(255)
    role = SQLEnum(UserRole, nullable=True)  # Может быть None при первой регистрации
    balance = Numeric(10, 2, default=0, nullable=False)
    reputation = Integer(default=0, nullable=False)
    created_at = DateTime(timezone=True, server_default=func.now())
    updated_at = DateTime(timezone=True, onupdate=func.now())
    
    # Relationships
    tasks_as_advertiser = relationship("Task", foreign_keys="Task.advertiser_id", back_populates="advertiser")
    tasks_as_executor = relationship("Task", foreign_keys="Task.executor_id", back_populates="executor")
    transactions = relationship("Transaction", back_populates="user")
    disputes_opened = relationship("Dispute", foreign_keys="Dispute.opened_by", back_populates="opener")
    disputes_resolved = relationship("Dispute", foreign_keys="Dispute.resolved_by", back_populates="resolver")


class Task(Base):
    """Модель задания"""
    __tablename__ = "tasks"
    
    id = BigInteger().with_variant(Integer, "sqlite").primary_key()
    advertiser_id = BigInteger().with_variant(Integer, "sqlite").nullable(False)
    executor_id = BigInteger().with_variant(Integer, "sqlite").nullable(True)
    
    title = String(100, nullable=False)
    description = Text
    link = String(500)
    price = Numeric(10, 2, nullable=False)
    deadline_days = Integer(nullable=False)
    status = SQLEnum(TaskStatus, nullable=False, default=TaskStatus.DRAFT)
    
    # Proof submission
    proof_text = Text
    proof_photos = Text  # JSON array of file_ids
    
    created_at = DateTime(timezone=True, server_default=func.now())
    taken_at = DateTime(timezone=True)
    submitted_at = DateTime(timezone=True)
    completed_at = DateTime(timezone=True)
    updated_at = DateTime(timezone=True, onupdate=func.now())
    
    # Relationships
    advertiser = relationship("User", foreign_keys=[advertiser_id], back_populates="tasks_as_advertiser")
    executor = relationship("User", foreign_keys=[executor_id], back_populates="tasks_as_executor")
    transactions = relationship("Transaction", back_populates="task")
    dispute = relationship("Dispute", back_populates="task", uselist=False)


class Transaction(Base):
    """Модель транзакции"""
    __tablename__ = "transactions"
    
    id = BigInteger().with_variant(Integer, "sqlite").primary_key()
    user_id = BigInteger().with_variant(Integer, "sqlite").nullable(False)
    task_id = BigInteger().with_variant(Integer, "sqlite").nullable(True)
    
    type = SQLEnum(TransactionType, nullable=False)
    amount = Numeric(10, 2, nullable=False)
    status = SQLEnum(TransactionStatus, nullable=False, default=TransactionStatus.PENDING)
    admin_comment = Text
    
    created_at = DateTime(timezone=True, server_default=func.now())
    updated_at = DateTime(timezone=True, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    task = relationship("Task", back_populates="transactions")


class Dispute(Base):
    """Модель спора"""
    __tablename__ = "disputes"
    
    id = BigInteger().with_variant(Integer, "sqlite").primary_key()
    task_id = BigInteger().with_variant(Integer, "sqlite").unique().nullable(False)
    opened_by = BigInteger().with_variant(Integer, "sqlite").nullable(False)
    resolved_by = BigInteger().with_variant(Integer, "sqlite").nullable(True)
    
    reason = Text(nullable=False)
    status = SQLEnum(DisputeStatus, nullable=False, default=DisputeStatus.OPEN)
    resolution = Text
    
    created_at = DateTime(timezone=True, server_default=func.now())
    resolved_at = DateTime(timezone=True)
    
    # Relationships
    task = relationship("Task", back_populates="dispute")
    opener = relationship("User", foreign_keys=[opened_by], back_populates="disputes_opened")
    resolver = relationship("User", foreign_keys=[resolved_by], back_populates="disputes_resolved")
