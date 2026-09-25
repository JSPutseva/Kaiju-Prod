from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, func
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

    # a CD-requisitioned move, bypassing adjacency — distinct from a regular
    # QC/LC transfer request for display/audit purposes
    requisition: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # route chosen at creation time — kept for audit/display, since the
    # validator only computes this transiently otherwise
    route_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    transit_via_id: Mapped[int | None] = mapped_column(
        ForeignKey("quarters.id", ondelete="SET NULL"),
        nullable=True,
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

    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    decided_at: Mapped[datetime | None] = mapped_column(
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