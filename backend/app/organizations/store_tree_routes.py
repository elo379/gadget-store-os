import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.auth.schemas import AuthenticatedUser
from app.organizations.authority import get_membership_for_user
from app.organizations.store_tree_schemas import (
    PersonnelCreate,
    StoreTreeMember,
    StoreTreePolicyResponse,
    StoreTreePolicyUpdate,
    StoreTreeResponse,
)
from app.organizations.store_tree_service import (
    create_store_tree_personnel,
    get_store_tree,
    get_store_tree_policy,
    update_store_tree_policy,
)
from app.permissions.access import user_has_permission

router = APIRouter(
    prefix="",
    tags=["store-tree"],
)


def require_owner(
    db: Session,
    organization_id: uuid.UUID,
    user: AuthenticatedUser,
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

    if not membership.is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )

    return membership


def visible_personnel(db: Session, organization_id: uuid.UUID, membership, members):
    if membership.is_owner:
        return members
    visible = {membership.id}
    changed = True
    while changed:
        changed = False
        for member in members:
            if member.parent_membership_id in visible and member.id not in visible:
                visible.add(member.id)
                changed = True
    return [member for member in members if member.id in visible]


@router.get(
    "/{organization_id}/store-tree",
    response_model=StoreTreeResponse,
)
def read_store_tree(
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

    members = get_store_tree(
        db,
        organization_id,
    )
    members = visible_personnel(db, organization_id, membership, members)

    return StoreTreeResponse(
        organization_id=organization_id,
        members=[
            StoreTreeMember.model_validate(member)
            for member in members
        ],
    )


@router.get(
    "/{organization_id}/store-tree/policy",
    response_model=StoreTreePolicyResponse,
)
def read_store_tree_policy(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    require_owner(
        db,
        organization_id,
        user,
    )

    policy = get_store_tree_policy(
        db,
        organization_id,
    )
    db.commit()
    return policy


@router.patch(
    "/{organization_id}/store-tree/policy",
    response_model=StoreTreePolicyResponse,
)
def change_store_tree_policy(
    organization_id: uuid.UUID,
    payload: StoreTreePolicyUpdate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    require_owner(
        db,
        organization_id,
        user,
    )

    policy = update_store_tree_policy(
        db,
        organization_id,
        payload,
    )
    db.commit()
    return policy


@router.post(
    "/{organization_id}/store-tree/personnel",
    response_model=StoreTreeMember,
    status_code=status.HTTP_201_CREATED,
)
def create_personnel_member(
    organization_id: uuid.UUID,
    payload: PersonnelCreate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        membership = create_store_tree_personnel(
            db,
            organization_id,
            uuid.UUID(user.user_id),
            payload,
        )
        db.commit()
        db.refresh(membership)
        return membership
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
