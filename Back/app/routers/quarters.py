from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.resource_type import ResourceType
from app.models.role import UserRole
from app.models.user import User
from app.schemas import (
    DisasterLevelOut,
    DisasterLevelUpdate,
    QuarterOut,
    QuarterResourceOut,
)
from app.services.disaster_level import (
    DISASTER_LEVELS,
    get_disaster_level_definition,
)
from app.services.transfer_validation import retention_min


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


@router.get(
    "/disaster-levels",
    response_model=list[DisasterLevelOut],
)
def get_disaster_levels(
    _current_user: User = Depends(get_current_user),
):
    return [
        DisasterLevelOut(
            level=level.value,
            code=definition["code"],
            name=definition["name"],
            description=definition["description"],
        )
        for level, definition in DISASTER_LEVELS.items()
    ]


@router.patch(
    "/{quarter_id}/disaster-level",
    response_model=QuarterOut,
)
def update_disaster_level(
    quarter_id: int,
    payload: DisasterLevelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.CD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the City Director can change the disaster level",
        )

    quarter = db.get(
        Quarter,
        quarter_id,
    )

    if quarter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarter not found",
        )

    try:
        get_disaster_level_definition(payload.level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid disaster level",
        )

    quarter.disaster_level = payload.level

    db.commit()
    db.refresh(quarter)

    return quarter


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