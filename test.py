from ib_insync import IB, Stock
import time

# Connect to IBKR TWS or Gateway
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Define a simple stock contract (AAPL)
contract = Stock(symbol='AAPL', exchange='SMART', currency='USD')

# Qualify the contract (makes sure IB recognizes it)
ib.qualifyContracts(contract)

# Request live market data
ticker = ib.reqMktData(contract, '', False, False)

# Wait for data to arrive
time.sleep(2)

# Print what we got
print(f"Bid: {ticker.bid}, Ask: {ticker.ask}, Last: {ticker.last}")

# Clean up
ib.cancelMktData(contract)
ib.disconnect()
