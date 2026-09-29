import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.customers.models import Customer
from app.db.dependencies import get_db
from app.devices.models import DeviceRecord
from app.permissions.access import require_organization_permission
from app.products.models import Product
from app.sales.models import Sale
from app.suppliers.models import Supplier

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def global_search(organization_id: uuid.UUID, query: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    term = query.strip()
    if len(term) < 2:
        return []
    user_id = uuid.UUID(current_user.user_id)
    pattern = f"%{term}%"
    results = []

    def allowed(permission: str) -> bool:
        try:
            require_organization_permission(db, user_id, organization_id, permission)
            return True
        except HTTPException:
            return False

    if allowed("products.view"):
        rows = db.scalars(select(Product).where(Product.organization_id == organization_id, or_(Product.name.ilike(pattern), Product.sku.ilike(pattern), Product.barcode.ilike(pattern), Product.brand.ilike(pattern), Product.model.ilike(pattern))).limit(8)).all()
        results.extend({"kind": "Product", "id": str(row.id), "label": row.name, "detail": row.sku, "href": "/products"} for row in rows)
    if allowed("inventory.view"):
        rows = db.scalars(select(DeviceRecord).where(DeviceRecord.organization_id == organization_id, or_(DeviceRecord.imei.ilike(pattern), DeviceRecord.imei_2.ilike(pattern), DeviceRecord.serial_number.ilike(pattern), DeviceRecord.barcode.ilike(pattern))).limit(8)).all()
        results.extend({"kind": "Device", "id": str(row.id), "label": row.model or row.brand or "Registered device", "detail": row.imei or row.serial_number or row.barcode or "", "href": "/devices"} for row in rows)
    if allowed("customers.view"):
        rows = db.scalars(select(Customer).where(Customer.organization_id == organization_id, or_(Customer.name.ilike(pattern), Customer.phone.ilike(pattern), Customer.email.ilike(pattern))).limit(8)).all()
        results.extend({"kind": "Customer", "id": str(row.id), "label": row.name, "detail": row.phone or row.email, "href": "/customers"} for row in rows)
    if allowed("sales.view"):
        rows = db.scalars(select(Sale).where(Sale.organization_id == organization_id, Sale.reference_number.ilike(pattern)).limit(8)).all()
        results.extend({"kind": "Sale", "id": str(row.id), "label": row.reference_number, "detail": str(row.total), "href": "/sales"} for row in rows)
    if allowed("suppliers.view"):
        rows = db.scalars(select(Supplier).where(Supplier.organization_id == organization_id, or_(Supplier.name.ilike(pattern), Supplier.phone.ilike(pattern), Supplier.email.ilike(pattern))).limit(8)).all()
        results.extend({"kind": "Supplier", "id": str(row.id), "label": row.name, "detail": row.phone or row.email, "href": "/purchasing"} for row in rows)
    return results
