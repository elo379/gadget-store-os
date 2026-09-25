from fastapi import APIRouter

from app.api.auth.routes import router as auth_router
from app.api.organizations.routes import router as organizations_router
from app.api.products.routes import router as products_router
from app.api.inventory.routes import router as inventory_router
from app.api.devices.routes import router as devices_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(organizations_router)

api_router.include_router(products_router)

api_router.include_router(inventory_router)
api_router.include_router(devices_router)

from app.api.finance import router as finance_router

api_router.include_router(finance_router)

from app.api.expenses import router as expenses_router

api_router.include_router(expenses_router)

from app.api.staff import router as staff_router

api_router.include_router(staff_router)
