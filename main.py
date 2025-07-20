# main.py

from ibkr_setup import connect_to_ibkr, define_option_contract
from stop_loss_logic import monitor_stop_loss
from config import OPTION_SYMBOL, STOP_PRICE
from logger import setup_logger
import time


def main():
    logger = setup_logger("stop_loss_bot")
    ib = None  # initialize outside try for safe access in finally

    try:
        logger.info("Connecting to IBKR...")
        ib = connect_to_ibkr()

        logger.info(f"Defining contract for symbol: {OPTION_SYMBOL}")
        option_contract = define_option_contract(OPTION_SYMBOL)

        logger.info(f"Monitoring contract: {option_contract}")
        logger.info(f"Stop-loss price set at: ${STOP_PRICE}")

        # Run the stop-loss monitor loop
        monitor_stop_loss(ib, option_contract, STOP_PRICE, logger)

    except Exception as e:
        logger.exception(f"Exception occurred during monitoring: {e}")
    finally:
        if ib and ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IBKR.")


if __name__ == "__main__":
    main()
