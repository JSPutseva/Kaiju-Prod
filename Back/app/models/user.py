from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.role import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    role: Mapped[UserRole | None] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=True,
    )

    quarter_id: Mapped[int | None] = mapped_column(
        ForeignKey("quarters.id"),
        nullable=True,
    )