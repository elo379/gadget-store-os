import uuid
from datetime import date
from sqlalchemy import select

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.staff.attendance import clock_in, clock_out, list_attendance
from app.staff.schemas import StaffProfileCreate
from app.models import User
from app.staff.service import (
    create_staff,
    get_staff,
    get_staff_attendance_summary,
    list_staff,
)
from app.models import Membership
from app.permissions.access import user_has_permission
from app.staff.models import StaffProfile
from sqlalchemy import select

router = APIRouter(prefix="/staff", tags=["staff"])


def _require_active_org_membership(db, current_user, organization_id):
    membership = db.scalar(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == uuid.UUID(str(current_user.user_id)),
        Membership.is_active.is_(True), Membership.account_status == "active",
    ))
    if membership is None:
        raise HTTPException(status_code=403, detail="Active organization membership required")
    return membership


def _authorize_staff_scope(db: Session, current_user, organization_id: uuid.UUID, staff_id=None, *, manage=False):
    user_id = uuid.UUID(str(current_user.user_id))
    membership = db.scalar(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == user_id,
        Membership.is_active.is_(True),
        Membership.account_status == "active",
    ))
    if membership is None:
        raise HTTPException(status_code=403, detail="Organization access denied")
    if manage:
        permission = "attendance.manage" if staff_id is None else "attendance.view"
        if membership.is_owner or user_has_permission(db, user_id, organization_id, permission):
            return
    elif staff_id is not None:
        profile = db.scalar(select(StaffProfile).where(
            StaffProfile.id == staff_id,
            StaffProfile.organization_id == organization_id,
            StaffProfile.is_active.is_(True),
        ))
        if profile is not None and profile.user_id == user_id:
            return
        if membership.is_owner:
            return
        target = db.scalar(select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == (profile.user_id if profile is not None else None),
        ))
        while target is not None:
            if target.parent_membership_id == membership.id:
                if user_has_permission(db, user_id, organization_id, "attendance.manage"):
                    return
                break
            if target.id == membership.id:
                break
            target = target.parent_membership
    elif membership.is_owner or user_has_permission(db, user_id, organization_id, "members.view"):
        return
    raise HTTPException(status_code=403, detail="Permission denied")


@router.post("")
def add_staff(
    payload: StaffProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _authorize_staff_scope(db, current_user, payload.organization_id)
    user_id = uuid.UUID(str(current_user.user_id))
    membership = db.scalar(select(Membership).where(
        Membership.organization_id == payload.organization_id,
        Membership.user_id == user_id,
        Membership.is_active.is_(True),
        Membership.account_status == "active",
    ))
    if not (membership and membership.is_owner) and not user_has_permission(
        db, user_id, payload.organization_id, "members.manage"
    ):
        raise HTTPException(status_code=403, detail="Permission denied")
    try:
        return create_staff(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}")
def staff(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_active_org_membership(db, current_user, organization_id)
    profiles = list_staff(db, organization_id)
    actor_id = uuid.UUID(str(current_user.user_id))
    actor = db.scalar(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == actor_id,
        Membership.is_active.is_(True),
        Membership.account_status == "active",
    ))
    if actor is not None and not actor.is_owner and not user_has_permission(db, actor_id, organization_id, "members.view"):
        profiles = [profile for profile in profiles if profile.user_id == actor_id]
    elif actor is not None and not actor.is_owner:
        visible_ids = {actor.id}
        memberships = db.scalars(select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )).all()
        changed = True
        while changed:
            changed = False
            for member in memberships:
                if member.parent_membership_id in visible_ids and member.id not in visible_ids:
                    visible_ids.add(member.id)
                    changed = True
        visible_user_ids = {m.user_id for m in memberships if m.id in visible_ids}
        profiles = [profile for profile in profiles if profile.user_id in visible_user_ids]
    emails = {
        str(user.id): user.email
        for user in db.scalars(
            select(User).where(User.id.in_([profile.user_id for profile in profiles]))
        ).all()
    } if profiles else {}
    member_status = {str(member.user_id): member.account_status for member in db.scalars(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id.in_([profile.user_id for profile in profiles]),
    )).all()} if profiles else {}
    return [
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "organization_id": profile.organization_id,
            "staff_code": profile.staff_code,
            "email": emails.get(str(profile.user_id)),
            "phone": profile.phone,
            "job_title": profile.job_title,
            "status": member_status.get(str(profile.user_id), "inactive").capitalize() if profile.is_active else member_status.get(str(profile.user_id), "inactive").capitalize(),
        }
        for profile in profiles
    ]


