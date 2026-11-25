"""British auction automatic extension logic.

Three trigger strategies:
  BID_RECEIVED      - any valid bid inside the trigger window extends.
  ANY_RANK_CHANGE   - a bid inside the window that changes any supplier's rank.
  L1_RANK_CHANGE    - a bid inside the window that changes the L1 identity.

New close time = MIN(current_close_time + extension_duration, forced_close_time).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models.auction_config import TriggerType
from ..models.rfq import RFQ
from .ranking import RankedBid, rank_map


@dataclass
class ExtensionResult:
    extended: bool
    reason: str | None
    previous_close_time: datetime | None
    new_close_time: datetime | None


def in_trigger_window(rfq: RFQ, now: datetime) -> bool:
    cfg = rfq.auction_config
    window_start = rfq.current_close_time - timedelta(minutes=cfg.trigger_window_minutes)
    return window_start <= now < rfq.current_close_time


def evaluate_extension(
    rfq: RFQ,
    before: list[RankedBid],
    after: list[RankedBid],
    now: datetime,
) -> ExtensionResult:
    """Decide whether the auction extends after an accepted bid."""
    cfg = rfq.auction_config
    if cfg is None:
        return ExtensionResult(False, None, None, None)
    if not in_trigger_window(rfq, now):
        return ExtensionResult(False, None, None, None)
    if now >= rfq.forced_close_time or rfq.current_close_time >= rfq.forced_close_time:
        return ExtensionResult(False, None, None, None)

    trigger = cfg.trigger_type
    qualifies, reason = False, None
    if trigger == TriggerType.BID_RECEIVED:
        qualifies, reason = True, "A valid bid was received within the trigger window"
    elif trigger == TriggerType.ANY_RANK_CHANGE:
        if rank_map(before) != rank_map(after):
            qualifies, reason = True, "A bid caused a supplier ranking change within the trigger window"
    elif trigger == TriggerType.L1_RANK_CHANGE:
        l1_before = before[0].supplier_id if before else None
        l1_after = after[0].supplier_id if after else None
        if l1_after is not None and l1_after != l1_before:
            qualifies, reason = True, "The lowest bidder (L1) changed within the trigger window"

    if not qualifies:
        return ExtensionResult(False, None, None, None)

    new_close = min(
        rfq.current_close_time + timedelta(minutes=cfg.extension_duration_minutes),
        rfq.forced_close_time,
    )
    if new_close <= rfq.current_close_time:
        return ExtensionResult(False, None, None, None)
    return ExtensionResult(True, reason, rfq.current_close_time, new_close)
