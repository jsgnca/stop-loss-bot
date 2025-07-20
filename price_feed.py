import logging

def subscribe_to_price_updates(ib, contract):
    """
    Subscribe to live market data for the given contract.
    Keeps the ticker updated for price retrieval.
    """
    ticker = ib.reqMktData(contract, '', False, False)
    ib.sleep(2)  # Non-blocking sleep to allow data to stream

    attempts = 0
    while ticker.last is None and attempts < 5:
        logging.warning("Waiting for market data...")
        ib.sleep(1)
        attempts += 1

    if ticker.last is None:
        logging.warning("Last price not available after several attempts.")
    else:
        logging.info(f"Initial price for {contract.symbol}: {ticker.last}")

    return ticker
