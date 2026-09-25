import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.products.models import Product


def search_products(
    db: Session,
    organization_id: uuid.UUID,
    search: str,
) -> list[Product]:
    pattern = f"%{search}%"

    statement = (
        select(Product)
        .where(
            Product.organization_id == organization_id,
            Product.is_active.is_(True),
            or_(
                Product.name.ilike(pattern),
                Product.sku.ilike(pattern),
                Product.brand.ilike(pattern),
                Product.model.ilike(pattern),
            ),
        )
        .order_by(Product.name)
    )

    return list(db.scalars(statement).all())
