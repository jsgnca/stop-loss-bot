# ibkr_setup.py

from ib_insync import IB, Option

def connect_to_ibkr():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1, timeout=10)  # Port 7497 = paper trading
    return ib

def define_option_contract(ib, symbol, expiry, strike, right):
    """
    Define an option contract dynamically.
    :param ib: IB instance
    :param symbol: Underlying stock symbol (e.g. "TSLA")
    :param expiry: Expiration date in 'YYYYMMDD' format (e.g. '20250719')
    :param strike: Strike price (e.g. 322.5)
    :param right: 'C' for Call or 'P' for Put
    """
    contract = Option(symbol, expiry, strike, right, 'SMART')
    ib.qualifyContracts(contract)
    return contract
