from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Organization
from app.products.service import (
    create_category,
    create_product,
    list_categories,
    list_products,
)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, Session(engine)


def test_duplicate_category_is_rejected():
    engine, db = build_session()

    organization = Organization(
        name="Store",
        slug="store",
    )
    db.add(organization)
    db.flush()

    create_category(
        db=db,
        organization_id=organization.id,
        name="Phones",
    )

    try:
        create_category(
            db=db,
            organization_id=organization.id,
            name="Phones",
        )
        assert False
    except ValueError as exc:
        assert "Category already exists" in str(exc)

    db.close()
    engine.dispose()


def test_inactive_products_are_not_in_active_listing():
    engine, db = build_session()

    organization = Organization(
        name="Store",
        slug="store",
    )
    db.add(organization)
    db.flush()

    product = create_product(
        db=db,
        organization_id=organization.id,
        name="Test Phone",
        sku="TEST-001",
    )

    product.is_active = False
    db.flush()

    products = list_products(
        db=db,
        organization_id=organization.id,
    )

    assert product not in products

    db.close()
    engine.dispose()


def test_inactive_categories_are_not_in_active_listing():
    engine, db = build_session()

    organization = Organization(
        name="Store",
        slug="store",
    )
    db.add(organization)
    db.flush()

    category = create_category(
        db=db,
        organization_id=organization.id,
        name="Phones",
    )

    category.is_active = False
    db.flush()

    categories = list_categories(
        db=db,
        organization_id=organization.id,
    )

    assert category not in categories

    db.close()
    engine.dispose()
