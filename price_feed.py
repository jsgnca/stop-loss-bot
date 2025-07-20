# price_feed.py

import logging
from ib_insync import util

def subscribe_to_price_updates(ib, contract):
    """
    Subscribe to live market data for the given contract.
    Keeps the ticker updated for price retrieval.
    """
    ticker = ib.reqMktData(contract, '', False, False)
    util.sleep(2)  # Give it some time to fetch data

    if ticker.last is None:
        logging.warning("Last price not available yet.")
    else:
        logging.info(f"Initial price for {contract.symbol}: {ticker.last}")

    return ticker
