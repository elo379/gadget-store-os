from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.organizations.schemas import (
    MembershipResponse,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
)
from app.models.membership import Membership
from app.organizations.service import (
    create_organization,
    get_membership,
    get_organization,
)

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_organization(
    payload: OrganizationCreate,
    db: Session = Depends(get_db),
):
    if not payload.owner_email or not payload.owner_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Owner email and password are required",
        )

    try:
        return create_organization(
            db,
            payload.name,
            payload.slug,
            payload.owner_email,
            payload.owner_password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def read_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
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
):
    membership = get_membership(
        db,
        organization_id,
        user_id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        )

    return membership
