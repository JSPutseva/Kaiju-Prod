from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class QuarterResource(Base):
    __tablename__ = "quarter_resources"

    __table_args__ = (
        UniqueConstraint(
            "quarter_id",
            "resource_type_id",
            name="uq_quarter_resource",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"),
        nullable=False,
    )

    resource_type_id: Mapped[int] = mapped_column(
        ForeignKey("resource_types.id", ondelete="CASCADE"),
        nullable=False,
    )

    initial_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    available_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )