from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.resource_type import ResourceType
from app.models.user import User
from app.schemas import ResourceTypeOut

router = APIRouter(prefix="/resource-types", tags=["Resource types"])


@router.get("", response_model=list[ResourceTypeOut])
def list_resource_types(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return db.scalars(select(ResourceType).order_by(ResourceType.name)).all()
