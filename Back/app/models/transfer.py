from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import (
    ROUTE_TYPE,
    TRANSFER_STATUS,
    RouteType,
    TransferStatus,
)


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    request_id: Mapped[int] = mapped_column(
        ForeignKey("requests.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )

    source_quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="RESTRICT"),
        nullable=False,
    )

    destination_quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="RESTRICT"),
        nullable=False,
    )

    resource_type_id: Mapped[int] = mapped_column(
        ForeignKey("resource_types.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    route_type: Mapped[RouteType] = mapped_column(
        ROUTE_TYPE,
        nullable=False,
    )

    status: Mapped[TransferStatus] = mapped_column(
        TRANSFER_STATUS,
        nullable=False,
        default=TransferStatus.PENDING,
    )

    departure_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )