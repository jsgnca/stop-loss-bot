# utils.py
from __future__ import annotations

import logging
from typing import List, Set
from ib_insync import IB, Option, MarketOrder, Position

# Cache: which option contracts we've already qualified (by conId)
_QUALIFIED_CONIDS: Set[int] = set()


def _ensure_qualified(ib: IB, contract: Option, logger: logging.Logger) -> None:
    """
    Qualify an option contract once (per conId). Uses SMART routing by default.
    """
    try:
        # For options, SMART is generally correct; primaryExchange is not required.
        if not getattr(contract, "exchange", None):
            contract.exchange = "SMART"

        con_id = getattr(contract, "conId", None)
        if con_id is None:
            # If contract came in without conId (rare), qualify to populate it.
            ib.qualifyContracts(contract)
            con_id = contract.conId

        if con_id not in _QUALIFIED_CONIDS:
            ib.qualifyContracts(contract)  # no-op if already fully specified
            _QUALIFIED_CONIDS.add(con_id)
    except Exception as e:
        logger.warning(f"Qualification failed for {getattr(contract, 'localSymbol', contract)}: {e}")


def get_open_option_positions(ib: IB, logger: logging.Logger | None = None) -> List[Position]:
    """
    Return all *currently open* option positions with qualified contracts.

    Notes:
      - We avoid calling ib.reqPositions() on every tick; ib_insync keeps positions
        updated as long as the event loop is pumping (use ib.sleep in your loop).
      - Each option contract is qualified once per conId to reduce API load.
    """
    positions = [
        p for p in ib.positions()
        if isinstance(p.contract, Option) and p.position != 0
    ]

    if not positions:
        return positions

    lg = logger or logging.getLogger("stoploss.utils")

    for p in positions:
        # Ensure SMART and qualify just once
        try:
            if not getattr(p.contract, "exchange", None):
                p.contract.exchange = "SMART"
            _ensure_qualified(ib, p.contract, lg)
        except Exception as e:
            lg.warning(f"Prep failed for {getattr(p.contract, 'localSymbol', p.contract)}: {e}")

    return positions


def place_market_sell_order(ib: IB, contract: Option, quantity: float, logger: logging.Logger):
    """
    Place a MARKET SELL for the given option contract and quantity (contracts).
    Returns the Trade object or None on failure.
    """
    try:
        qty = int(abs(round(quantity)))  # IB requires int contracts
        if qty <= 0:
            logger.info(f"Skipping MARKET SELL for {getattr(contract, 'localSymbol', contract)}: qty <= 0")
            return None

        order = MarketOrder("SELL", qty)
        trade = ib.placeOrder(contract, order)
        logger.warning(f"Placed MARKET SELL x{qty} for {getattr(contract, 'localSymbol', contract)}")
        return trade
    except Exception as e:
        logger.error(f"Failed to place MARKET SELL for {getattr(contract, 'localSymbol', contract)}: {e}")
        return None
