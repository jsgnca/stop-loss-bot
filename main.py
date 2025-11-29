# main.py

from ib_insync import util
import sys
from logger import setup_logger            # uses the minimal logger file I sent
from ibkr_setup import connect_to_ibkr
from stop_loss_logic import monitor_all_positions

CHECK_INTERVAL_SECONDS = 1.0  # 1s loop for options; reduces missed triggers

def main():
    log = setup_logger(name="stop_loss_bot")
    ib = None

    try:
        log.info("Connecting to IBKR...")
        ib = connect_to_ibkr()
        util.startLoop()  # ensure ib_insync's event loop is running
        log.info("Connected to IBKR. Starting all-day monitoring...")

        while True:
            monitor_all_positions(ib, log)
            # use ib.sleep so the event loop continues processing ticks & fills
            ib.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log.info("KeyboardInterrupt: shutting down...")

    except Exception as e:
        # full traceback + message
        log.exception(f"Unexpected error during monitoring: {e}")

    finally:
        if ib and ib.isConnected():
            ib.disconnect()
            log.info("Disconnected from IBKR.")

if __name__ == "__main__":
    # Allow clean exit codes for shells/PM2/etc.
    try:
        main()
        sys.exit(0)
    except SystemExit as se:
        raise
    except Exception:
        sys.exit(1)
