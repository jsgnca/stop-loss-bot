"""
panic_flatten.py

TradePilot Brick #1:
API-based PANIC FLATTEN for your scalp account (options only).

This uses your existing ibkr_setup LIVE/PAPER configuration
so you never accidentally connect to the wrong environment.

- Press HOTKEY (e.g., F9)
- Cancels working orders for all option positions
- Sends MARKET orders to flatten everything
"""

from ib_insync import IB, Position, Contract, MarketOrder
import keyboard
import time
import logging
from typing import List, Optional

# ================== IMPORT YOUR IB SETUP ================== #
from ibkr_setup import (
    IB_HOST, USE_LIVE,
    IB_LIVE_PORT, IB_PAPER_PORT
)

# Panic flattener uses its own unique clientId
CLIENT_ID = 2001

# Which account to flatten (None = all accounts)
ACCOUNT: Optional[str] = None

# Which key triggers the flatten
HOTKEY = "F9"

# =========================================================== #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


class PanicFlattener:
    def __init__(self):
        self.ib = IB()
        self.connected = False

    def connect(self) -> None:
        """Connect using your LIVE / PAPER toggle from ibkr_setup."""
        if self.connected:
            return

        port = IB_LIVE_PORT if USE_LIVE else IB_PAPER_PORT
        env = "LIVE" if USE_LIVE else "PAPER"

        logging.info(f"Connecting to IBKR {env} at {IB_HOST}:{port}, clientId={CLIENT_ID}...")
        self.ib.connect(IB_HOST, port, clientId=CLIENT_ID, timeout=10)
        self.connected = True
        logging.info("Connected to IBKR.")

        # use live data (or adjust if you only have delayed permissions)
        self.ib.reqMarketDataType(1)

    def get_open_option_positions(self) -> List[Position]:
        """Return non-zero option positions."""
        self.ib.reqPositions()
        positions = [p for p in self.ib.positions() if abs(p.position) > 0]

        # Filter to options only
        positions = [p for p in positions if p.contract.secType == "OPT"]

        # Filter by specific account (if provided)
        if ACCOUNT:
            positions = [p for p in positions if p.account == ACCOUNT]

        return positions

    def cancel_open_orders_for_contracts(self, contracts: List[Contract]) -> None:
        """Cancel any working orders on the given contracts."""
        if not contracts:
            return

        open_orders = self.ib.openOrders()
        con_ids = {c.conId for c in contracts if c.conId}

        for order in open_orders:
            c = order.contract
            if not c or c.conId not in con_ids:
                continue
            logging.info(f"Cancelling order {order.orderId} on {c.localSymbol}")
            self.ib.cancelOrder(order)

    def flatten_all_options(self) -> None:
        """Flatten all open option positions with MARKET orders."""
        self.connect()

        positions = self.get_open_option_positions()
        if not positions:
            logging.info("No open option positions to flatten.")
            return

        logging.info("PANIC FLATTEN TRIGGERED:")
        for p in positions:
            logging.info(f"  {p.account} | {p.contract.localSymbol} | qty={p.position}")

        # Cancel working orders on these contracts
        contracts = [p.contract for p in positions]
        self.cancel_open_orders_for_contracts(contracts)

        trades = []
        for pos in positions:
            qty = abs(pos.position)
            if qty == 0:
                continue

            side = "SELL" if pos.position > 0 else "BUY"
            c = pos.contract

            logging.info(f"Submitting MARKET {side} for {qty} of {c.localSymbol}")
            order = MarketOrder(side, qty)
            trade = self.ib.placeOrder(c, order)
            trades.append(trade)

        # allow order statuses to update
        self.ib.sleep(1.0)

        for trade in trades:
            status = trade.orderStatus.status
            logging.info(f"Order {trade.order.orderId} on {trade.contract.localSymbol} -> {status}")

    def run_hotkey_loop(self) -> None:
        """Main loop: listen for hotkey → flatten."""
        self.connect()
        logging.info(f"PANIC FLATTENER READY. Press {HOTKEY} to flatten all option positions.")
        logging.info("Press Ctrl+C in this window to exit.\n")

        try:
            while True:
                if keyboard.is_pressed(HOTKEY):
                    logging.info(f"Hotkey {HOTKEY} detected!")
                    self.flatten_all_options()
                    time.sleep(1.0)   # debounce

                self.ib.sleep(0.05)

        except KeyboardInterrupt:
            logging.info("Exiting panic flattener...")
        finally:
            if self.connected:
                self.ib.disconnect()
                logging.info("Disconnected from IBKR.")


if __name__ == "__main__":
    flattener = PanicFlattener()
    flattener.run_hotkey_loop()
