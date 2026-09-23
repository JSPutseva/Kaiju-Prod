from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.user import User
from app.schemas import RouteDecisionOut, RouteTransferIn
from app.services.transfer_permissions import (
    TransferAction,
    TransferPermissionService,
)
from app.services.transfer_validation import TransferValidator, retention_min


router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("/route", response_model=RouteDecisionOut)
def route_transfer(
    payload: RouteTransferIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role is None:
        raise HTTPException(
            status_code=403,
            detail="Your account has no role assigned yet.",
        )

    quarters = {
        quarter.id: quarter
        for quarter in db.query(Quarter).all()
    }

    source = quarters.get(payload.source_quarter_id)
    destination = quarters.get(payload.destination_quarter_id)

    if source is None or destination is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown quarter.",
        )

    source_qr = (
        db.query(QuarterResource)
        .filter_by(
            quarter_id=payload.source_quarter_id,
            resource_type_id=payload.resource_type_id,
        )
        .first()
    )

    if source_qr is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No stock record for that source quarter "
                "and resource type."
            ),
        )

    # ---------------------------------------------------------
    # Permission matrix
    # ---------------------------------------------------------
    #
    # Every transfer request starts as an
    # "adjacent transfer request".
    #
    # A request involving an intermediate quarter additionally
    # requires the permission to organize transit.
    #
    # The authenticated user's role comes from the JWT/database.
    # The frontend cannot choose or override it.
    # ---------------------------------------------------------

    request_permission = TransferPermissionService.check(
        role=current_user.role,
        disaster_level=source.disaster_level,
        action=TransferAction.REQUEST_ADJACENT_TRANSFER,
    )

    if not request_permission.allowed:
        raise HTTPException(
            status_code=403,
            detail=request_permission.message,
        )

    transit_via_name = None

    if payload.transit_via is not None:
        transit_quarter = quarters.get(payload.transit_via)

        if transit_quarter is None:
            raise HTTPException(
                status_code=404,
                detail="Unknown transit quarter.",
            )

        transit_permission = TransferPermissionService.check(
            role=current_user.role,
            disaster_level=source.disaster_level,
            action=TransferAction.ORGANIZE_TRANSIT,
        )

        if not transit_permission.allowed:
            raise HTTPException(
                status_code=403,
                detail=transit_permission.message,
            )

        transit_via_name = transit_quarter.name

    neighbor_names = TransferValidator.neighbors(
        destination.name
    )

    neighbor_ids = {
        quarter.id: quarter.name
        for quarter in quarters.values()
        if quarter.name in neighbor_names
    }

    adjacent_surplus = {}

    if neighbor_ids:
        rows = (
            db.query(QuarterResource)
            .filter(
                QuarterResource.quarter_id.in_(neighbor_ids.keys()),
                QuarterResource.resource_type_id
                == payload.resource_type_id,
            )
            .all()
        )

        adjacent_surplus = {
            neighbor_ids[row.quarter_id]: max(
                row.available_quantity
                - retention_min(row.initial_quantity),
                0,
            )
            for row in rows
        }

    validator = TransferValidator()

    decision = validator.validate(
        user_role=current_user.role,
        source_quarter=source.name,
        destination_quarter=destination.name,
        disaster_level=source.disaster_level,
        quantity=payload.quantity,
        initial_quantity=source_qr.initial_quantity,
        available_quantity=source_qr.available_quantity,
        maritime=payload.prefer_maritime,
        transit_via=transit_via_name,
        adjacent_surplus=adjacent_surplus,

        # /route is currently a route-preview/validation endpoint.
        # It does not persist or execute the transfer, so there is
        # no separate approval workflow attached to this endpoint.
        #
        # Permission to request the transfer has already been
        # checked above.
        qc_approved=True,
        lc_approved=True,
        cd_approved=True,
    )

    transit_via_id = None

    if decision.transit_via is not None:
        transit_quarter = next(
            (
                quarter
                for quarter in quarters.values()
                if quarter.name == decision.transit_via
            ),
            None,
        )

        if transit_quarter is not None:
            transit_via_id = transit_quarter.id

    return RouteDecisionOut(
        ok=decision.allowed,
        route_type=decision.route_type,
        transit_via=transit_via_id,
        deprioritized_behind_xeno=decision.deprioritized_behind_xeno,
        reason=decision.reason.value,
        message=decision.message,
    )