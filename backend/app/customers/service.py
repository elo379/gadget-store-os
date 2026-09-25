import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.customers.models import Customer
from app.customers.schemas import CustomerCreate, CustomerUpdate


def create_customer(db: Session, payload: CustomerCreate):
    customer = Customer(
        organization_id=payload.organization_id,
        name=payload.name.strip(),
        phone=payload.phone.strip(),
        email=payload.email.strip(),
        address=payload.address.strip(),
        notes=payload.notes.strip(),
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_customer(
    db: Session,
    organization_id: uuid.UUID,
    customer_id: uuid.UUID,
):
    return db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == organization_id,
        )
    )


def list_customers(
    db: Session,
    organization_id: uuid.UUID,
    search: str | None = None,
):
    query = select(Customer).where(
        Customer.organization_id == organization_id
    )

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            Customer.name.ilike(term)
            | Customer.phone.ilike(term)
            | Customer.email.ilike(term)
        )

    return list(
        db.scalars(
            query.order_by(Customer.name.asc())
        ).all()
    )


def update_customer(
    db: Session,
    customer: Customer,
    payload: CustomerUpdate,
):
    values = payload.model_dump(exclude_unset=True)

    for field, value in values.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer
