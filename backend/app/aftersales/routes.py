import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.permissions.access import require_organization_permission
from app.aftersales.models import RepairCase, RepairStatusHistory
from app.customers.models import Customer
from app.devices.models import DeviceRecord
from app.audit.models import AuditLog
from app.finance.models import FinancialTransaction
from app.models.membership import Membership

router = APIRouter(prefix="/aftersales", tags=["after-sales"])


@router.get("/repairs")
def list_repairs(organization_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "customers.view")
    return list(db.scalars(select(RepairCase).where(RepairCase.organization_id == organization_id).order_by(RepairCase.created_at.desc())).all())


@router.get("/warranties")
def list_warranties(organization_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "customers.view")
    return list(db.scalars(select(Warranty).where(Warranty.organization_id == organization_id).order_by(Warranty.ends_at.asc())).all())


class RepairIntake(BaseModel):
    organization_id: uuid.UUID
    device_id: uuid.UUID
    customer_id: uuid.UUID
    reference_number: str = Field(min_length=1, max_length=100)
    notes: str = ""


class RepairUpdate(BaseModel):
    status: str | None = None
    diagnosis: str | None = None
    parts: str | None = None
    labour: Decimal | None = Field(default=None, ge=0)
    cost: Decimal | None = Field(default=None, ge=0)
    customer_charge: Decimal | None = Field(default=None, ge=0)
    assigned_to_user_id: uuid.UUID | None = None
    notes: str | None = None


@router.post("/repairs", status_code=201)
def intake_repair(payload: RepairIntake, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "sales.manage")
    device = db.scalar(select(DeviceRecord).where(DeviceRecord.id == payload.device_id, DeviceRecord.organization_id == payload.organization_id).with_for_update())
    customer = db.scalar(select(Customer).where(Customer.id == payload.customer_id, Customer.organization_id == payload.organization_id))
    if device is None or customer is None:
        raise HTTPException(status_code=404, detail="Device or customer not found")
    if device.status not in {"sold", "service"}:
        raise HTTPException(status_code=409, detail="Device is not eligible for service")
    case = RepairCase(organization_id=payload.organization_id, device_id=device.id, customer_id=customer.id, reference_number=payload.reference_number, notes=payload.notes)
    device.status = "service"
    db.add(case)
    db.flush()
    db.add(RepairStatusHistory(repair_id=case.id, from_status="", to_status="intake", changed_by_user_id=uuid.UUID(current_user.user_id), notes=payload.notes))
    db.commit()
    db.refresh(case)
    return case


@router.patch("/repairs/{repair_id}")
def update_repair(repair_id: uuid.UUID, organization_id: uuid.UUID, payload: RepairUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "sales.manage")
    case = db.scalar(select(RepairCase).where(RepairCase.id == repair_id, RepairCase.organization_id == organization_id).with_for_update())
    if case is None:
        raise HTTPException(status_code=404, detail="Repair not found")
    values = payload.model_dump(exclude_unset=True)
    assignee_id = values.get("assigned_to_user_id")
    if assignee_id and db.scalar(select(Membership.id).where(Membership.organization_id == organization_id, Membership.user_id == assignee_id, Membership.is_active.is_(True))) is None:
        raise HTTPException(status_code=409, detail="Repair assignee must be an active organization member")
    status = values.get("status")
    if status not in {None, "intake", "diagnosis", "assigned", "waiting_parts", "repairing", "completed", "collected"}:
        raise HTTPException(status_code=422, detail="Invalid repair status")
    old_status = case.status
    for key, value in values.items():
        setattr(case, key, value)
    if status and status != old_status:
        db.add(RepairStatusHistory(repair_id=case.id, from_status=old_status, to_status=status, changed_by_user_id=uuid.UUID(current_user.user_id), notes=values.get("notes", "")))
        db.add(AuditLog(organization_id=organization_id, user_id=uuid.UUID(current_user.user_id), action="repair.status_changed", entity_type="repair", entity_id=case.id, description=f"Repair {case.reference_number}: {old_status} → {status}", metadata_json="{}"))
    if status == "completed":
        for transaction_type, direction, amount, description in (
            ("repair_cost", "debit", case.cost, f"Repair cost {case.reference_number}"),
            ("repair_charge", "credit", case.customer_charge, f"Customer repair charge {case.reference_number}"),
        ):
            exists = db.scalar(select(FinancialTransaction.id).where(FinancialTransaction.reference_type == "repair", FinancialTransaction.reference_id == case.id, FinancialTransaction.transaction_type == transaction_type))
            if not exists and amount:
                db.add(FinancialTransaction(organization_id=organization_id, transaction_type=transaction_type, direction=direction, amount=amount, reference_type="repair", reference_id=case.id, description=description, actor_id=uuid.UUID(current_user.user_id)))
    if status == "collected":
        case.device.status = "sold"
    db.commit()
    db.refresh(case)
    return case


@router.get("/customers/{customer_id}")
def customer_history(customer_id: uuid.UUID, organization_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "customers.view")
    customer = db.scalar(select(Customer).where(Customer.id == customer_id, Customer.organization_id == organization_id))
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    from app.sales.models import Sale
    from app.customers.returns import CustomerReturn
    sales = list(db.scalars(select(Sale).where(Sale.customer_id == customer.id).order_by(Sale.created_at.desc())).all())
    returns = list(db.scalars(select(CustomerReturn).where(CustomerReturn.customer_id == customer.id).order_by(CustomerReturn.created_at.desc())).all())
    repairs = list(db.scalars(select(RepairCase).where(RepairCase.customer_id == customer.id).order_by(RepairCase.created_at.desc())).all())
    return {"profile": customer, "purchases": sales, "orders": [], "payments": [p for sale in sales for p in sale.payments], "outstanding": sum((sale.total - sum((p.amount for p in sale.payments), Decimal("0")) for sale in sales), Decimal("0")), "devices": [line.device for sale in sales for line in sale.lines if line.device], "warranties": list(db.scalars(select(__import__("app.aftersales.models", fromlist=["Warranty"]).Warranty).where(__import__("app.aftersales.models", fromlist=["Warranty"]).Warranty.customer_id == customer.id)).all()), "returns": returns, "repairs": repairs, "notes": customer.notes, "activity": list(db.scalars(select(AuditLog).where(AuditLog.organization_id == organization_id, AuditLog.entity_id.in_([sale.id for sale in sales] + [repair.id for repair in repairs] + [record.id for record in returns])).order_by(AuditLog.created_at.desc())).all())}
