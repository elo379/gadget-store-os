import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.products.models import Product, ProductCategory


def create_category(
    db: Session,
    organization_id: uuid.UUID,
    name: str,
    description: str = "",
) -> ProductCategory:
    existing = db.scalar(
        select(ProductCategory).where(
            ProductCategory.organization_id == organization_id,
            ProductCategory.name == name,
        )
    )

    if existing:
        raise ValueError("Category already exists")

    category = ProductCategory(
        organization_id=organization_id,
        name=name,
        description=description,
    )

    db.add(category)
    db.flush()

    return category


def create_product(
    db: Session,
    organization_id: uuid.UUID,
    name: str,
    sku: str,
    brand: str = "",
    model: str = "",
    description: str = "",
    category_id: uuid.UUID | None = None,
    is_serialized: bool = False,
    product_type: str = "other",
    barcode: str = "",
    unit_cost=0,
    selling_price=0,
    reorder_threshold=0,
) -> Product:
    product_type = product_type.strip().lower()
    if product_type not in {"smartphone", "laptop", "tablet", "accessory", "screen_protector", "charger_cable", "wearable", "audio", "other"}:
        raise ValueError("Unsupported product type")
    if product_type in {"smartphone", "laptop", "tablet", "wearable"} and not is_serialized:
        raise ValueError("This product type must be serialized")
    existing = db.scalar(
        select(Product).where(
            Product.organization_id == organization_id,
            Product.sku == sku,
        )
    )

    if existing:
        raise ValueError("Product SKU already exists")

    if category_id is not None:
        category = db.scalar(
            select(ProductCategory).where(
                ProductCategory.id == category_id,
                ProductCategory.organization_id == organization_id,
                ProductCategory.is_active.is_(True),
            )
        )

        if category is None:
            raise ValueError("Category does not belong to organization")

    product = Product(
        organization_id=organization_id,
        category_id=category_id,
        name=name,
        sku=sku,
        brand=brand,
        model=model,
        description=description,
        is_serialized=is_serialized,
        product_type=product_type,
        barcode=barcode.strip(),
        unit_cost=unit_cost,
        selling_price=selling_price,
        reorder_threshold=reorder_threshold,
    )

    db.add(product)
    db.flush()

    return product


def get_product(
    db: Session,
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
) -> Product | None:
    return db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.organization_id == organization_id,
        )
    )


def list_products(
    db: Session,
    organization_id: uuid.UUID,
) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .where(
                Product.organization_id == organization_id,
                Product.is_active.is_(True),
            )
            .order_by(Product.created_at.desc())
        ).all()
    )


def get_category(
    db: Session,
    organization_id: uuid.UUID,
    category_id: uuid.UUID,
) -> ProductCategory | None:
    return db.scalar(
        select(ProductCategory).where(
            ProductCategory.id == category_id,
            ProductCategory.organization_id == organization_id,
        )
    )


def list_categories(
    db: Session,
    organization_id: uuid.UUID,
) -> list[ProductCategory]:
    return list(
        db.scalars(
            select(ProductCategory)
            .where(
                ProductCategory.organization_id == organization_id,
                ProductCategory.is_active.is_(True),
            )
            .order_by(ProductCategory.name)
        ).all()
    )
