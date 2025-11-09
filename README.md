# ICT Trading Bot

A Streamlit-based Smart Money Concept (ICT) trading bot that performs live intraday trading on MetaTrader 5 using ICT patterns such as Liquidity Grab, Break of Structure (BOS), Change of Character (CHoCH), and Fair Value Gaps (FVG).

## Features

- **MT5 Integration**: Connect to MetaTrader 5 for live market data and order execution
- **ICT Pattern Detection**: Automatically detects FVG, BOS, CHoCH, and Liquidity Grab patterns
- **Multi-Timeframe Analysis**: Uses 1m, 5m, 15m, and 1h timeframes for confirmation
- **Real-time Dashboard**: Interactive Streamlit dashboard with live charts and signals
- **Risk Management**: Configurable risk percentage, lot size, and stop loss/take profit
- **Trade Logging**: Automatic logging of all trades to CSV
- **Auto-Close**: Automatically closes all positions before Friday 21:00 GMT

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure MetaTrader 5 is installed on your system

3. Configure your MT5 credentials in `smc_trader/config.json` or use the Streamlit UI

## Usage

1. Start the Streamlit application:
```bash
streamlit run smc_trader/main.py
```

2. In the Streamlit UI:
   - Connect to MT5 using your credentials
   - Configure trading parameters (symbol, risk %, lot size)
   - Click "Start Trading" to begin automated trading

## Configuration

Edit `smc_trader/config.json` to customize:
- MT5 connection settings
- Trading parameters (symbol, risk %, lot size, TP/SL)
- Timeframe settings
- Notification settings (optional)
- Logging settings

## Trading Logic

The bot follows this entry logic:
1. **Liquidity Sweep**: Detects liquidity grab on 15m or 1h timeframe
2. **CHoCH Confirmation**: Confirms change of character on 1m or 5m timeframe
3. **FVG Mitigation**: Enters when price reaches an unfilled FVG zone
4. **Stop Loss**: Placed below/above the liquidity sweep level
5. **Take Profit**: Either fixed R:R (1:2) or fixed dollar amount ($10-$15)

## Project Structure

```
smc_trader/
├── main.py                # Streamlit entrypoint
├── smc_logic.py           # ICT detection logic
├── mt5_connector.py       # MT5 data fetch + order execution
├── utils.py               # Logging, plotting, utilities
├── config.json            # Runtime parameters
└── __init__.py            # Package initialization
```

## Safety Features

- Verifies MT5 login before enabling trading
- Prevents duplicate entries (max 1 position at a time)
- Handles MT5 disconnections gracefully
- Auto-stops trading on Friday close time
- Comprehensive error handling and logging

## Disclaimer

This software is for educational purposes only. Trading involves substantial risk of loss. Always test thoroughly in a demo account before using real money. The authors are not responsible for any financial losses.

## License

MIT License

