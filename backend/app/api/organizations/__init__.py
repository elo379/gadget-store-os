from app.organizations.routes import router as organizations_router
from app.organizations.store_tree_routes import router as store_tree_router
from app.organizations.invitation_routes import router as invitation_router
from app.organizations.personnel_lifecycle_routes import router as personnel_lifecycle_router
from app.organizations.role_permissions import router as role_permissions_router

router = organizations_router
router.include_router(store_tree_router)
router.include_router(invitation_router)
router.include_router(personnel_lifecycle_router)
router.include_router(role_permissions_router)

__all__ = ["router"]
