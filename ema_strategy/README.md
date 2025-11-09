# EMA8-EMA20 Crossover Strategy

A configurable MT5 trading strategy based on EMA8-EMA20 crossover with Scalping, Intraday, and Swing modes.

## Features

- **EMA Crossover Strategy**: Buy when EMA8 crosses above EMA20, Sell when EMA8 crosses below EMA20
- **Multiple Trading Modes**: Scalper, Intraday, and Swing with preset configurations
- **Advanced Filters**: ADX, ESI, and pullback confirmation
- **Risk Management**: Position sizing, stop loss, take profit, and trailing stop
- **Streamlit UI**: Easy configuration and monitoring interface
- **Trade Logging**: CSV logging and statistics tracking

## Project Structure

```
ema_strategy/
├── __init__.py           # Package initialization
├── main.py               # Main trading application (Streamlit)
├── config_ui.py          # Configuration UI (Streamlit)
├── strategy_core.py      # EMA strategy logic
├── indicators.py         # Technical indicators (EMA, ADX, ESI)
├── risk_manager.py      # Risk management and position sizing
├── logger.py            # Trade logging and statistics
├── config.json          # Strategy configuration
└── README.md           # This file
```

## Installation

1. Make sure you have the parent project dependencies installed:
```bash
pip install -r requirements.txt
```

2. The EMA strategy uses the same MT5 connector from `smc_trader` module.

## Usage

### 1. Configure Strategy

Run the configuration UI:
```bash
streamlit run ema_strategy/config_ui.py
```

Configure:
- Strategy mode (Scalper/Intraday/Swing)
- EMA periods (default: 8 and 20)
- Timeframes (entry and confirmation)
- Risk parameters (lot size, risk %, SL, TP)
- Technical filters (ADX, ESI, pullback confirmation)
- Trailing stop settings

Click "Save Configuration" to save settings.

### 2. Run Trading Bot

Run the main trading application:
```bash
streamlit run ema_strategy/main.py
```

Steps:
1. Connect to MT5 (enter credentials in sidebar)
2. Load configuration (or use defaults)
3. Click "Start Trading" to begin automated trading

## Strategy Modes

### Scalper Mode
- **Entry Timeframe**: M5
- **Confirmation Timeframe**: M15
- **Stop Loss**: 10 pips
- **Take Profit**: 20 pips
- **Trailing Stop**: 5 pips

### Intraday Mode (Default)
- **Entry Timeframe**: M15
- **Confirmation Timeframe**: H1
- **Stop Loss**: 20 pips
- **Take Profit**: 40 pips
- **Trailing Stop**: 15 pips

### Swing Mode
- **Entry Timeframe**: H4
- **Confirmation Timeframe**: D1
- **Stop Loss**: 50 pips
- **Take Profit**: 120 pips
- **Trailing Stop**: 40 pips

## Entry Rules

### BUY Signal:
1. EMA8 crosses above EMA20 on entry timeframe
2. Higher timeframe confirms uptrend (optional)
3. ADX > threshold (if enabled)
4. ESI confirms momentum (if enabled)
5. Pullback + bullish engulfing (if enabled)

### SELL Signal:
1. EMA8 crosses below EMA20 on entry timeframe
2. Higher timeframe confirms downtrend (optional)
3. ADX > threshold (if enabled)
4. ESI confirms momentum (if enabled)
5. Pullback + bearish engulfing (if enabled)

## Exit Rules

- Stop loss hit
- Take profit hit
- Trailing stop activated (if enabled)
- Opposite EMA crossover signal

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `strategy_mode` | Scalper/Intraday/Swing | Intraday |
| `lot_size` | Lot size for trade | 0.1 |
| `ema_fast` | Fast EMA period | 8 |
| `ema_slow` | Slow EMA period | 20 |
| `timeframe_entry` | Entry timeframe | M15 |
| `timeframe_confirmation` | Confirmation timeframe | H1 |
| `enable_adx_check` | Enable ADX filter | True |
| `adx_threshold` | ADX threshold | 25 |
| `enable_esi_check` | Enable ESI filter | False |
| `pullback_confirmation` | Enable pullback confirmation | True |
| `stop_loss_pips` | Stop loss in pips | 20 |
| `take_profit_pips` | Take profit in pips | 40 |
| `trailing_stop_pips` | Trailing stop distance | 15 |
| `use_trailing_stop` | Enable trailing stop | True |
| `max_open_trades` | Max concurrent positions | 1 |
| `risk_per_trade` | Risk percentage | 1.0 |
| `use_fixed_lot` | Use fixed lot size | False |

## Files

- **main.py**: Main Streamlit application for live trading
- **config_ui.py**: Configuration interface for strategy parameters
- **strategy_core.py**: Core strategy logic and signal detection
- **indicators.py**: Technical indicator calculations
- **risk_manager.py**: Position sizing and risk management
- **logger.py**: Trade logging and statistics
- **config.json**: Strategy configuration file

## Logging

Trades are logged to:
- **CSV File**: `ema_trades.csv` (default)
- **Log File**: `ema_trades.log` (default)

Statistics tracked:
- Total trades
- Win rate
- Net profit/loss
- Average profit/loss
- Open positions

## Notes

- The strategy uses the MT5 connector from `smc_trader` module
- All timeframes must be available in MT5
- Ensure proper risk management settings before live trading
- Test thoroughly in demo account first

## Troubleshooting

### No signals detected
- Check if EMAs are calculated correctly
- Verify timeframes are available
- Check filter settings (ADX threshold, etc.)

### Trades not executing
- Verify MT5 connection
- Check max_open_trades limit
- Ensure account has sufficient margin

### Configuration not saving
- Check file permissions
- Verify config.json path is correct

