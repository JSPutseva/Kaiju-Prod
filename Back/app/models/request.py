from datetime import datetime

from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import REQUEST_STATUS, RequestStatus


class ResourceRequest(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
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

    status: Mapped[RequestStatus] = mapped_column(
        REQUEST_STATUS,
        nullable=False,
        default=RequestStatus.PENDING,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )