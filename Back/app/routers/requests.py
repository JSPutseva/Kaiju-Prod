from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.request import ResourceRequest
from app.models.resource_type import ResourceType
from app.models.user import User
from app.schemas import ResourceRequestCreate, ResourceRequestOut
from app.services.transfer_validation import TransferValidator, retention_min


router = APIRouter(
    prefix="/requests",
    tags=["Requests"],
)


@router.post(
    "",
    response_model=ResourceRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    payload: ResourceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NO_ROLE_ASSIGNED",
                "message": "Your account has no role assigned yet.",
            },
        )

    if payload.source_quarter_id == payload.destination_quarter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SAME_QUARTER",
                "message": "Source and destination quarters must be different.",
            },
        )

    source_quarter = db.get(Quarter, payload.source_quarter_id)
    if source_quarter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "SOURCE_QUARTER_NOT_FOUND",
                "message": "Source quarter not found.",
            },
        )

    destination_quarter = db.get(Quarter, payload.destination_quarter_id)
    if destination_quarter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DESTINATION_QUARTER_NOT_FOUND",
                "message": "Destination quarter not found.",
            },
        )

    resource_type = db.get(
        ResourceType,
        payload.resource_type_id,
    )
    if resource_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_TYPE_NOT_FOUND",
                "message": "Resource type not found.",
            },
        )

    source_resource = db.scalar(
        select(QuarterResource).where(
            QuarterResource.quarter_id == payload.source_quarter_id,
            QuarterResource.resource_type_id == payload.resource_type_id,
        )
    )

    if source_resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_AVAILABLE",
                "message": "No resource stock exists in the source quarter.",
            },
        )

    transit_via_name = None
    if payload.transit_via is not None:
        transit_quarter = db.get(Quarter, payload.transit_via)
        if transit_quarter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TRANSIT_QUARTER_NOT_FOUND",
                    "message": "Transit quarter not found.",
                },
            )
        transit_via_name = transit_quarter.name

    # surplus of quarters adjacent to the destination, by name — same rule
    # the /transfers/route preview enforces, kept in sync here.
    neighbor_names = TransferValidator.neighbors(destination_quarter.name)
    neighbors = db.scalars(
        select(Quarter).where(Quarter.name.in_(neighbor_names))
    ).all()
    adjacent_surplus = {}
    if neighbors:
        rows = db.scalars(
            select(QuarterResource).where(
                QuarterResource.quarter_id.in_([q.id for q in neighbors]),
                QuarterResource.resource_type_id == payload.resource_type_id,
            )
        ).all()
        names_by_id = {q.id: q.name for q in neighbors}
        adjacent_surplus = {
            names_by_id[row.quarter_id]: max(
                row.available_quantity - retention_min(row.initial_quantity), 0
            )
            for row in rows
        }

    validator = TransferValidator()
    decision = validator.validate(
        user_role=current_user.role,
        source_quarter=source_quarter.name,
        destination_quarter=destination_quarter.name,
        disaster_level=source_quarter.disaster_level,
        quantity=payload.quantity,
        initial_quantity=source_resource.initial_quantity,
        available_quantity=source_resource.available_quantity,
        maritime=payload.prefer_maritime,
        transit_via=transit_via_name,
        adjacent_surplus=adjacent_surplus,
        # no persisted approval flow yet — same placeholder the route
        # preview uses; a real request still starts out PENDING below.
        qc_approved=True,
        lc_approved=True,
        cd_approved=True,
    )

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": decision.reason.value,
                "message": decision.message,
            },
        )

    request = ResourceRequest(
        requester_id=current_user.id,
        source_quarter_id=payload.source_quarter_id,
        destination_quarter_id=payload.destination_quarter_id,
        resource_type_id=payload.resource_type_id,
        quantity=payload.quantity,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return request


@router.get(
    "",
    response_model=list[ResourceRequestOut],
)
def get_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ResourceRequest).order_by(
        ResourceRequest.created_at.desc()
    )

    if current_user.role == "QC" and current_user.quarter_id is not None:
        query = query.where(
            ResourceRequest.destination_quarter_id
            == current_user.quarter_id
        )

    return db.scalars(query).all()


@router.get(
    "/{request_id}",
    response_model=ResourceRequestOut,
)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    request = db.get(ResourceRequest, request_id)

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REQUEST_NOT_FOUND",
                "message": "Resource request not found.",
            },
        )

    return request