from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.role import UserRole
from app.models.user import User
from app.models.user_quarter import UserQuarter
from app.schemas import RoleAssignIn, UserOut

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_out(user: User, quarter_ids: list[int]) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        quarter_ids=quarter_ids,
    )


def _quarter_ids_by_user(db: Session, user_ids: list[int]) -> dict[int, list[int]]:
    by_user: dict[int, list[int]] = {uid: [] for uid in user_ids}
    if not user_ids:
        return by_user
    rows = db.query(UserQuarter).filter(UserQuarter.user_id.in_(user_ids)).all()
    for row in rows:
        by_user[row.user_id].append(row.quarter_id)
    return by_user


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    all_users = db.query(User).order_by(User.name).all()
    quarter_ids = _quarter_ids_by_user(db, [u.id for u in all_users])
    return [_to_user_out(u, quarter_ids[u.id]) for u in all_users]


@router.patch("/{user_id}/role", response_model=UserOut)
def assign_role(
    user_id: int,
    payload: RoleAssignIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # bootstrapping: with no CD yet, anyone can assign the first one;
    # after that, only an existing CD can assign roles.
    any_cd_exists = db.query(User).filter(User.role == UserRole.CD).first() is not None
    if any_cd_exists and current_user.role != UserRole.CD:
        raise HTTPException(
            status_code=403,
            detail="Only a City Director can assign roles.",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    # QC is scoped to exactly one quarter; LC can span several; CD is city-wide.
    if payload.role == UserRole.QC and len(payload.quarter_ids) > 1:
        raise HTTPException(
            status_code=400,
            detail="A Quarter Coordinator can only be assigned one quarter.",
        )

    user.role = payload.role
    # keep the legacy single quarter_id column (used by /auth/me) as the first pick
    user.quarter_id = payload.quarter_ids[0] if payload.quarter_ids else None

    db.query(UserQuarter).filter(UserQuarter.user_id == user_id).delete()
    for quarter_id in dict.fromkeys(payload.quarter_ids):  # de-dupe, keep order
        db.add(UserQuarter(user_id=user_id, quarter_id=quarter_id))

    db.commit()
    db.refresh(user)

    return _to_user_out(user, list(dict.fromkeys(payload.quarter_ids)))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.CD:
        raise HTTPException(
            status_code=403,
            detail="Only a City Director can delete accounts.",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You can't delete your own account.",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.role == UserRole.CD:
        other_cd_exists = (
            db.query(User)
            .filter(User.role == UserRole.CD, User.id != user_id)
            .first()
            is not None
        )
        if not other_cd_exists:
            raise HTTPException(
                status_code=400,
                detail="Can't delete the last City Director.",
            )

    db.query(UserQuarter).filter(UserQuarter.user_id == user_id).delete()
    db.delete(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Can't delete this user: they have existing requests or reservations.",
        )
