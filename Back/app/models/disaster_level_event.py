from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DisasterLevelEvent(Base):
    __tablename__ = "disaster_level_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"),
        nullable=False,
    )

    level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    changed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
