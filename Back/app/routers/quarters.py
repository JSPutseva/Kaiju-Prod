from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.disaster_level_event import DisasterLevelEvent
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.resource_type import ResourceType
from app.models.role import UserRole
from app.models.user import User
from app.schemas import (
    DisasterLevelEventOut,
    DisasterLevelSetIn,
    QuarterOut,
    QuarterResourceOut,
)
from app.services.transfer_validation import retention_min
from app.websocket.manager import publish_event

LEVEL_NAMES = {
    1: "Watch",
    2: "Alert",
    3: "Emergency",
    4: "Critical",
    5: "Catastrophic",
}


router = APIRouter(
    prefix="/quarters",
    tags=["Quarters"],
)


@router.get(
    "",
    response_model=list[QuarterOut],
)
def get_quarters(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Quarter).order_by(Quarter.id)
    ).all()


@router.patch(
    "/disaster-level",
    response_model=list[QuarterOut],
)
async def set_disaster_level(
    payload: DisasterLevelSetIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # demo/test trigger for the defense: no rule in the spec dictates how
    # escalation is triggered, only that a CD has the authority to do it
    # (full authority, city-wide) and that it goes through an inspectable
    # API route rather than e.g. direct DB access.
    if current_user.role != UserRole.CD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Only a City Director can change disaster levels.",
            },
        )

    quarter_ids = list(dict.fromkeys(payload.quarter_ids))  # de-dupe, keep order
    quarters = db.scalars(
        select(Quarter).where(Quarter.id.in_(quarter_ids))
    ).all()

    missing = set(quarter_ids) - {q.id for q in quarters}
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "QUARTER_NOT_FOUND",
                "message": f"Quarter(s) not found: {sorted(missing)}",
            },
        )

    for quarter in quarters:
        quarter.disaster_level = payload.level
        db.add(
            DisasterLevelEvent(
                quarter_id=quarter.id,
                level=payload.level,
                changed_by_id=current_user.id,
            )
        )

    db.commit()

    level_name = LEVEL_NAMES.get(payload.level, str(payload.level))
    for quarter in quarters:
        db.refresh(quarter)
        await publish_event(
            "LEVEL_CHANGED",
            {
                "quarter_id": quarter.id,
                "quarter_name": quarter.name,
                "level": quarter.disaster_level,
                "level_name": level_name,
                "changed_by_id": current_user.id,
                "label": f"{quarter.name} → Level {quarter.disaster_level} ({level_name})",
            },
        )

    return quarters


@router.get(
    "/disaster-level-events",
    response_model=list[DisasterLevelEventOut],
)
def get_disaster_level_events(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    # recent history, so a fresh page load can show past attacks/level
    # changes too, not just ones broadcast live while connected
    return db.scalars(
        select(DisasterLevelEvent)
        .order_by(DisasterLevelEvent.created_at.desc())
        .limit(50)
    ).all()


@router.get(
    "/{quarter_id}/resources",
    response_model=list[QuarterResourceOut],
)
def get_quarter_resources(
    quarter_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    quarter = db.get(
        Quarter,
        quarter_id,
    )

    if quarter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarter not found",
        )

    rows = db.execute(
        select(
            QuarterResource,
            ResourceType.name,
        )
        .join(
            ResourceType,
            ResourceType.id == QuarterResource.resource_type_id,
        )
        .where(
            QuarterResource.quarter_id == quarter_id,
        )
        .order_by(
            ResourceType.name,
        )
    ).all()

    return [
        QuarterResourceOut(
            id=resource.id,
            quarter_id=resource.quarter_id,
            resource_type_id=resource.resource_type_id,
            resource_name=resource_name,
            initial_quantity=resource.initial_quantity,
            available_quantity=resource.available_quantity,
            reserved_quantity=resource.reserved_quantity,
            retention_min=retention_min(
                resource.initial_quantity,
            ),
        )
        for resource, resource_name in rows
    ]
