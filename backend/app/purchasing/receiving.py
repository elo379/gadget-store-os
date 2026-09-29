import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.devices.models import DeviceRecord
from app.devices.validation import normalize_imei, normalize_identifier
from app.inventory.constants import MOVEMENT_RECEIVE
from app.inventory.models import InventoryItem, InventoryLocation
from app.inventory.service import record_movement
from app.products.models import Product
from app.models.organization import Organization
from app.purchasing.models import PurchaseLine, PurchaseOrder
from app.purchasing.schemas import PurchaseReceiveRequest
from app.purchasing.service import create_supplier_transaction


def receive_purchase(
    db: Session,
    payload: PurchaseReceiveRequest,
):
    if db.scalar(select(Organization.id).where(Organization.id == payload.organization_id).with_for_update()) is None:
        raise ValueError("Organization not found")
    purchase_ids = set()
    receipt_totals = {}

    for item in payload.lines:
        line = db.scalar(
            select(PurchaseLine)
            .where(PurchaseLine.id == item.purchase_line_id)
            .with_for_update()
        )

        if line is None:
            raise ValueError("Purchase line not found")

        purchase = db.scalar(
            select(PurchaseOrder)
            .where(
                PurchaseOrder.id == line.purchase_id,
                PurchaseOrder.organization_id == payload.organization_id,
            )
        )

        if purchase is None:
            raise ValueError("Purchase order not found")

        if purchase.status == "received":
            raise ValueError("Purchase order already received")

        if item.quantity + line.received_quantity > line.quantity:
            raise ValueError("Received quantity exceeds purchased quantity")

        product = db.scalar(
            select(Product).where(
                Product.id == line.product_id,
                Product.organization_id == payload.organization_id,
                Product.is_active.is_(True),
            )
        )

        if product is None:
            raise ValueError("Product not found")

        if product.is_serialized and item.quantity != 1:
            raise ValueError("Serialized products must be received one unit at a time")
        if not product.is_serialized and any((item.imei, item.imei_2, item.serial_number, item.barcode)):
            raise ValueError("Identifiers may only be supplied for serialized products")

        location = None

        if item.location_id is not None:
            location = db.scalar(
                select(InventoryLocation).where(
                    InventoryLocation.id == item.location_id,
                    InventoryLocation.organization_id
                    == payload.organization_id,
                    InventoryLocation.is_active.is_(True),
                )
            )

            if location is None:
                raise ValueError("Inventory location not found")

        inventory = db.scalar(
            select(InventoryItem).where(
                InventoryItem.organization_id == payload.organization_id,
                InventoryItem.product_id == product.id,
                InventoryItem.location_id == item.location_id,
                InventoryItem.status == "active",
            )
        )

        if inventory is None:
            inventory = InventoryItem(
                organization_id=payload.organization_id,
                product_id=product.id,
                location_id=item.location_id,
                quantity=Decimal("0"),
                reserved_quantity=Decimal("0"),
                status="active",
                notes="",
            )
            db.add(inventory)
            db.flush()

        if not product.is_serialized:
            old_quantity = Decimal(str(inventory.quantity))
            old_cost = Decimal(str(inventory.average_unit_cost))
            received_quantity = Decimal(str(item.quantity))
            if old_quantity > 0 and old_cost <= 0:
                raise ValueError("Existing quantity inventory has no acquisition cost basis; reconcile its opening cost before receipt")
            if line.unit_cost <= 0:
                raise ValueError("Received stock requires a positive acquisition cost")
            inventory.average_unit_cost = ((old_quantity * old_cost) + (received_quantity * line.unit_cost)) / (old_quantity + received_quantity)

        record_movement(
            db=db,
            organization_id=payload.organization_id,
            inventory_item_id=inventory.id,
            movement_type=MOVEMENT_RECEIVE,
            quantity=item.quantity,
            reason=f"Purchase receipt {purchase.reference_number}",
            reference_type="purchase_order",
            reference_id=purchase.id,
            performed_by_user_id=payload.received_by_user_id,
        )
        line.received_quantity += item.quantity
        receipt_totals[purchase.id] = receipt_totals.get(purchase.id, Decimal("0")) + item.quantity * line.unit_cost

        if product.is_serialized:
            imei = normalize_imei(item.imei)
            imei_2 = normalize_imei(item.imei_2)
            serial = normalize_identifier(item.serial_number)
            barcode = normalize_identifier(item.barcode)

            if not imei and not serial and not barcode:
                raise ValueError(
                    "Serialized products require IMEI, serial number, or barcode"
                )

            existing = None

            for identifier in (imei, imei_2, serial, barcode):
                if not identifier:
                    continue

                existing = db.scalar(
                    select(DeviceRecord).where(
                        DeviceRecord.organization_id
                        == payload.organization_id,
                        (
                            (DeviceRecord.imei == identifier)
                            | (DeviceRecord.imei_2 == identifier)
                            | (DeviceRecord.serial_number == identifier)
                            | (DeviceRecord.barcode == identifier)
                        ),
                    )
                )

                if existing is not None:
                    break

            if existing is not None:
                raise ValueError("Device identifier already exists")

            device = DeviceRecord(
                organization_id=payload.organization_id,
                product_id=product.id,
                imei=imei,
                imei_2=imei_2,
                serial_number=serial,
                barcode=barcode,
                brand=item.brand.strip() or product.brand,
                model=item.model.strip() or product.model,
                variant=item.variant.strip(),
                storage=item.storage.strip(),
                ram=item.ram.strip(),
                color=item.color.strip(),
                network_sim=item.network_sim.strip(),
                grade=item.grade.strip(),
                selling_price=item.selling_price,
                warranty=item.warranty.strip(),
                location_id=item.location_id,
                source_type="supplier",
                source_name=purchase.supplier.name,
                source_contact=purchase.supplier.phone,
                source_reference=purchase.reference_number,
                received_by_user_id=payload.received_by_user_id,
                condition=item.condition.strip(),
                status="in_stock",
                acquisition_cost=line.unit_cost,
                notes=item.notes.strip(),
                is_active=True,
            )

            db.add(device)

        purchase_ids.add(purchase.id)

    db.flush()

    for purchase_id in purchase_ids:
        purchase = db.scalar(
            select(PurchaseOrder).where(
                PurchaseOrder.id == purchase_id,
                PurchaseOrder.organization_id == payload.organization_id,
            )
        )

        if purchase is None:
            continue

        lines = db.scalars(select(PurchaseLine).where(PurchaseLine.purchase_id == purchase_id)).all()
        purchase.status = "received" if all(
            line.received_quantity >= line.quantity for line in lines
        ) else "partially_received"

        create_supplier_transaction(
            db,
            payload=type(
                "SupplierTransactionPayload",
                (),
                {
                    "organization_id": purchase.organization_id,
                    "supplier_id": purchase.supplier_id,
                    "transaction_type": "purchase",
                    "amount": receipt_totals[purchase.id],
                    "reference_type": "purchase_order",
                    "reference_id": purchase.id,
                    "notes": f"Purchase receipt {purchase.reference_number}",
                },
            )(),
            performed_by_user_id=payload.received_by_user_id,
        )

    db.commit()

    return {
        "status": "received",
        "purchase_ids": list(purchase_ids),
    }
