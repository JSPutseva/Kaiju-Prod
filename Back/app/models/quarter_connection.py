from sqlalchemy import Boolean, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QuarterConnection(Base):
    __tablename__ = "quarter_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    from_quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"),
        nullable=False,
    )

    to_quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "from_quarter_id",
            "to_quarter_id",
            name="uq_quarter_connection",
        ),
    )