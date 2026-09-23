import enum

from sqlalchemy import Enum as SAEnum


class RouteType(str, enum.Enum):
    LAND = "LAND"
    MARITIME = "MARITIME"
    TRANSIT = "TRANSIT"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class TransferStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ReservationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


def _pg_enum(
    python_enum: type[enum.Enum],
    pg_name: str,
) -> SAEnum:
    return SAEnum(
        python_enum,
        name=pg_name,
        create_type=False,
        values_callable=lambda e: [member.value for member in e],
    )


ROUTE_TYPE = _pg_enum(RouteType, "route_type")
REQUEST_STATUS = _pg_enum(RequestStatus, "request_status")
TRANSFER_STATUS = _pg_enum(TransferStatus, "transfer_status")
RESERVATION_STATUS = _pg_enum(
    ReservationStatus,
    "reservation_status",
)