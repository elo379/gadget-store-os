from sqlalchemy import select
from sqlalchemy.orm import Session

from app.suppliers.models import Supplier
from app.suppliers.schemas import SupplierCreate


def create_supplier(
    db: Session,
    payload: SupplierCreate,
) -> Supplier:
    existing = db.scalar(
        select(Supplier).where(
            Supplier.organization_id == payload.organization_id,
            Supplier.name == payload.name.strip(),
        )
    )

    if existing is not None:
        raise ValueError("Supplier already exists")

    supplier = Supplier(
        organization_id=payload.organization_id,
        name=payload.name.strip(),
        contact_person=payload.contact_person.strip(),
        phone=payload.phone.strip(),
        email=payload.email.strip().lower(),
        address=payload.address.strip(),
        notes=payload.notes.strip(),
        is_active=True,
    )

    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    return supplier


def get_supplier(
    db: Session,
    organization_id,
    supplier_id,
) -> Supplier | None:
    return db.scalar(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.organization_id == organization_id,
        )
    )


def list_suppliers(
    db: Session,
    organization_id,
    active_only: bool = True,
) -> list[Supplier]:
    statement = select(Supplier).where(
        Supplier.organization_id == organization_id,
    )

    if active_only:
        statement = statement.where(
            Supplier.is_active.is_(True),
        )

    statement = statement.order_by(Supplier.name)

    return list(db.scalars(statement).all())
