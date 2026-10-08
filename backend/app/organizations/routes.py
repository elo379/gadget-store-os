from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.permissions.access import require_organization_permission
from app.organizations.schemas import (
    MembershipResponse,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
)
from app.models.membership import Membership
from app.organizations.service import (
    get_membership,
    get_organization,
)
from app.models import Membership
from app.activation.service import create_organization_with_code, is_rate_limited, register_failed_attempt
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


@router.get("")
def list_my_organizations(
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    memberships = db.scalars(
        select(Membership).where(
            Membership.user_id == UUID(user.user_id),
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )
    ).all()
    return [
        {
            "organization_id": str(item.organization.id),
            "name": item.organization.name,
            "slug": item.organization.slug,
            "role_name": item.role_name,
            "is_owner": item.is_owner,
        }
        for item in memberships
    ]


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_organization(
    payload: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    if not payload.owner_email or not payload.owner_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Owner email and password are required",
        )

    remote_address = request.client.host if request.client else "unknown"
    if is_rate_limited(db, remote_address):
        raise HTTPException(status_code=429, detail="Too many activation attempts. Try again later.")

    try:
        return create_organization_with_code(
            db,
            name=payload.name,
            slug=payload.slug,
            owner_email=payload.owner_email,
            owner_password=payload.owner_password,
            activation_code=payload.activation_code,
        )
    except ValueError as exc:
        if "activation code" in str(exc).lower():
            blocked = register_failed_attempt(db, remote_address)
            db.commit()
            if blocked:
                raise HTTPException(status_code=429, detail="Too many activation attempts. Try again later.")
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST if "activation code" in str(exc).lower() else status.HTTP_409_CONFLICT),
            detail=("Invalid or unavailable activation code" if "activation code" in str(exc).lower() else str(exc)),
        )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def read_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    require_organization_permission(db, UUID(user.user_id), organization_id, "organization.view")
    organization = get_organization(db, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


@router.get(
    "/{organization_id}/memberships/{user_id}",
    response_model=MembershipResponse,
)
def read_membership(
    organization_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    caller = UUID(user.user_id)
    require_organization_permission(db, caller, organization_id, "members.view")
    membership = get_membership(
        db,
        organization_id,
        user_id,
    )

    caller_membership = db.scalar(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == caller,
        Membership.is_active.is_(True),
        Membership.account_status == "active",
    ))
    if membership is not None and caller_membership is not None and not caller_membership.is_owner:
        ancestor = membership
        visible = membership.user_id == caller
        while ancestor is not None and not visible:
            visible = ancestor.parent_membership_id == caller_membership.id
            ancestor = ancestor.parent_membership
        if not visible:
            membership = None

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )

    return membership
