# ibkr_setup.py

from ib_insync import IB, Option

# --- LIVE / PAPER toggle (one place) ---
USE_LIVE = True           # True = LIVE (7496), False = PAPER (7497)
IB_HOST = "127.0.0.1"
IB_LIVE_PORT = 7496
IB_PAPER_PORT = 7497
IB_CLIENT_ID = 1001       # keep unique if multiple scripts run

def connect_to_ibkr() -> IB:
    """
    Connect to IBKR TWS/Gateway with a clear LIVE/PAPER switch and basic safety checks.
    """
    ib = IB()
    port = IB_LIVE_PORT if USE_LIVE else IB_PAPER_PORT
    env = "LIVE" if USE_LIVE else "PAPER"

    # Connect
    ib.connect(IB_HOST, port, clientId=IB_CLIENT_ID, timeout=10)
    if not ib.isConnected():
        raise RuntimeError(f"Failed to connect to IBKR {env} at {IB_HOST}:{port} (clientId={IB_CLIENT_ID})")

    # Optional: set market data type (1 = live, 2 = frozen, 3 = delayed, 4 = delayed-frozen)
    # Use 1 when you have live data; if you only have delayed permissions, 3 avoids None ticks.
    ib.reqMarketDataType(1)

    # Quick sanity: list managed accounts so you can see where you are
    try:
        accts = ib.managedAccounts()
        # Not logging here (keeps file minimal); main/logger will print this if needed
        _ = accts  # no-op to avoid lint warnings
    except Exception:
        pass

    return ib

def define_option_contract(ib: IB, symbol: str, expiry: str, strike: float, right: str) -> Option:
    """
    Define and qualify an option contract (SMART routing).
    expiry: 'YYYYMMDD' (e.g., '20250719'); right: 'C' or 'P'
    """
    contract = Option(symbol, expiry, strike, right, 'SMART')
    ib.qualifyContracts(contract)
    return contract
