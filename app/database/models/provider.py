from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Provider(Base, TimestampMixin):

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    api_key: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    base_url: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    adapter: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    models = relationship(
        "Model",
        back_populates="provider",
        cascade="all, delete-orphan",
    )