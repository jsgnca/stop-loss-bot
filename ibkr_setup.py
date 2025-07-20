# ibkr_setup.py

from ib_insync import IB, Option

def setup_ib_connection():
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)  # Port 7497 for paper trading
    return ib

def define_option_contract(ib):
    # Replace with your actual option details or hardcode for manual test
    contract = Option('TSLA', '20250718', 322.5, 'P', 'SMART')
    ib.qualifyContracts(contract)
    return contract
