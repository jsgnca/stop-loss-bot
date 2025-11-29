# Stop Loss Bot

Small IBKR stop-loss bot using `ib-insync`. Exits options with **market orders** when unrealized P&L hits the configured loss %.

## Files
- `main.py` — entry point; 1s loop; passes logger to logic.
- `stop_loss_logic.py` — scans open option positions, triggers market exits; duplicate-exit guard.
- `utils.py` — helpers: get open option positions (qualified), place market sell.
- `ibkr_setup.py` — connect to TWS/Gateway; LIVE/PAPER toggle.
- `config.py` — risk knobs (currently `STOP_LOSS_PERCENT = 7.5`).
- `logger.py` — console + rotating file logger (`bot.log`).
- `test.py` — scratchpad for experiments.

## Install
```bash
python -m pip install -r requirements.txt