@router.post("/{organization_id}/{staff_id}/clock-in")
def staff_clock_in(
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_active_org_membership(db, current_user, organization_id)
    profile = db.scalar(select(StaffProfile).where(StaffProfile.id == staff_id, StaffProfile.organization_id == organization_id, StaffProfile.user_id == uuid.UUID(str(current_user.user_id))))
    if profile is None or not profile.is_active:
        raise HTTPException(status_code=403, detail="Attendance is limited to your own staff profile")
    try:
        return clock_in(db, organization_id, staff_id, actor_user_id=uuid.UUID(str(current_user.user_id)))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{organization_id}/{staff_id}/clock-out")
def staff_clock_out(
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_active_org_membership(db, current_user, organization_id)
    profile = db.scalar(select(StaffProfile).where(StaffProfile.id == staff_id, StaffProfile.organization_id == organization_id, StaffProfile.user_id == uuid.UUID(str(current_user.user_id))))
    if profile is None or not profile.is_active:
        raise HTTPException(status_code=403, detail="Attendance is limited to your own staff profile")
    try:
        return clock_out(db, organization_id, staff_id, actor_user_id=uuid.UUID(str(current_user.user_id)))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}/attendance")
def attendance(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    actor_id = uuid.UUID(str(current_user.user_id))
    actor = _require_active_org_membership(db, current_user, organization_id)
    can_view_all = actor.is_owner or user_has_permission(db, actor_id, organization_id, "attendance.view") or user_has_permission(db, actor_id, organization_id, "attendance.manage")
    records = list_attendance(db, organization_id)
    actor = db.scalar(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == uuid.UUID(str(current_user.user_id)),
        Membership.is_active.is_(True),
        Membership.account_status == "active",
    ))
    if actor is not None and not can_view_all:
        own_profile_ids = set(db.scalars(select(StaffProfile.id).where(StaffProfile.organization_id == organization_id, StaffProfile.user_id == actor_id)).all())
        records = [record for record in records if record.staff_id in own_profile_ids]
    elif actor is not None and not actor.is_owner:
        visible = {actor.id}
        members = db.scalars(select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )).all()
        changed = True
        while changed:
            changed = False
            for member in members:
                if member.parent_membership_id in visible and member.id not in visible:
                    visible.add(member.id)
                    changed = True
        user_ids = {member.user_id for member in members if member.id in visible}
        profile_ids = set(db.scalars(select(StaffProfile.id).where(
            StaffProfile.organization_id == organization_id,
            StaffProfile.user_id.in_(user_ids),
        )).all())
        records = [record for record in records if record.staff_id in profile_ids]
    return records


