from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.enums import ReservationStatus
from app.models.quarter import Quarter
from app.models.quarter_resource import QuarterResource
from app.models.reservation import Reservation
from app.models.resource_type import ResourceType
from app.models.role import UserRole
from app.models.user import User
from app.schemas import ReservationCreate, ReservationOut
from app.services.transfer_validation import retention_min
from app.websocket.manager import publish_event


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


@router.post(
    "",
    response_model=ReservationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # rules: reservations are QC-only, within the QC's own quarter, from
    # disaster level 2 (Alert) up.
    if current_user.role != UserRole.QC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Only a Quarter Coordinator can reserve resources.",
            },
        )

    if current_user.quarter_id != payload.quarter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "A Quarter Coordinator can only reserve within their own quarter.",
            },
        )

    if payload.end_at <= payload.start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_RESERVATION_DATES",
                "message": "end_at must be after start_at.",
            },
        )

    quarter = db.get(Quarter, payload.quarter_id)

    if quarter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "QUARTER_NOT_FOUND",
                "message": "Quarter not found.",
            },
        )

    if quarter.disaster_level < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DISASTER_LEVEL_TOO_LOW",
                "message": "Reservations require at least disaster level 2 (Alert).",
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

    # locked so two officers reserving from the same pool at the same moment
    # serialize instead of both reading stale stock and over-committing it
    resource = db.scalar(
        select(QuarterResource)
        .where(
            QuarterResource.quarter_id == payload.quarter_id,
            QuarterResource.resource_type_id
            == payload.resource_type_id,
        )
        .with_for_update()
    )

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESOURCE_NOT_AVAILABLE",
                "message": "No resource stock exists in this quarter.",
            },
        )

    if resource.available_quantity < payload.quantity:
        await publish_event(
            "RESOURCE_CONFLICT",
            {
                "quarter_id": payload.quarter_id,
                "resource_type_id": payload.resource_type_id,
                "attempted_by_id": current_user.id,
                "reason": "INSUFFICIENT_RESOURCE",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INSUFFICIENT_RESOURCE",
                "message": "Not enough available resources for this reservation.",
            },
        )

    minimum_retention = retention_min(resource.initial_quantity)
    remaining = resource.available_quantity - payload.quantity
    if remaining < minimum_retention:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "RETENTION_LIMIT",
                "message": (
                    f"Reserving {payload.quantity} would leave {remaining}, below the "
                    f"retention floor of {minimum_retention}."
                ),
            },
        )

    resource.available_quantity -= payload.quantity
    resource.reserved_quantity += payload.quantity

    reservation = Reservation(
        quarter_id=payload.quarter_id,
        resource_type_id=payload.resource_type_id,
        user_id=current_user.id,
        quantity=payload.quantity,
        status=ReservationStatus.APPROVED,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    await publish_event(
        "RESOURCE_UPDATE",
        {
            "quarter_id": resource.quarter_id,
            "resource_type_id": resource.resource_type_id,
            "available_quantity": resource.available_quantity,
            "reserved_quantity": resource.reserved_quantity,
            "reason": "RESERVATION_CREATED",
            "reservation_id": reservation.id,
        },
    )

    return reservation


@router.get(
    "",
    response_model=list[ReservationOut],
)
def get_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Reservation).order_by(
        Reservation.start_at.asc()
    )

    if current_user.role == "QC" and current_user.quarter_id is not None:
        query = query.where(
            Reservation.quarter_id == current_user.quarter_id
        )
    elif current_user.role not in {"LC", "CD"}:
        query = query.where(
            Reservation.user_id == current_user.id
        )

    return db.scalars(query).all()


@router.delete(
    "/{reservation_id}",
    response_model=ReservationOut,
)
async def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation = db.get(
        Reservation,
        reservation_id,
    )

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESERVATION_NOT_FOUND",
                "message": "Reservation not found.",
            },
        )

    if reservation.status in {
        ReservationStatus.CANCELLED,
        ReservationStatus.COMPLETED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "RESERVATION_ALREADY_CLOSED",
                "message": "This reservation can no longer be cancelled.",
            },
        )

    if (
        reservation.user_id != current_user.id
        and current_user.role not in {"LC", "CD"}
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "RESERVATION_FORBIDDEN",
                "message": "You cannot cancel this reservation.",
            },
        )

    resource = db.scalar(
        select(QuarterResource)
        .where(
            QuarterResource.quarter_id == reservation.quarter_id,
            QuarterResource.resource_type_id
            == reservation.resource_type_id,
        )
        .with_for_update()
    )

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "RESOURCE_STOCK_MISSING",
                "message": "The resource stock record no longer exists.",
            },
        )

    resource.available_quantity += reservation.quantity
    resource.reserved_quantity -= reservation.quantity

    reservation.status = ReservationStatus.CANCELLED

    db.commit()
    db.refresh(reservation)

    await publish_event(
        "RESOURCE_UPDATE",
        {
            "quarter_id": resource.quarter_id,
            "resource_type_id": resource.resource_type_id,
            "available_quantity": resource.available_quantity,
            "reserved_quantity": resource.reserved_quantity,
            "reason": "RESERVATION_CANCELLED",
            "reservation_id": reservation.id,
        },
    )

    return reservation