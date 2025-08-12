import time
from ib_insync import IB
from config import STOP_LOSS_PERCENT
from utils import get_open_option_positions, place_limit_sell_order, place_market_sell_order

# Track contracts we’ve already sent an exit for this *open* position
# conId -> orderId (or True)
active_exits: dict[int, int | bool] = {}

# How long to wait for the limit to fill before falling back to market
LIMIT_FILL_TIMEOUT_SEC = 1.5   # tune: 1.0–2.0 is typical
POLL_STEP_SEC = 0.15           # how often we poll the order status while waiting

def _prune_inactive_exits(ib: IB, open_conids: set[int]) -> None:
    """
    Remove entries for conIds that are no longer open *or* have no open SELL order.
    This lets us re-enter the same contract later in the session.
    """
    open_sell_conids = set()
    for t in ib.openTrades():
        if t.order.action == 'SELL':
            open_sell_conids.add(t.contract.conId)

    for conId in list(active_exits.keys()):
        if (conId not in open_conids) or (conId not in open_sell_conids):
            active_exits.pop(conId, None)

def _wait_until_filled_or_timeout(ib: IB, trade, timeout_s: float, poll_s: float) -> float:
    """
    Wait until the given trade is fully filled or the timeout elapses.
    Returns remaining quantity (0.0 means fully filled).
    """
    elapsed = 0.0
    while elapsed < timeout_s:
        ib.sleep(poll_s)
        elapsed += poll_s
        # Ensure status is current
        remaining = getattr(trade.orderStatus, "remaining", None)
        status = getattr(trade.orderStatus, "status", "")
        if remaining is not None:
            if remaining <= 0 or status.upper() == "FILLED":
                return 0.0
    # Timed out; fetch most recent remaining
    return float(getattr(trade.orderStatus, "remaining", 0.0) or 0.0)

def monitor_all_positions(ib: IB, logger):
    """
    Continuously monitor all open option positions with stop-loss protection.
    Avoids duplicate exit orders and allows re-entries of the same contract.
    Adds Plan C: limit sell, short wait, then market fallback for any remainder.
    """
    logger.info("Monitoring all open option positions with stop-loss protection...")

    try:
        while True:
            positions = get_open_option_positions(ib)  # always refreshed
            open_conids = {p.contract.conId for p in positions}
            _prune_inactive_exits(ib, open_conids)

            if not positions:
                logger.info("No open option positions found. Sleeping before next check...")
                time.sleep(1)
                continue

            for pos in positions:
                contract = pos.contract
                conId = contract.conId
                symbol = contract.localSymbol
                quantity = abs(pos.position)
                if quantity <= 0:
                    continue

                # If we already fired an exit for this still-open position, skip
                if conId in active_exits:
                    continue

                # Request live market data
                ib.qualifyContracts(contract)
                ticker = ib.reqMktData(contract, "", False, False)

                # Retry to get a valid bid
                bid = None
                for _ in range(3):
                    ib.sleep(0.4)
                    if ticker.bid is not None:
                        bid = ticker.bid
                        break

                ib.cancelMktData(contract)

                if bid is None:
                    logger.warning(f"{symbol}: Bid price unavailable after retries.")
                    continue

                cost_basis = pos.avgCost / 100.0  # per-share
                loss_percent = ((bid - cost_basis) / cost_basis) * 100.0

                logger.info(
                    f"Checking {symbol} | Cost: {cost_basis:.2f} | Bid: {bid:.2f} | Loss: {loss_percent:.2f}%"
                )

                if loss_percent <= -STOP_LOSS_PERCENT:
                    logger.warning(f"STOP-LOSS TRIGGERED for {symbol} | Loss: {loss_percent:.2f}%")

                    # Final safety: don’t place if there’s already an open SELL on this conId
                    already_has_sell = any(
                        t.contract.conId == conId and t.order.action == 'SELL'
                        for t in ib.openTrades()
                    )
                    if already_has_sell:
                        active_exits[conId] = True
                        logger.info(f"Skipped duplicate exit for {symbol}: SELL already open.")
                        continue

                    # 1) Place LIMIT at current bid
                    limit_trade = place_limit_sell_order(ib, contract, quantity, bid, logger)
                    active_exits[conId] = getattr(limit_trade.order, "orderId", True)

                    # 2) Wait briefly for fill
                    remaining = _wait_until_filled_or_timeout(
                        ib, limit_trade, LIMIT_FILL_TIMEOUT_SEC, POLL_STEP_SEC
                    )

                    if remaining > 0:
                        # 3) Cancel limit and fall back to MARKET for remaining qty
                        try:
                            ib.cancelOrder(limit_trade.order)
                        except Exception:
                            pass
                        ib.sleep(0.1)  # let cancel propagate
                        logger.warning(
                            f"{symbol}: Limit did not fully fill in {LIMIT_FILL_TIMEOUT_SEC:.2f}s "
                            f"(remaining {remaining:.0f}). Sending MARKET for remainder."
                        )
                        place_market_sell_order(ib, contract, remaining, logger)

                else:
                    logger.info(f"Holding {symbol} | Loss {loss_percent:.2f}% is within limit.")

            time.sleep(1)

    except Exception as e:
        logger.exception(f"Exception occurred in monitoring loop: {e}")
