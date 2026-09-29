import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.devices.schemas import DeviceRecordCreate, DeviceRecordResponse
from app.devices.service import (
    create_device_record,
    find_device_by_barcode,
    find_device_by_imei,
    find_device_by_serial,
    get_device_record,
    search_devices,
)
from app.permissions.access import require_organization_permission

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", response_model=DeviceRecordResponse)
def create_device(
    payload: DeviceRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "inventory.manage")
    authoritative_payload = payload.model_copy(update={
        "received_by_user_id": uuid.UUID(current_user.user_id),
    })
    try:
        device = create_device_record(db, payload.organization_id, authoritative_payload)
        db.commit()
        db.refresh(device)
        return device
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/search", response_model=list[DeviceRecordResponse])
def search_device_records(
    organization_id: uuid.UUID,
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "inventory.view")
    if not q:
        return []

    return search_devices(
        db,
        organization_id,
        q,
    )


@router.get("/lookup/imei/{imei}", response_model=DeviceRecordResponse)
def lookup_imei(
    imei: str,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "inventory.view")
    device = find_device_by_imei(
        db,
        organization_id,
        imei,
    )

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.get(
    "/lookup/serial/{serial_number}",
    response_model=DeviceRecordResponse,
)
def lookup_serial(
    serial_number: str,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "inventory.view")
    device = find_device_by_serial(
        db,
        organization_id,
        serial_number,
    )

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.get(
    "/lookup/barcode/{barcode}",
    response_model=DeviceRecordResponse,
)
def lookup_barcode(
    barcode: str,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "inventory.view")
    device = find_device_by_barcode(
        db,
        organization_id,
        barcode,
    )

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.get("/{device_id}", response_model=DeviceRecordResponse)
def get_device(
    device_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "inventory.view")
    device = get_device_record(
        db,
        organization_id,
        device_id,
    )

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device
