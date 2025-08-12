from ib_insync import IB, Option, LimitOrder, MarketOrder, Position
import logging

def get_open_option_positions(ib: IB):
    """
    Fetch all open option positions from the IBKR account.
    Returns a list of Position objects with valid contracts.
    """
    ib.reqPositions()
    ib.sleep(0.2)  # short pause to let positions refresh
    positions = [p for p in ib.positions() if isinstance(p.contract, Option) and p.position != 0]

    # Enrich contracts with portfolio data (to get primaryExchange)
    for p in positions:
        matching_items = [item for item in ib.portfolio() if item.contract.conId == p.contract.conId]
        if matching_items and matching_items[0].contract.primaryExchange:
            p.contract.exchange = matching_items[0].contract.primaryExchange
        else:
            p.contract.exchange = 'SMART'
        ib.qualifyContracts(p.contract)

    return positions

def place_limit_sell_order(ib: IB, contract: Option, quantity: float, price: float, logger: logging.Logger):
    """
    Places a LIMIT sell order for the given option contract using the correct exchange.
    """
    order = LimitOrder('SELL', quantity, round(float(price), 2))
    trade = ib.placeOrder(contract, order)
    logger.info(f"Placed LIMIT SELL for {contract.localSymbol} | Qty: {quantity} @ ${order.lmtPrice:.2f}")
    ib.sleep(0.1)
    return trade

def place_market_sell_order(ib: IB, contract: Option, quantity: float, logger: logging.Logger):
    """
    Places a MARKET sell order for the given option contract using the correct exchange.
    """
    order = MarketOrder('SELL', quantity)
    trade = ib.placeOrder(contract, order)
    logger.warning(f"Placed MARKET SELL for {contract.localSymbol} | Qty: {quantity}")
    ib.sleep(0.1)
    return trade
