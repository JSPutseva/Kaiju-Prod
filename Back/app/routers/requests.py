from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.enums import RequestStatus
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.request import ResourceRequest
from app.models.resource_type import ResourceType
from app.models.role import UserRole
from app.models.user import User
from app.models.user_quarter import UserQuarter
from app.schemas import RequestDenyIn, ResourceRequestCreate, ResourceRequestOut
from app.services.transfer_validation import TransferValidator, retention_min
from app.websocket.manager import publish_event


router = APIRouter(
    prefix="/requests",
    tags=["Requests"],
)


@router.post(
    "",
    response_model=ResourceRequestOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
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

    # a QC only acts for their own quarter — either side of the request,
    # since they may be sending their own stock out or asking a neighbor to
    # send some in. An LC is scoped to their assigned quarters the same way.
    # A CD has city-wide authority and isn't restricted.
    requested_quarters = {payload.source_quarter_id, payload.destination_quarter_id}
    if current_user.role == UserRole.QC:
        if current_user.quarter_id not in requested_quarters:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "A QC can only create requests involving their own quarter.",
                },
            )
    elif current_user.role == UserRole.LC:
        lc_quarter_ids = {
            row.quarter_id
            for row in db.query(UserQuarter).filter(UserQuarter.user_id == current_user.id)
        }
        if not lc_quarter_ids & requested_quarters:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": "An LC can only create requests involving one of their assigned quarters.",
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
    # the /transfers/route preview enforces, kept in sync here. Irrelevant
    # for a requisition, which bypasses adjacency entirely.
    adjacent_surplus = {}
    neighbors = []
    if not payload.requisition:
        neighbor_names = TransferValidator.neighbors(destination_quarter.name)
        neighbors = db.scalars(
            select(Quarter).where(Quarter.name.in_(neighbor_names))
        ).all()
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
        requisition=payload.requisition,
        retention_override=payload.retention_override,
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

    # resolve the transit quarter the validator picked/accepted, by id,
    # so it survives past this request (the validator only deals in names)
    transit_via_id = None
    if decision.transit_via is not None:
        transit_quarter_row = db.scalar(
            select(Quarter).where(Quarter.name == decision.transit_via)
        )
        transit_via_id = transit_quarter_row.id if transit_quarter_row else None

    request = ResourceRequest(
        requester_id=current_user.id,
        source_quarter_id=payload.source_quarter_id,
        destination_quarter_id=payload.destination_quarter_id,
        resource_type_id=payload.resource_type_id,
        quantity=payload.quantity,
        requisition=payload.requisition,
        route_type=decision.route_type,
        transit_via_id=transit_via_id,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    await publish_event(
        "REQUEST_CREATED",
        {
            "id": request.id,
            "source_quarter_id": request.source_quarter_id,
            "destination_quarter_id": request.destination_quarter_id,
            "resource_type_id": request.resource_type_id,
            "quantity": request.quantity,
            "requisition": request.requisition,
            "route_type": request.route_type,
            "transit_via_id": request.transit_via_id,
            "status": request.status.value,
            "requester_id": request.requester_id,
        },
    )

    return request


@router.get(
    "",
    response_model=list[ResourceRequestOut],
)
def get_requests(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    # unfiltered on purpose: this is the city-wide audit trail (operational
    # calendar) as well as the QC/CD decision inbox — every quarter can see
    # who asked whom for what, even if only the source's QC/CD can act on it
    query = select(ResourceRequest).order_by(
        ResourceRequest.created_at.desc()
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


async def _get_pending_request(db: Session, request_id: int, current_user: User) -> ResourceRequest:
    # locked for the rest of this transaction: if two decisions on the same
    # request race (double-click, two tabs, two officers), the second one
    # blocks here until the first commits, then sees the now-decided status
    # below and cleanly 409s instead of both proceeding
    request = db.scalar(
        select(ResourceRequest).where(ResourceRequest.id == request_id).with_for_update()
    )

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "REQUEST_NOT_FOUND",
                "message": "Resource request not found.",
            },
        )

    # the source quarter's QC manages their own resources and decides on
    # incoming requests for them; a CD has full authority and can decide on
    # any of them
    is_source_qc = (
        current_user.role == UserRole.QC
        and current_user.quarter_id == request.source_quarter_id
    )
    if not (is_source_qc or current_user.role == UserRole.CD):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Only the source quarter's QC or a City Director can decide on this request.",
            },
        )

    if request.status != RequestStatus.PENDING:
        # someone else (or another tab/click) decided this first — surface it
        # as a live conflict, not just a silent error to the loser
        await publish_event(
            "REQUEST_CONFLICT",
            {
                "request_id": request.id,
                "attempted_by_id": current_user.id,
                "actual_status": request.status.value,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "REQUEST_ALREADY_DECIDED",
                "message": f"This request was already {request.status.value.lower()}.",
            },
        )

    return request


