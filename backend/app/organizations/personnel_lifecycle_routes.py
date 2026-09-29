import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.auth.schemas import AuthenticatedUser
from app.organizations.authority import get_membership_for_user
from app.organizations.personnel_lifecycle import (
    get_personnel,
    reactivate_personnel,
    revoke_personnel,
    suspend_personnel,
    deactivate_personnel,
)

router = APIRouter(
    prefix="",
    tags=["personnel-lifecycle"],
)


def get_actor(
    db: Session,
    organization_id: uuid.UUID,
    user: AuthenticatedUser,
):
    actor = get_membership_for_user(
        db,
        organization_id,
        uuid.UUID(user.user_id),
    )

    if actor is None:
        raise HTTPException(
            status_code=403,
            detail="Active organization membership required",
        )

    return actor


def get_target(
    db: Session,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
):
    target = get_personnel(
        db,
        organization_id,
        membership_id,
    )

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Personnel not found",
        )

    return target


@router.patch(
    "/{organization_id}/store-tree/personnel/{membership_id}/suspend",
)
def suspend_member(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    actor = get_actor(db, organization_id, user)
    target = get_target(db, organization_id, membership_id)

    try:
        suspend_personnel(db, actor, target)
        db.commit()
        return {"status": "suspended"}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{organization_id}/store-tree/personnel/{membership_id}/reactivate",
)
def reactivate_member(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    actor = get_actor(db, organization_id, user)
    target = get_target(db, organization_id, membership_id)

    try:
        reactivate_personnel(db, actor, target)
        db.commit()
        return {"status": "active"}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{organization_id}/store-tree/personnel/{membership_id}/revoke",
)
def revoke_member(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    actor = get_actor(db, organization_id, user)
    target = get_target(db, organization_id, membership_id)

    try:
        revoke_personnel(db, actor, target)
        db.commit()
        return {"status": "revoked"}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc


@router.patch("/{organization_id}/store-tree/personnel/{membership_id}/deactivate")
def deactivate_member(organization_id: uuid.UUID, membership_id: uuid.UUID, db: Session = Depends(get_db), user: AuthenticatedUser = Depends(get_current_user)):
    actor = get_actor(db, organization_id, user)
    target = get_target(db, organization_id, membership_id)
    try:
        deactivate_personnel(db, actor, target)
        db.commit()
        return {"status": "deactivated"}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
