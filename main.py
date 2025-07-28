# main.py

from ibkr_setup import connect_to_ibkr, define_option_contract
from stop_loss_logic import monitor_stop_loss
from config import OPTION_SYMBOL, OPTION_EXPIRY, OPTION_STRIKE, OPTION_RIGHT, STOP_PRICE
from logger import logging
import time


def main():
    logger = logging.getLogger("stop_loss_bot")
    ib = None

    try:
        logger.info("Connecting to IBKR...")
        ib = connect_to_ibkr()

        logger.info(f"Defining option contract: {OPTION_SYMBOL} {OPTION_EXPIRY} {OPTION_STRIKE} {OPTION_RIGHT}")
        contract = define_option_contract(ib, OPTION_SYMBOL, OPTION_EXPIRY, OPTION_STRIKE, OPTION_RIGHT)

        logger.info(f"Monitoring contract: {contract}")
        logger.info(f"Stop-loss price set at: ${STOP_PRICE}")

        monitor_stop_loss(ib, contract, STOP_PRICE, logger)

    except Exception as e:
        logger.exception(f"Exception occurred during monitoring: {e}")
    finally:
        if ib and ib.isConnected():
            ib.disconnect()
            logger.info("Disconnected from IBKR.")


if __name__ == "__main__":
    main()