@router.patch(
    "/{request_id}/approve",
    response_model=ResourceRequestOut,
)
async def approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = await _get_pending_request(db, request_id, current_user)

    # locked so a second concurrent approval drawing from the same pool (a
    # different request, same source+resource) waits for this one to commit
    # and then re-checks against the up-to-date available_quantity below,
    # instead of both reading stale stock and over-committing it
    source_resource = db.scalar(
        select(QuarterResource)
        .where(
            QuarterResource.quarter_id == request.source_quarter_id,
            QuarterResource.resource_type_id == request.resource_type_id,
        )
        .with_for_update()
    )
    if source_resource is None or source_resource.available_quantity < request.quantity:
        await publish_event(
            "RESOURCE_CONFLICT",
            {
                "quarter_id": request.source_quarter_id,
                "resource_type_id": request.resource_type_id,
                "request_id": request.id,
                "reason": "INSUFFICIENT_RESOURCE",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INSUFFICIENT_RESOURCE",
                "message": "The source quarter no longer has enough available stock.",
            },
        )

    destination_resource = db.scalar(
        select(QuarterResource)
        .where(
            QuarterResource.quarter_id == request.destination_quarter_id,
            QuarterResource.resource_type_id == request.resource_type_id,
        )
        .with_for_update()
    )
    if destination_resource is None:
        destination_resource = QuarterResource(
            quarter_id=request.destination_quarter_id,
            resource_type_id=request.resource_type_id,
            initial_quantity=0,
            available_quantity=0,
        )
        db.add(destination_resource)

    source_resource.available_quantity -= request.quantity
    destination_resource.available_quantity += request.quantity
    # the destination now physically holds more stock than its original
    # allocation accounted for — grow its capacity to match, otherwise
    # available_quantity can exceed initial_quantity and violate the
    # quarter_resources_check constraint. The source's initial_quantity is
    # left untouched: its retention floor (30% of initial) shouldn't shrink
    # just because it lent resources out.
    destination_resource.initial_quantity += request.quantity

    request.status = RequestStatus.APPROVED
    request.decided_by_id = current_user.id
    request.decided_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)

    await publish_event(
        "REQUEST_APPROVED",
        {
            "id": request.id,
            "decided_by_id": request.decided_by_id,
            "decided_at": request.decided_at.isoformat(),
        },
    )
    await publish_event(
        "RESOURCE_UPDATE",
        {
            "quarter_id": source_resource.quarter_id,
            "resource_type_id": source_resource.resource_type_id,
            "available_quantity": source_resource.available_quantity,
            "reserved_quantity": source_resource.reserved_quantity,
            "reason": "REQUEST_APPROVED",
            "request_id": request.id,
        },
    )
    await publish_event(
        "RESOURCE_UPDATE",
        {
            "quarter_id": destination_resource.quarter_id,
            "resource_type_id": destination_resource.resource_type_id,
            "available_quantity": destination_resource.available_quantity,
            "reserved_quantity": destination_resource.reserved_quantity,
            "reason": "REQUEST_APPROVED",
            "request_id": request.id,
        },
    )

    return request


@router.patch(
    "/{request_id}/deny",
    response_model=ResourceRequestOut,
)
async def deny_request(
    request_id: int,
    payload: RequestDenyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = await _get_pending_request(db, request_id, current_user)

    request.status = RequestStatus.REJECTED
    request.rejection_reason = payload.reason
    request.decided_by_id = current_user.id
    request.decided_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)

    await publish_event(
        "REQUEST_DENIED",
        {
            "id": request.id,
            "requester_id": request.requester_id,
            "source_quarter_id": request.source_quarter_id,
            "destination_quarter_id": request.destination_quarter_id,
            "resource_type_id": request.resource_type_id,
            "quantity": request.quantity,
            "decided_by_id": request.decided_by_id,
            "decided_at": request.decided_at.isoformat(),
            "rejection_reason": request.rejection_reason,
        },
    )

    return request