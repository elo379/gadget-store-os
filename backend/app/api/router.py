from fastapi import APIRouter

from app.api.auth.routes import router as auth_router
from app.api.auth.passkeys import router as passkeys_router
from app.api.organizations import router as organizations_router
from app.api.products.routes import router as products_router
from app.api.inventory.routes import router as inventory_router
from app.api.devices.routes import router as devices_router
from app.api.sales.routes import router as sales_router
from app.api.purchasing.routes import router as purchasing_router
from app.api.suppliers.routes import router as suppliers_router
from app.api.finance import router as finance_router
from app.api.expenses import router as expenses_router
from app.api.staff import router as staff_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notifications_router
from app.api.stocktake import router as stocktake_router
from app.api.reports import router as reports_router
from app.api.audit import router as audit_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(passkeys_router)
api_router.include_router(organizations_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
api_router.include_router(devices_router)
api_router.include_router(sales_router)
api_router.include_router(purchasing_router)
api_router.include_router(suppliers_router)
api_router.include_router(finance_router)
api_router.include_router(expenses_router)
api_router.include_router(staff_router)
api_router.include_router(dashboard_router)
api_router.include_router(notifications_router)
api_router.include_router(stocktake_router)
api_router.include_router(reports_router)
api_router.include_router(audit_router)

from app.api.customers import router as customers_router
api_router.include_router(customers_router)

from app.api.customers import router as customers_router
api_router.include_router(customers_router)
