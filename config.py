# config.py

# --- Trade Config ---
ENTRY_PRICE = 11.40  # Manually enter the price you paid per contract
STOP_LOSS_PERCENT = 10  # Triggers exit if price drops by this %

# --- IBKR Option Contract Info (update as needed) ---
OPTION_SYMBOL = "TSLA"
OPTION_EXPIRY = "20250725"  # Format: YYYYMMDD
OPTION_STRIKE = 330
OPTION_RIGHT = "P"  # 'C' for Call, 'P' for Put
EXCHANGE = "SMART"

# --- IBKR Paper Account Info ---
ACCOUNT_ID = "DUN086112"  # Found in IBKR TWS under 'Account'

# --- Derived ---
STOP_PRICE = round(ENTRY_PRICE * (1 - STOP_LOSS_PERCENT / 100), 2)
