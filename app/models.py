from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    Date,
    CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from app.db import Base, engine

DATABASE_URL = "sqlite:///insurance.db"

# -----------------------------
# Customer Model
# -----------------------------
class Customer(Base):
    __tablename__ = "customer"

    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("age > 0", name="check_age"),
    )

    policies = relationship(
        "Policy",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


# -----------------------------
# Policy Model
# -----------------------------
class Policy(Base):
    __tablename__ = "policy"

    policy_id = Column(String, primary_key=True)
    customer_id = Column(
        String,
        ForeignKey("customer.customer_id"),
        nullable=False
    )

    policy_issue_date = Column(Date, nullable=False)
    coverage_limit = Column(Float, nullable=False)
    deductible = Column(Float, nullable=False)
    state = Column(String, nullable=False)

    customer = relationship(
        "Customer",
        back_populates="policies"
    )

    claims = relationship(
        "Claim",
        back_populates="policy",
        cascade="all, delete-orphan"
    )


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(String, primary_key=True)
    policy_id = Column(
        String,
        ForeignKey("policy.policy_id"),
        nullable=False
    )

    loss_date = Column(Date, nullable=False)
    loss_amount = Column(Float, nullable=False)
    cause = Column(String, nullable=False)

    policy = relationship(
        "Policy",
        back_populates="claims"
    )

# -----------------------------
# Create Tables
# -----------------------------
def create_tables():
    Base.metadata.create_all(bind=engine)

