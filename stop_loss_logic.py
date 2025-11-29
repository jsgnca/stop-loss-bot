# stop_loss_logic.py
from __future__ import annotations

import math
from typing import Dict, Set, Optional
from ib_insync import IB, MarketOrder, Ticker
from config import STOP_LOSS_PERCENT
from utils import get_open_option_positions, place_market_sell_order

# Track contracts we’ve already sent an exit for while that position is (or was) open
# conId -> orderId (or True)
active_exits: Dict[int, int | bool] = {}


def _current_open_sell_conids(ib: IB) -> Set[int]:
    conids: Set[int] = set()
    for t in ib.openTrades():
        try:
            if t.order.action == "SELL":
                conids.add(t.contract.conId)
        except Exception:
            continue
    return conids


def _prune_inactive_exits(ib: IB, open_conids: Set[int]) -> None:
    """
    Remove exit guards for contracts that no longer have an open position
    OR no longer have an open SELL order on the exchange.
    This allows re-entering the same contract later.
    """
    open_sell_conids = _current_open_sell_conids(ib)

    for conId in list(active_exits.keys()):
        if (conId not in open_conids) or (conId not in open_sell_conids):
            active_exits.pop(conId, None)


def _valid_price(x: Optional[float]) -> bool:
    """True if x is a usable price (not None/NaN/inf and > 0)."""
    if x is None:
        return False
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return False
    return x > 0.0


def _get_reliable_bid(ib: IB, contract, retries: int = 3, pause_s: float = 0.4) -> Optional[float]:
    """
    Request streaming market data and try a few times for a valid bid.
    Uses ib.sleep() so the event loop keeps pumping.
    """
    ticker: Ticker = ib.reqMktData(contract, "", False, False)
    bid: Optional[float] = None
    try:
        for _ in range(retries):
            ib.sleep(pause_s)
            if _valid_price(ticker.bid):
                bid = float(ticker.bid)
                break
    finally:
        # Cancel subscription to avoid leaking reqs
        ib.cancelMktData(contract)
    return bid


def monitor_all_positions(ib: IB, logger) -> None:
    """
    Single-pass monitor:
      - Sync open option positions
      - Prune duplicate-exit latches for closed positions / no-open-SELL
      - Evaluate stop-loss for each position
      - Place exactly one MARKET exit when triggered
      - Re-check live qty just before sending to avoid oversells
    Intended to be called ~once per second from main loop.
    """
    # If disconnected, do nothing this tick
    if not ib.isConnected():
        logger.warning("IBKR disconnected; skipping this tick.")
        return

    # Pull latest positions and clean up latches
    positions = get_open_option_positions(ib)
    open_conids = {p.contract.conId for p in positions}
    _prune_inactive_exits(ib, open_conids)

    if not positions:
        logger.debug("No open option positions.")
        return

    for pos in positions:
        contract = pos.contract
        conId = contract.conId
        symbol = getattr(contract, "localSymbol", str(contract))

        qty_abs = float(abs(pos.position))
        if qty_abs <= 0:
            continue

        # Debounce: if we already fired an exit for this still-open position, skip
        if conId in active_exits:
            continue

        # Get bid with retries and validate it
        bid = _get_reliable_bid(ib, contract, retries=3, pause_s=0.4)
        if not _valid_price(bid):
            logger.warning(f"{symbol}: Invalid bid ({bid}); skipping until next tick.")
            continue

        # IBKR avgCost for options is commonly 100x contract price; divide to get per-contract price
        cost_basis = float(pos.avgCost) / 100.0
        if not _valid_price(cost_basis):
            logger.warning(f"{symbol}: Invalid cost basis ({cost_basis}); skipping.")
            continue

        loss_pct = ((bid - cost_basis) / cost_basis) * 100.0
        # Guard against NaN/inf in loss_pct
        if not (isinstance(loss_pct, float) and math.isfinite(loss_pct)):
            logger.warning(f"{symbol}: Computed invalid loss_pct ({loss_pct}); skipping.")
            continue

        logger.info(
            f"Checking {symbol} | Qty: {qty_abs:.0f} | Cost: {cost_basis:.2f} | "
            f"Bid: {bid:.2f} | Loss: {loss_pct:.2f}%"
        )

        # Hold if inside loss limit
        if loss_pct > -float(STOP_LOSS_PERCENT):
            logger.debug(f"Holding {symbol} | Loss {loss_pct:.2f}% within limit.")
            continue

        logger.warning(f"STOP-LOSS TRIGGERED for {symbol} | Loss: {loss_pct:.2f}%")

        # Final duplicate safety: if an open SELL already exists, mark and skip
        if any(t.contract.conId == conId and t.order.action == "SELL" for t in ib.openTrades()):
            active_exits[conId] = True
            logger.info(f"Skipped duplicate exit for {symbol}: SELL already open.")
            continue

        # Re-read the live position to avoid overselling (in case fills/partials just changed it)
        live_qty = 0.0
        for p in ib.positions():
            if p.contract.conId == conId:
                live_qty = float(p.position)
                break

        close_qty = max(0.0, live_qty)
        if close_qty <= 0.0:
            # Position already closed between checks
            active_exits[conId] = True
            logger.info(f"{symbol}: Position already closed; no sell placed.")
            continue

        # Place MARKET exit for the *current* live size
        trade = place_market_sell_order(ib, contract, close_qty, logger)
        if trade is None:
            # If placeOrder failed, do not set the guard; allow retry next tick
            continue

        active_exits[conId] = getattr(trade.order, "orderId", True)

        # Briefly wait for order status updates so we don't re-fire immediately
        deadline_seconds = 2.0
        waited = 0.0
        step = 0.1
        while waited < deadline_seconds:
            ib.sleep(step)
            waited += step
            st = getattr(trade.orderStatus, "status", None)
            if st in ("Filled", "Inactive", "Cancelled"):
                break

        # After waiting, prune guards if the position truly closed / no open SELL remains
        positions_after = get_open_option_positions(ib)
        open_after_conids = {p.contract.conId for p in positions_after}
        _prune_inactive_exits(ib, open_after_conids)
