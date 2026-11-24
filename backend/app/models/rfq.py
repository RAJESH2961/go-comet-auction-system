import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .user import utcnow


class RFQStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    FORCE_CLOSED = "FORCE_CLOSED"


class RFQ(Base):
    __tablename__ = "rfqs"

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    pickup_location: Mapped[str | None] = mapped_column(String(300))
    destination_location: Mapped[str | None] = mapped_column(String(300))
    service_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    bid_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bid_close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    forced_close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[RFQStatus] = mapped_column(
        Enum(RFQStatus, name="rfq_status"), default=RFQStatus.UPCOMING, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    buyer: Mapped["User"] = relationship(back_populates="rfqs")
    auction_config: Mapped["AuctionConfig"] = relationship(
        back_populates="rfq", uselist=False, cascade="all, delete-orphan"
    )
    quotes: Mapped[list["SupplierQuote"]] = relationship(back_populates="rfq", cascade="all, delete-orphan")
    bids: Mapped[list["Bid"]] = relationship(back_populates="rfq", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="rfq", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_rfqs_close_time", "current_close_time"),
    )
