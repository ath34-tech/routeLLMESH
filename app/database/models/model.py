from sqlalchemy import Boolean
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Model(Base, TimestampMixin):

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id"),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    context_window: Mapped[int] = mapped_column(
        Integer,
        default=128000,
    )

    input_cost: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    output_cost: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    fallback_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    supports_stream: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    supports_tools: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    supports_vision: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    provider = relationship(
        "Provider",
        back_populates="models",
    )