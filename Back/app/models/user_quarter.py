from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# LC's multi-quarter scope: one row per (user, quarter) they're assigned to.
class UserQuarter(Base):
    __tablename__ = "user_quarters"
    __table_args__ = (UniqueConstraint("user_id", "quarter_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    quarter_id: Mapped[int] = mapped_column(
        ForeignKey("quarters.id", ondelete="CASCADE"), nullable=False
    )
