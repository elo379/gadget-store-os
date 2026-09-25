import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Membership, Organization, User
from app.products.models import Product, ProductCategory
from app.products.service import (
    create_category,
    create_product,
    get_product,
    list_products,
)


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, Session(engine)


def test_product_tables_registered():
    assert "products" in Base.metadata.tables
    assert "product_categories" in Base.metadata.tables


def test_create_product():
    engine, db = build_session()

    organization = Organization(
        name="Test Store",
        slug="test-store",
    )
    db.add(organization)
    db.flush()

    product = create_product(
        db=db,
        organization_id=organization.id,
        name="iPhone 15",
        sku="IPH15-128",
        brand="Apple",
        model="iPhone 15",
        is_serialized=True,
    )

    assert product.organization_id == organization.id
    assert product.sku == "IPH15-128"
    assert product.is_serialized is True

    db.close()
    engine.dispose()


def test_duplicate_sku_is_rejected_inside_same_organization():
    engine, db = build_session()

    organization = Organization(
        name="Test Store",
        slug="test-store",
    )
    db.add(organization)
    db.flush()

    create_product(
        db=db,
        organization_id=organization.id,
        name="iPhone 15",
        sku="IPH15",
    )

    try:
        create_product(
            db=db,
            organization_id=organization.id,
            name="Another Phone",
            sku="IPH15",
        )
        assert False
    except ValueError as exc:
        assert "SKU already exists" in str(exc)

    db.close()
    engine.dispose()


def test_same_sku_allowed_in_different_organizations():
    engine, db = build_session()

    first = Organization(
        name="Store One",
        slug="store-one",
    )
    second = Organization(
        name="Store Two",
        slug="store-two",
    )

    db.add_all([first, second])
    db.flush()

    create_product(
        db=db,
        organization_id=first.id,
        name="iPhone 15",
        sku="IPH15",
    )

    product = create_product(
        db=db,
        organization_id=second.id,
        name="iPhone 15",
        sku="IPH15",
    )

    assert product.organization_id == second.id

    db.close()
    engine.dispose()


def test_category_must_belong_to_same_organization():
    engine, db = build_session()

    first = Organization(
        name="Store One",
        slug="store-one",
    )
    second = Organization(
        name="Store Two",
        slug="store-two",
    )

    db.add_all([first, second])
    db.flush()

    category = create_category(
        db=db,
        organization_id=first.id,
        name="Phones",
    )

    try:
        create_product(
            db=db,
            organization_id=second.id,
            name="iPhone 15",
            sku="IPH15",
            category_id=category.id,
        )
        assert False
    except ValueError as exc:
        assert "does not belong" in str(exc)

    db.close()
    engine.dispose()


def test_product_lookup_is_organization_scoped():
    engine, db = build_session()

    first = Organization(
        name="Store One",
        slug="store-one",
    )
    second = Organization(
        name="Store Two",
        slug="store-two",
    )

    db.add_all([first, second])
    db.flush()

    product = create_product(
        db=db,
        organization_id=first.id,
        name="Galaxy S24",
        sku="S24",
    )

    assert get_product(
        db=db,
        organization_id=first.id,
        product_id=product.id,
    ) is not None

    assert get_product(
        db=db,
        organization_id=second.id,
        product_id=product.id,
    ) is None

    db.close()
    engine.dispose()
