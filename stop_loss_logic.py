# stop_loss_logic.py

import logging
from ib_insync import LimitOrder
from config import ENTRY_PRICE, STOP_LOSS_PERCENT, STOP_PRICE, ACCOUNT_ID

def check_stop_loss(ib, contract):
    """
    Checks current price of the option, compares with stop price,
    and sends a sell order if stop-loss is triggered.
    """
    ticker = ib.reqMktData(contract, '', False, False)
    ib.sleep(1)  # wait for fresh data

    current_price = ticker.last
    if current_price is None:
        logging.warning("Current price unavailable, skipping check.")
        return

    loss_percent = ((current_price - ENTRY_PRICE) / ENTRY_PRICE) * 100
    logging.info(f"Current Price: {current_price:.2f} | Loss: {loss_percent:.2f}% | Stop Loss: -{STOP_LOSS_PERCENT}%")

    if loss_percent <= -STOP_LOSS_PERCENT:
        logging.info(f"Stop-loss hit! Selling {contract.symbol} option at {current_price:.2f}")

        order = LimitOrder('SELL', 1, current_price)
        trade = ib.placeOrder(contract, order)
        ib.sleep(1)  # wait for order to process

        if trade.orderStatus.status == 'Filled':
            logging.info("Order filled successfully.")
        else:
            logging.warning(f"Order status: {trade.orderStatus.status}")
