from sqlalchemy import Boolean, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Quarter(Base):
    __tablename__ = "quarters"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    disaster_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
    )

    sea_access: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
