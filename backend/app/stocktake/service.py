import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.inventory.models import InventoryItem, InventoryLocation
from app.stocktake.models import Stocktake, StocktakeLine
from app.stocktake.schemas import StocktakeCreate
from app.audit.models import AuditLog


def create_stocktake(
    db: Session,
    payload: StocktakeCreate,
    actor_user_id: uuid.UUID,
):
    existing = db.scalar(
        select(Stocktake).where(
            Stocktake.organization_id == payload.organization_id,
            Stocktake.reference_number
            == payload.reference_number.strip(),
        )
    )

    if existing is not None:
        raise ValueError("Stocktake reference already exists")

    if payload.location_id is not None:
        location = db.scalar(select(InventoryLocation).where(
            InventoryLocation.id == payload.location_id,
            InventoryLocation.organization_id == payload.organization_id,
        ))
        if location is None:
            raise ValueError("Stocktake location not found in organization")

    stocktake = Stocktake(
        organization_id=payload.organization_id,
        location_id=payload.location_id,
        reference_number=payload.reference_number.strip(),
        notes=payload.notes.strip(),
        created_by_user_id=actor_user_id,
    )

    db.add(stocktake)
    db.flush()

    query = select(InventoryItem).where(
        InventoryItem.organization_id == payload.organization_id,
        InventoryItem.status == "active",
    )

    if payload.location_id is not None:
        query = query.where(
            InventoryItem.location_id == payload.location_id
        )

    items = db.scalars(query).all()

    for item in items:
        db.add(
            StocktakeLine(
                stocktake_id=stocktake.id,
                inventory_item_id=item.id,
                expected_quantity=item.quantity,
            )
        )

    db.add(AuditLog(
        organization_id=payload.organization_id, user_id=actor_user_id,
        action="stocktake.started", entity_type="stocktake", entity_id=stocktake.id,
        description="Stocktake started",
        metadata_json=json.dumps({"location_id": str(payload.location_id) if payload.location_id else None, "line_count": len(items)}),
    ))

    db.commit()
    db.refresh(stocktake)
    return stocktake


def get_stocktake(
    db: Session,
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
):
    return db.scalar(
        select(Stocktake).where(
            Stocktake.id == stocktake_id,
            Stocktake.organization_id == organization_id,
        )
    )


def list_stocktakes(
    db: Session,
    organization_id: uuid.UUID,
):
    return list(
        db.scalars(
            select(Stocktake).where(
                Stocktake.organization_id == organization_id
            ).order_by(
                Stocktake.created_at.desc()
            )
        ).all()
    )


def count_stocktake_line(
    db: Session,
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    line_id: uuid.UUID,
    counted_quantity,
    actor_user_id: uuid.UUID,
    notes: str = "",
):
    line = db.scalar(
        select(StocktakeLine)
        .join(Stocktake)
        .where(
            StocktakeLine.id == line_id,
            StocktakeLine.stocktake_id == stocktake_id,
            Stocktake.organization_id == organization_id,
        )
    )

    if line is None:
        raise ValueError("Stocktake line not found")

    if line.stocktake.status != "draft":
        raise ValueError("Stocktake is not open for counting")

    line.counted_quantity = counted_quantity
    line.variance = (
        counted_quantity - line.expected_quantity
    )
    line.notes = notes.strip()
    line.counted_by_user_id = actor_user_id
    db.add(AuditLog(
        organization_id=organization_id, user_id=actor_user_id,
        action="stocktake.line_counted", entity_type="stocktake_line", entity_id=line.id,
        description="Stocktake line counted",
        metadata_json=json.dumps({"stocktake_id": str(stocktake_id), "counted_quantity": str(counted_quantity), "variance": str(line.variance)}),
    ))

    db.commit()
    db.refresh(line)
    return line


def complete_stocktake(
    db: Session,
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
    actor_user_id: uuid.UUID,
):
    from app.inventory.constants import MOVEMENT_ADJUSTMENT
    from app.inventory.service import record_movement

    stocktake = get_stocktake(
        db,
        organization_id,
        stocktake_id,
    )

    if stocktake is None:
        raise ValueError("Stocktake not found")

    if stocktake.status != "draft":
        raise ValueError("Stocktake is already completed")

    lines = list(
        db.scalars(
            select(StocktakeLine).where(
                StocktakeLine.stocktake_id == stocktake.id
            )
        ).all()
    )

    if any(line.counted_quantity is None for line in lines):
        raise ValueError("All stocktake lines must be counted")

    for line in lines:
        variance = line.counted_quantity - line.expected_quantity

        if variance == 0:
            continue

        item = db.get(
            InventoryItem,
            line.inventory_item_id,
        )

        if item is None:
            raise ValueError("Inventory item not found")

        record_movement(
            db,
            organization_id=organization_id,
            inventory_item_id=item.id,
            movement_type=MOVEMENT_ADJUSTMENT,
            quantity=variance,
            reason=f"Stocktake reconciliation: {stocktake.reference_number}",
            reference_type="stocktake",
            reference_id=stocktake.id,
            performed_by_user_id=actor_user_id,
        )

    stocktake.status = "completed"
    stocktake.completed_by_user_id = actor_user_id
    stocktake.completed_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        organization_id=organization_id, user_id=actor_user_id,
        action="stocktake.completed", entity_type="stocktake", entity_id=stocktake.id,
        description="Stocktake completed and variances reconciled",
        metadata_json=json.dumps({"line_count": len(lines)}),
    ))

    db.commit()
    db.refresh(stocktake)
    return stocktake


def get_stocktake_summary(
    db: Session,
    organization_id: uuid.UUID,
    stocktake_id: uuid.UUID,
):
    stocktake = get_stocktake(
        db,
        organization_id,
        stocktake_id,
    )

    if stocktake is None:
        raise ValueError("Stocktake not found")

    lines = list(
        db.scalars(
            select(StocktakeLine).where(
                StocktakeLine.stocktake_id == stocktake.id
            )
        ).all()
    )

    counted = [
        line for line in lines
        if line.counted_quantity is not None
    ]

    positive_variance = sum(
        (
            line.variance
            for line in counted
            if line.variance > 0
        ),
        0,
    )

    negative_variance = sum(
        (
            line.variance
            for line in counted
            if line.variance < 0
        ),
        0,
    )

    variance_lines = sum(
        1
        for line in counted
        if line.variance != 0
    )

    return {
        "stocktake_id": stocktake.id,
        "status": stocktake.status,
        "total_lines": len(lines),
        "counted_lines": len(counted),
        "variance_lines": variance_lines,
        "positive_variance": positive_variance,
        "negative_variance": negative_variance,
    }
