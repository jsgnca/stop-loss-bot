# config.py

# --- Trade Config ---
ENTRY_PRICE = 2.50  # Manually enter the price you paid per contract
STOP_LOSS_PERCENT = 25  # Triggers exit if price drops by this %

# --- IBKR Option Contract Info (update as needed) ---
OPTION_SYMBOL = "TSLA"
EXPIRATION = "20250718"  # Format: YYYYMMDD
STRIKE = 322.5
RIGHT = "P"  # 'C' for Call, 'P' for Put
EXCHANGE = "SMART"

# --- IBKR Paper Account Info ---
ACCOUNT_ID = "DUN086112"  # Find this in IBKR TWS under 'Account'

# --- Derived ---
STOP_PRICE = round(ENTRY_PRICE * (1 - STOP_LOSS_PERCENT / 100), 2)
