import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .user import utcnow


class ActivityEventType(str, enum.Enum):
    RFQ_CREATED = "RFQ_CREATED"
    RFQ_UPDATED = "RFQ_UPDATED"
    SUPPLIER_JOINED = "SUPPLIER_JOINED"
    QUOTE_SUBMITTED = "QUOTE_SUBMITTED"
    BID_RECEIVED = "BID_RECEIVED"
    RANK_CHANGED = "RANK_CHANGED"
    AUCTION_EXTENDED = "AUCTION_EXTENDED"
    AUCTION_STARTED = "AUCTION_STARTED"
    AUCTION_CLOSED = "AUCTION_CLOSED"
    AUCTION_FORCE_CLOSED = "AUCTION_FORCE_CLOSED"


class ActivityLog(Base):
    __tablename__ = "auction_activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    rfq_id: Mapped[int] = mapped_column(
        ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[ActivityEventType] = mapped_column(
        Enum(ActivityEventType, name="activity_event_type"), nullable=False
    )
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    rfq: Mapped["RFQ"] = relationship(back_populates="activity_logs")

    __table_args__ = (
        Index("ix_activity_rfq_time", "rfq_id", "created_at"),
    )
