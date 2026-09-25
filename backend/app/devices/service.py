from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.devices.models import DeviceRecord
from app.devices.validation import normalize_identifier, normalize_imei
from app.products.models import Product
from app.models.user import User


def create_device_record(
    db: Session,
    organization_id,
    data,
):
    imei = normalize_imei(data.imei) if data.imei else None
    imei_2 = normalize_imei(data.imei_2) if data.imei_2 else None

    barcode = normalize_identifier(data.barcode)
    serial_number = normalize_identifier(data.serial_number)

    if data.product_id is not None:
        product = db.scalar(
            select(Product).where(
                Product.id == data.product_id,
                Product.organization_id == organization_id,
                Product.is_active.is_(True),
            )
        )

        if product is None:
            raise ValueError(
                "Product does not belong to organization"
            )

    if data.received_by_user_id is not None:
        user = db.scalar(
            select(User).where(
                User.id == data.received_by_user_id,
                User.is_active.is_(True),
            )
        )

        if user is None:
            raise ValueError("Receiving user not found")

    if imei is not None:
        existing = db.scalar(
            select(DeviceRecord).where(
                DeviceRecord.organization_id == organization_id,
                DeviceRecord.imei == imei,
            )
        )

        if existing is not None:
            raise ValueError("IMEI already exists")

    if imei_2 is not None:
        existing = db.scalar(
            select(DeviceRecord).where(
                DeviceRecord.organization_id == organization_id,
                DeviceRecord.imei_2 == imei_2,
            )
        )

        if existing is not None:
            raise ValueError("Secondary IMEI already exists")

    if serial_number is not None:
        existing = db.scalar(
            select(DeviceRecord).where(
                DeviceRecord.organization_id == organization_id,
                DeviceRecord.serial_number == serial_number,
            )
        )

        if existing is not None:
            raise ValueError("Serial number already exists")

    if barcode is not None:
        existing = db.scalar(
            select(DeviceRecord).where(
                DeviceRecord.organization_id == organization_id,
                DeviceRecord.barcode == barcode,
            )
        )

        if existing is not None:
            raise ValueError("Barcode already exists")

    device = DeviceRecord(
        organization_id=organization_id,
        product_id=data.product_id,
        imei=imei,
        imei_2=imei_2,
        serial_number=serial_number,
        barcode=barcode,
        brand=data.brand.strip(),
        model=data.model.strip(),
        variant=data.variant.strip(),
        storage=data.storage.strip(),
        color=data.color.strip(),
        source_type=data.source_type.strip(),
        source_name=data.source_name.strip(),
        source_contact=data.source_contact.strip(),
        source_reference=data.source_reference.strip(),
        received_by_user_id=data.received_by_user_id,
        condition=data.condition.strip(),
        status=data.status.strip(),
        acquisition_cost=data.acquisition_cost,
        notes=data.notes.strip(),
    )

    db.add(device)
    db.flush()

    return device


def get_device_record(
    db: Session,
    organization_id,
    device_id,
):
    return db.scalar(
        select(DeviceRecord).where(
            DeviceRecord.id == device_id,
            DeviceRecord.organization_id == organization_id,
        )
    )


def find_device_by_imei(
    db: Session,
    organization_id,
    imei: str,
):
    normalized = normalize_imei(imei)

    return db.scalar(
        select(DeviceRecord).where(
            DeviceRecord.organization_id == organization_id,
            or_(
                DeviceRecord.imei == normalized,
                DeviceRecord.imei_2 == normalized,
            ),
        )
    )


def find_device_by_serial(
    db: Session,
    organization_id,
    serial_number: str,
):
    normalized = normalize_identifier(serial_number)

    return db.scalar(
        select(DeviceRecord).where(
            DeviceRecord.organization_id == organization_id,
            DeviceRecord.serial_number == normalized,
        )
    )


def find_device_by_barcode(
    db: Session,
    organization_id,
    barcode: str,
):
    normalized = normalize_identifier(barcode)

    return db.scalar(
        select(DeviceRecord).where(
            DeviceRecord.organization_id == organization_id,
            DeviceRecord.barcode == normalized,
        )
    )


def search_devices(
    db: Session,
    organization_id,
    search: str,
):
    term = search.strip()

    if not term:
        return []

    normalized = term.upper()
    pattern = f"%{normalized}%"

    statement = (
        select(DeviceRecord)
        .where(
            DeviceRecord.organization_id == organization_id,
            DeviceRecord.is_active.is_(True),
            or_(
                DeviceRecord.imei.ilike(pattern),
                DeviceRecord.imei_2.ilike(pattern),
                DeviceRecord.serial_number.ilike(pattern),
                DeviceRecord.barcode.ilike(pattern),
                DeviceRecord.brand.ilike(pattern),
                DeviceRecord.model.ilike(pattern),
                DeviceRecord.variant.ilike(pattern),
                DeviceRecord.storage.ilike(pattern),
                DeviceRecord.color.ilike(pattern),
                DeviceRecord.source_name.ilike(pattern),
                DeviceRecord.source_contact.ilike(pattern),
                DeviceRecord.source_reference.ilike(pattern),
            ),
        )
        .order_by(DeviceRecord.created_at.desc())
    )

    return list(db.scalars(statement).all())


def get_device_by_id(
    db,
    organization_id,
    device_id,
    user_id,
):
    return get_device_record(
        db,
        organization_id,
        device_id,
        user_id,
    )