@router.get("/{organization_id}/{staff_id}/attendance-summary")
def attendance_summary(
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _authorize_staff_scope(db, current_user, organization_id, staff_id)
    return get_staff_attendance_summary(
        db,
        organization_id,
        staff_id,
    )


@router.get("/{organization_id}/timebook")
def monthly_timebook(
    organization_id: uuid.UUID,
    month: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        year, month_number = (int(part) for part in month.split("-", 1))
        start = date(year, month_number, 1)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="month must be YYYY-MM")
    actor_id = uuid.UUID(str(current_user.user_id))
    actor = _require_active_org_membership(db, current_user, organization_id)
    can_view_all = actor.is_owner or user_has_permission(db, actor_id, organization_id, "attendance.view") or user_has_permission(db, actor_id, organization_id, "attendance.manage")
    from calendar import monthrange
    from app.staff.attendance import AttendanceRecord
    end = date(year, month_number, monthrange(year, month_number)[1])
    rows = db.scalars(select(AttendanceRecord).where(
        AttendanceRecord.organization_id == organization_id,
        AttendanceRecord.work_date >= start,
        AttendanceRecord.work_date <= end,
        *([] if can_view_all else [AttendanceRecord.staff_id.in_(select(StaffProfile.id).where(StaffProfile.organization_id == organization_id, StaffProfile.user_id == actor_id))]),
    ).order_by(AttendanceRecord.work_date, AttendanceRecord.staff_id)).all()
    profile_ids = {row.staff_id for row in rows}
    profiles = {p.id: p for p in db.scalars(select(StaffProfile).where(
        StaffProfile.organization_id == organization_id, StaffProfile.id.in_(profile_ids)
    )).all()} if profile_ids else {}
    from app.staff.attendance import StaffAbsence
    absences = db.scalars(select(StaffAbsence).where(
        StaffAbsence.organization_id == organization_id,
        StaffAbsence.absence_date >= start,
        StaffAbsence.absence_date <= end,
        *([] if can_view_all else [StaffAbsence.staff_id.in_(select(StaffProfile.id).where(StaffProfile.organization_id == organization_id, StaffProfile.user_id == actor_id))]),
    )).all()
    absence_ids = {row.staff_id for row in absences}
    if absence_ids:
        for profile in db.scalars(select(StaffProfile).where(StaffProfile.organization_id == organization_id, StaffProfile.id.in_(absence_ids))).all():
            profiles.setdefault(profile.id, profile)
    return [{"staff_id": str(row.staff_id), "staff_code": profiles[row.staff_id].staff_code,
        "date": row.work_date.isoformat(), "clock_in": row.clock_in, "clock_out": row.clock_out,
        "worked_hours": round(max(0, ((row.clock_out or row.clock_in) - row.clock_in).total_seconds()) / 3600, 2),
        "late_minutes": row.late_minutes, "early_departure_minutes": row.early_departure_minutes,
        "status": row.status} for row in rows] + [{"staff_id": str(row.staff_id), "staff_code": profiles[row.staff_id].staff_code,
        "date": row.absence_date.isoformat(), "clock_in": None, "clock_out": None, "worked_hours": 0,
        "late_minutes": 0, "early_departure_minutes": 0, "status": "absent", "reason": row.reason} for row in absences]


@router.post("/{organization_id}/absences")
def record_absence(organization_id: uuid.UUID, payload: dict, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    _authorize_staff_scope(db, current_user, organization_id, manage=True)
    from app.staff.attendance import AttendanceRecord, StaffAbsence
    try:
        staff_id = uuid.UUID(str(payload["staff_id"]))
        absence_date = date.fromisoformat(str(payload["date"]))
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=422, detail="staff_id and ISO date are required")
    if db.scalar(select(StaffProfile).where(StaffProfile.id == staff_id, StaffProfile.organization_id == organization_id, StaffProfile.is_active.is_(True))) is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    if db.scalar(select(AttendanceRecord).where(AttendanceRecord.organization_id == organization_id, AttendanceRecord.staff_id == staff_id, AttendanceRecord.work_date == absence_date)):
        raise HTTPException(status_code=409, detail="Attendance already exists for this date")
    if db.scalar(select(StaffAbsence).where(StaffAbsence.organization_id == organization_id, StaffAbsence.staff_id == staff_id, StaffAbsence.absence_date == absence_date)):
        raise HTTPException(status_code=409, detail="Absence is already recorded")
    absence = StaffAbsence(organization_id=organization_id, staff_id=staff_id, absence_date=absence_date,
        reason=str(payload.get("reason", "")).strip()[:300], created_by_user_id=uuid.UUID(str(current_user.user_id)))
    from app.audit.models import AuditLog
    import json
    db.add(absence)
    db.flush()
    db.add(AuditLog(organization_id=organization_id, user_id=uuid.UUID(str(current_user.user_id)), action="attendance.absence_recorded", entity_type="staff_absence", entity_id=absence.id, description="Staff absence recorded", metadata_json=json.dumps({"staff_id": str(staff_id), "date": absence_date.isoformat()})))
    db.commit()
    db.refresh(absence)
    return {"id": absence.id, "staff_id": staff_id, "date": absence_date, "status": "absent"}
