🎯 Project Goal

Build a configurable MT5 Expert Advisor (EA) based on the EMA8–EMA20 crossover strategy, supporting Scalping, Intraday, and Swing modes, with advanced confirmation filters and risk management features.

⚙️ Strategy Overview
🧩 Core Logic

Primary Signal:

Buy Signal: EMA8 crosses above EMA20.

Sell Signal: EMA8 crosses below EMA20.

Trend Confirmation:

Confirm direction using higher timeframe EMA alignment (e.g., 4H trend for intraday, 1H for scalping, Daily for swing).

Option to enable/disable higher timeframe confirmation via UI.

Noise Filtering / Pullback Entry:

Entry is only valid after a pullback and candle confirmation in the direction of the trend.

Candle confirmation options:

Bullish engulfing for buy

Bearish engulfing for sell

User can enable or disable this in UI.

🔧 Configurable Parameters (Streamlit UI)
Parameter	Description	Default	Type
strategy_mode	Scalper / Intraday / Swing	Intraday	Dropdown
lot_size	Lot size for trade	0.1	Numeric
ema_fast	Fast EMA (default 8)	8	Numeric
ema_slow	Slow EMA (default 20)	20	Numeric
timeframe_entry	Timeframe for entry logic	M15	Dropdown
timeframe_confirmation	Higher timeframe for trend confirmation	H1	Dropdown
enable_esi_check	Enable ESI indicator confirmation	False	Boolean
enable_adx_check	Enable ADX trend filter	True	Boolean
adx_threshold	ADX strength threshold	25	Numeric
pullback_confirmation	Enable pullback + candle confirmation entry	True	Boolean
stop_loss_pips	Stop loss in pips	20	Numeric
take_profit_pips	Take profit in pips	40	Numeric
trailing_stop_pips	Trailing stop distance in pips	15	Numeric
use_trailing_stop	Enable trailing stop	True	Boolean
max_open_trades	Limit concurrent positions	1	Numeric
risk_per_trade	Risk % for position sizing	1	Numeric
enable_logging	Enable trade logging to file	True	Boolean
📈 Optional Technical Filters

ADX Filter:

Trade only if ADX > threshold (configurable).

Helps filter out sideways markets.

ESI (Entry Strength Index):

Optional filter to confirm momentum.

Trade only if ESI confirms EMA direction.

Volume Confirmation (optional future feature):

Trade only when candle volume exceeds previous N-candle average.

💹 Entry & Exit Logic
✅ Entry Rules

BUY:

EMA8 crosses above EMA20 on the entry timeframe.

Higher timeframe confirms uptrend (optional).

ADX > threshold (if enabled).

Optional ESI or candle confirmation aligned with uptrend.

SELL:

EMA8 crosses below EMA20 on the entry timeframe.

Higher timeframe confirms downtrend (optional).

ADX > threshold (if enabled).

Optional ESI or candle confirmation aligned with downtrend.

❌ Exit Rules

Stop loss or take profit hit.

Optional trailing stop moves SL with profit.

Opposite EMA crossover signal.

🧮 Trade Management

Dynamic Lot Size: Can be fixed or based on risk_per_trade and account balance.

Trailing Stop: Moves stop loss once price moves X pips in profit.

Break-even Logic (future expansion): Automatically move SL to entry after profit reaches X pips.

🧰 Architecture Outline
Files / Modules

main.py: Streamlit UI + config manager

strategy_core.mq5: Main trading logic (EMA + ADX + ESI)

indicators.mq5: Custom indicators wrapper

risk_manager.mq5: Position sizing and risk logic

logger.py: Logs trade actions and results

backtest_config.json: Stores parameter presets per mode

🧭 Mode-Specific Presets
Mode	Timeframe	Stop Loss	Take Profit	Trailing	Higher TF
Scalper	M1–M5	10 pips	20 pips	5 pips	M15
Intraday	M15–H1	20 pips	40 pips	15 pips	H1
Swing	H4–D1	50 pips	120 pips	40 pips	D1
💬 Example Prompts for Cursor AI
Prompt 1 — Core Strategy Builder

Build a complete MT5 Expert Advisor in MQL5 implementing the EMA8–EMA20 crossover logic with selectable modes (Scalper, Intraday, Swing), and all configurable parameters listed in the table. Include ADX and ESI as optional confirmations.

Prompt 2 — Streamlit Configuration Interface

Build a Streamlit interface that allows me to configure and save all strategy parameters (lot size, timeframes, EMA values, ADX threshold, trailing stop, etc.) and then write them to a JSON config file that the EA reads at runtime.

Prompt 3 — Risk & Trade Manager

Add a risk management module that calculates lot size based on risk percentage per trade, limits concurrent trades, and manages trailing stop and stop loss updates dynamically.

Prompt 4 — Logging & Reporting

Add a Python-based logging module that records each trade event (entry, exit, profit, stop, trailing move) to a local file and displays trade summaries in Streamlit dashboard.

🚀 Deliverables Expected

MQL5 Expert Advisor (EMA8_EMA20_Strategy.mq5)

Streamlit UI (config_ui.py)

Config file (config.json)

Logging system (logger.py)

Documentation (README.md)