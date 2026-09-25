import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.products.schemas import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCreate,
    ProductResponse,
)
from app.products.service import (
    create_category,
    create_product,
    get_category,
    get_product,
    list_categories,
    list_products,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "/categories",
    response_model=ProductCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_category(
    organization_id: uuid.UUID,
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
):
    return create_category(
        db=db,
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
    )


@router.get(
    "/categories",
    response_model=list[ProductCategoryResponse],
)
def list_product_categories(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return list_categories(
        db=db,
        organization_id=organization_id,
    )


@router.get(
    "/categories/{category_id}",
    response_model=ProductCategoryResponse,
)
def get_product_category(
    organization_id: uuid.UUID,
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    category = get_category(
        db=db,
        organization_id=organization_id,
        category_id=category_id,
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_endpoint(
    organization_id: uuid.UUID,
    payload: ProductCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_product(
            db=db,
            organization_id=organization_id,
            name=payload.name,
            sku=payload.sku,
            brand=payload.brand,
            model=payload.model,
            description=payload.description,
            category_id=payload.category_id,
            is_serialized=payload.is_serialized,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_product_items(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    return list_products(
        db=db,
        organization_id=organization_id,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product_item(
    organization_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    product = get_product(
        db=db,
        organization_id=organization_id,
        product_id=product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.get(
    "/search/query",
    response_model=list[ProductResponse],
)
def search_product_items(
    organization_id: uuid.UUID,
    search: str,
    db: Session = Depends(get_db),
):
    from app.products.queries import search_products

    if not search.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search term is required",
        )

    return search_products(
        db=db,
        organization_id=organization_id,
        search=search,
    )
