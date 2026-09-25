import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models import Membership, User
from app.organizations.authority import get_membership_for_user
from app.organizations.invitation_model import PersonnelInvitation
from app.organizations.invitation_schemas import (
    InvitationAccept,
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationResponse,
)
from app.organizations.invitations import (
    accept_invitation,
    create_invitation,
)

router = APIRouter(
    prefix="/organizations",
    tags=["invitations"],
)


@router.post(
    "/{organization_id}/store-tree/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_personnel_invitation(
    organization_id: uuid.UUID,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    creator = get_membership_for_user(
        db,
        organization_id,
        user.id,
    )

    if creator is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization membership required",
        )

    try:
        invitation, _token = create_invitation(
            db,
            organization_id,
            creator,
            payload.email,
            payload.role_name,
        )

        db.commit()
        db.refresh(invitation)

        return invitation

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.get(
    "/{organization_id}/store-tree/invitations",
    response_model=list[InvitationResponse],
)
def list_personnel_invitations(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = get_membership_for_user(
        db,
        organization_id,
        user.id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership required",
        )

    return list(
        db.scalars(
            select(PersonnelInvitation)
            .where(
                PersonnelInvitation.organization_id == organization_id,
            )
            .order_by(PersonnelInvitation.created_at.desc())
        ).all()
    )


@router.post(
    "/store-tree/invitations/accept",
    response_model=InvitationAcceptResponse,
)
def accept_personnel_invitation(
    payload: InvitationAccept,
    db: Session = Depends(get_db),
):
    try:
        membership = accept_invitation(
            db,
            payload.token,
            payload.password,
        )

        db.commit()
        db.refresh(membership)

        return InvitationAcceptResponse(
            membership_id=membership.id,
            personnel_id=membership.personnel_id,
            role_name=membership.role_name,
            account_status=membership.account_status,
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
