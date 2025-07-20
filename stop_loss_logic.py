# stop_loss_logic.py

import logging
from ib_insync import LimitOrder
from config import ENTRY_PRICE, STOP_LOSS_PERCENT

def monitor_stop_loss(ib, contract, stop_price, logger):
    """
    Monitors the price of the given option contract and places a sell order if
    the price falls to or below the stop-loss price.
    """
    logger.info("Subscribing to market data...")
    ticker = ib.reqMktData(contract, '', False, False)
    ib.sleep(1.5)  # Give it time to update

    current_price = ticker.last or ticker.close

    if current_price is None:
        logger.warning("Current price unavailable. Retrying in next loop.")
        ib.cancelMktData(contract)
        return

    loss_percent = ((current_price - ENTRY_PRICE) / ENTRY_PRICE) * 100
    logger.info(f"Price: {current_price:.2f} | Loss: {loss_percent:.2f}% | Trigger: -{STOP_LOSS_PERCENT}%")

    if current_price <= stop_price:
        logger.info(f"Stop-loss triggered at {current_price:.2f}. Sending sell order...")
        order = LimitOrder('SELL', 1, current_price)

        trade = ib.placeOrder(contract, order)
        ib.sleep(2)  # Let order process

        if trade.orderStatus.status == 'Filled':
            logger.info("Stop-loss order filled.")
        else:
            logger.warning(f"Order not filled. Status: {trade.orderStatus.status}")

    ib.cancelMktData(contract)
