from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import RESERVATION_STATUS, ReservationStatus


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="RESTRICT"),
        nullable=False,
    )

    resource_type_id: Mapped[int] = mapped_column(
        ForeignKey("resource_types.id", ondelete="RESTRICT"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    status: Mapped[ReservationStatus] = mapped_column(
        RESERVATION_STATUS,
        nullable=False,
        default=ReservationStatus.PENDING,
    )

    start_at: Mapped[datetime] = mapped_column(
        nullable=False,
    )

    end_at: Mapped[datetime] = mapped_column(
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )