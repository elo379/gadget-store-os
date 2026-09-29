import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models import Membership
from app.auth.schemas import AuthenticatedUser
from app.organizations.authority import get_membership_for_user
from app.organizations.invitation_model import PersonnelInvitation
from app.organizations.invitation_schemas import (
    InvitationAccept,
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationCreatedResponse,
    InvitationResponse,
)
from app.organizations.invitations import (
    accept_invitation,
    create_invitation,
)
from app.permissions.access import user_has_permission

router = APIRouter(
    prefix="",
    tags=["invitations"],
)


@router.post(
    "/{organization_id}/store-tree/invitations",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_personnel_invitation(
    organization_id: uuid.UUID,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    creator = get_membership_for_user(
        db,
        organization_id,
        uuid.UUID(user.user_id),
    )

    if creator is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization membership required",
        )

    try:
        invitation, token = create_invitation(
            db,
            organization_id,
            creator,
            payload.email,
            payload.role_name,
        )

        db.commit()
        db.refresh(invitation)

        return InvitationCreatedResponse(
            id=invitation.id,
            organization_id=invitation.organization_id,
            email=invitation.email,
            role_name=invitation.role_name,
            status=invitation.status,
            expires_at=invitation.expires_at,
            activation_id=invitation.id,
            activation_credential=token,
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.patch("/{organization_id}/store-tree/invitations/{invitation_id}/revoke")
def revoke_personnel_invitation(organization_id: uuid.UUID, invitation_id: uuid.UUID, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    from datetime import datetime, timezone
    from app.audit.models import AuditLog
    import json
    actor = get_membership_for_user(db, organization_id, uuid.UUID(user.user_id))
    if actor is None or not actor.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required")
    invitation = db.scalar(select(PersonnelInvitation).where(PersonnelInvitation.id == invitation_id, PersonnelInvitation.organization_id == organization_id))
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Only pending invitations can be revoked")
    invitation.status = "revoked"
    db.add(AuditLog(organization_id=organization_id, user_id=uuid.UUID(user.user_id), action="personnel.invitation_revoked", entity_type="personnel_invitation", entity_id=invitation.id, description="Personnel activation invitation revoked", metadata_json=json.dumps({"status": "revoked"})))
    db.commit()
    return {"status": invitation.status}


@router.get(
    "/{organization_id}/store-tree/invitations",
    response_model=list[InvitationResponse],
)
def list_personnel_invitations(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    membership = get_membership_for_user(
        db,
        organization_id,
        uuid.UUID(user.user_id),
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership required",
        )

    if not membership.is_owner and not user_has_permission(
        db, uuid.UUID(user.user_id), organization_id, "members.view"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Personnel view permission required",
        )

    query = select(PersonnelInvitation).where(
        PersonnelInvitation.organization_id == organization_id,
    )
    if not membership.is_owner:
        visible_ids = {membership.id}
        members = db.scalars(select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )).all()
        changed = True
        while changed:
            changed = False
            for member in members:
                if member.parent_membership_id in visible_ids and member.id not in visible_ids:
                    visible_ids.add(member.id)
                    changed = True
        query = query.where(PersonnelInvitation.parent_membership_id.in_(visible_ids))
    return list(db.scalars(query.order_by(PersonnelInvitation.created_at.desc())).all())


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
            payload.activation_id,
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
        if str(exc) == "Invitation has expired":
            db.commit()
        else:
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
