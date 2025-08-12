# main.py

import time
from ibkr_setup import connect_to_ibkr
from stop_loss_logic import monitor_all_positions
from logger import logging

CHECK_INTERVAL_SECONDS = 10  # how often to re-check positions

def main():
    logger = logging.getLogger("stop_loss_bot")
    ib = None

    try:
        logger.info("Connecting to IBKR...")
        ib = connect_to_ibkr()
        logger.info("Connected to IBKR. Starting all-day monitoring...")

        while True:
            monitor_all_positions(ib, logger)
            time.sleep(CHECK_INTERVAL_SECONDS)

    except Exception as e:
        logger.exception(f"Unexpected error during monitoring: {e}")

    finally:
        if ib and ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IBKR.")


if __name__ == "__main__":
    main()
