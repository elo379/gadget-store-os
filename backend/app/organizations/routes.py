from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.organizations.schemas import (
    MembershipResponse,
    OrganizationResponse,
)
from app.organizations.service import (
    get_membership,
    get_organization,
)

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
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
