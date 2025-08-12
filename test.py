from ib_insync import IB, Stock, util
import time

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock(symbol='TSLA', exchange='SMART', currency='USD')
ib.qualifyContracts(contract)
print("✅ Contract qualified:", contract)

ib.reqMarketDataType(1)
ticker = ib.reqMktData(contract)

start_time = time.time()
timeout = 60  # seconds

print("📡 Listening for live market data (press Ctrl+C to stop)...")

try:
    while time.time() - start_time < timeout:
        ib.sleep(0.5)
        print(f"⏱️ {round(time.time() - start_time, 1)}s | Bid: {ticker.bid}, Ask: {ticker.ask}, Last: {ticker.last}")
except KeyboardInterrupt:
    print("\n🛑 Interrupted by user.")

print("\n✅ Auto-shutdown.")
util.tree(ticker)

ib.cancelMktData(contract)
ib.disconnect()
