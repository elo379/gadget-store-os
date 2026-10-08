import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.stocktake.access import require_stocktake_access
from app.stocktake.models import Stocktake, StocktakeLine
from app.stocktake.schemas import StocktakeCount, StocktakeCreate
from app.stocktake.service import (
    complete_stocktake,
    count_stocktake_line,
    create_stocktake,
    get_stocktake,
    list_stocktakes,
    get_stocktake_summary,
)

router = APIRouter(
    prefix="/stocktakes",
    tags=["stocktake"],
)


@router.post("")
def create_stocktake_route(
    payload: StocktakeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_stocktake_access(db, current_user, payload.organization_id, manage=True)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    try:
        return create_stocktake(db, payload, uuid.UUID(current_user.user_id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}")
def stocktakes(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_stocktake_access(db, current_user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return list_stocktakes(db, organization_id)


@router.get("/{organization_id}/{stocktake_id}")
def stocktake(
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_stocktake(
        db,
        organization_id,
        stocktake_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Stocktake not found",
        )

    try:
        require_stocktake_access(db, current_user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return result


@router.get("/{organization_id}/{stocktake_id}/lines")
def stocktake_lines(
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_stocktake_access(db, current_user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return list(
        db.scalars(
            select(StocktakeLine)
            .join(Stocktake, Stocktake.id == StocktakeLine.stocktake_id)
            .where(
                StocktakeLine.stocktake_id == stocktake_id,
                Stocktake.organization_id == organization_id,
            )
            .order_by(StocktakeLine.created_at.asc())
        ).all()
    )


@router.patch(
    "/{organization_id}/{stocktake_id}/lines/{line_id}"
)
def count_line(
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    line_id: uuid.UUID,
    payload: StocktakeCount,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_stocktake_access(db, current_user, organization_id, manage=True)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    try:
        return count_stocktake_line(
            db,
            organization_id,
            stocktake_id,
            line_id,
            payload.counted_quantity,
            uuid.UUID(current_user.user_id),
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/{organization_id}/{stocktake_id}/complete"
)
def complete(
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_stocktake_access(db, current_user, organization_id, manage=True)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    try:
        return complete_stocktake(
            db,
            organization_id,
            stocktake_id,
            uuid.UUID(current_user.user_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))



@router.get("/{organization_id}/{stocktake_id}/summary")
def summary(
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_stocktake_access(db, current_user, organization_id)
        return get_stocktake_summary(
            db,
            organization_id,
            stocktake_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
