import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.organizations.service import create_organization
from app.products.service import create_product
from app.inventory.service import create_location
from app.suppliers.service import create_supplier
from app.suppliers.schemas import SupplierCreate
from app.purchasing.schemas import PurchaseOrderCreate, PurchaseLineCreate, PurchaseReceiveRequest, PurchaseReceiveLine
from app.purchasing.service import create_purchase_order
from app.purchasing.receiving import receive_purchase
from app.sales.schemas import SaleCreate, SaleLineCreate
from app.sales.service import create_sale, add_sale_payment
from app.expenses.service import list_categories, create_expense, update_expense_status
from app.expenses.schemas import ExpenseCreate
from app.finance.service import get_financial_summary, get_reconciliation


def test_multiday_retail_financials_reconcile():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        org = create_organization(db, "Scenario Store", f"scenario-{uuid.uuid4().hex[:8]}", f"{uuid.uuid4().hex}@example.com", "StrongPassword123!")
        actor = org.memberships[0].user
        product = create_product(db, org.id, "USB-C Charger", f"CHG-{uuid.uuid4().hex[:6]}")
        supplier = create_supplier(db, SupplierCreate(organization_id=org.id, name="Device Supply Co"))
        location = create_location(db, org.id, "Main Store")

        # Day 1: receive four units at a traceable acquisition cost of ₦50 each.
        po = create_purchase_order(db, PurchaseOrderCreate(organization_id=org.id, supplier_id=supplier.id,
            reference_number="PO-SCENARIO-1", lines=[PurchaseLineCreate(product_id=product.id, quantity=4, unit_cost=50)]))
        line = po.lines[0]
        receive_purchase(db, PurchaseReceiveRequest(organization_id=org.id, received_by_user_id=actor.id,
            lines=[PurchaseReceiveLine(purchase_line_id=line.id, quantity=4, location_id=location.id)]))
        db.commit()

        # Day 2: sell one unit on account, then collect the balance on day 3.
        sale = create_sale(db, SaleCreate(organization_id=org.id, sold_by_user_id=actor.id, reference_number="SALE-SCENARIO-1",
            lines=[SaleLineCreate(product_id=product.id, location_id=location.id, quantity=1, unit_price=100)],
            amount_paid=25, payment_method="cash"))
        db.commit()
        add_sale_payment(db, sale.id, "bank_transfer", 75, "BANK-1001", performed_by_user_id=actor.id)
        db.commit()

        # Day 3: record and approve a store expense, then record its actual payment.
        category = next(c for c in list_categories(db, org.id) if c.name == "Internet")
        expense = create_expense(db, ExpenseCreate(organization_id=org.id, category_id=category.id, amount=10,
            payment_method="bank_transfer", reference_number="EXP-SCENARIO-1", description="Monthly internet",
            payment_account="Operating account"), actor.id)
        update_expense_status(db, org.id, expense.id, "approved", actor.id)
        update_expense_status(db, org.id, expense.id, "paid", actor.id)

        summary = get_financial_summary(db, org.id)
        assert summary["revenue"] == 100
        assert summary["cogs"] == 50
        assert summary["gross_profit"] == 50
        assert summary["expenses"] == 10
        assert summary["operating_result"] == 40
        assert summary["payments_received"] == 100
        assert summary["customer_outstanding"] == 0
        assert summary["supplier_outstanding"] == 200
        assert summary["inventory_value"] == 150
        assert get_reconciliation(db, org.id)["issue_count"] == 0
    Base.metadata.drop_all(engine)
