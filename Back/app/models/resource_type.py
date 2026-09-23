from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResourceType(Base):
    __tablename__ = "resource_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )