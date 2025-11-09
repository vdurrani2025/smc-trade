# How the ICT Trading Bot Works

## Overview

This trading bot implements **Smart Money Concept (ICT)** trading strategies using pattern recognition across multiple timeframes. It analyzes market data to identify specific price patterns that indicate potential trading opportunities.

---

## Market Features Captured

The bot captures and analyzes the following market features:

### 1. **OHLCV Data (Open, High, Low, Close, Volume)**
   - **Source**: Live MT5 data or uploaded CSV files
   - **Timeframes**: 1-minute (M1), 5-minute (M5), 15-minute (M15), 1-hour (H1)
   - **Purpose**: Raw price data for pattern detection

### 2. **Fair Value Gaps (FVG)**
   - **What it is**: Price imbalances where there's a gap between three consecutive candles
   - **Detection**: 
     - **Bullish FVG**: When candle 2's low > candle 1's high AND candle 3's low > candle 1's high
     - **Bearish FVG**: When candle 2's high < candle 1's low AND candle 3's high < candle 1's low
   - **Timeframes**: Detected on 1m and 5m charts
   - **Market Feature**: Shows areas where price "jumped" and may return to fill the gap
   - **Trading Use**: Entry zones - price often returns to fill these gaps

### 3. **Break of Structure (BOS)**
   - **What it is**: When price breaks through a previous swing high or low
   - **Detection**: 
     - Finds swing highs/lows (local peaks and valleys)
     - Detects when a candle closes beyond a previous swing point
     - **Bullish BOS**: Close above previous swing high
     - **Bearish BOS**: Close below previous swing low
   - **Timeframes**: Detected on 15m and 1h charts (higher timeframes for trend confirmation)
   - **Market Feature**: Indicates a change in market structure and potential trend continuation
   - **Trading Use**: Confirms trend direction and momentum

### 4. **Change of Character (CHoCH)**
   - **What it is**: The first reversal in market structure - when trend changes direction
   - **Detection**: 
     - Identifies when a bearish BOS is followed by a bullish BOS (bullish CHoCH)
     - Identifies when a bullish BOS is followed by a bearish BOS (bearish CHoCH)
   - **Timeframes**: Detected on 1m and 5m charts
   - **Market Feature**: Signals a potential trend reversal or major shift in market sentiment
   - **Trading Use**: Confirms that the market structure has changed, validating trade direction

### 5. **Liquidity Grab (Liquidity Sweep)**
   - **What it is**: When price briefly breaks a previous high/low (wick) but then reverses
   - **Detection**: 
     - **Bullish Liquidity**: Wick breaks previous low, but closes above it
     - **Bearish Liquidity**: Wick breaks previous high, but closes below it
   - **Timeframes**: Detected on 15m and 1h charts
   - **Market Feature**: Shows where "stop losses" were triggered (liquidity taken), often followed by reversal
   - **Trading Use**: Entry trigger - after liquidity is grabbed, price often moves in opposite direction

### 6. **Liquidity Levels**
   - **What it is**: Recent swing highs and lows (support/resistance levels)
   - **Detection**: Finds highest high and lowest low in recent price action (last 50 candles)
   - **Timeframes**: Analyzed on 5m chart
   - **Market Feature**: Key price levels where orders cluster
   - **Trading Use**: Stop loss placement and target levels

---

## How the Trading Logic Works

### Step-by-Step Process:

#### **1. Data Collection**
```
Every 60 seconds (or when CSV is uploaded):
├── Fetch OHLCV data from MT5 or parse CSV
├── Get data for 4 timeframes: M1, M5, M15, H1
└── Store in pandas DataFrames
```

#### **2. Pattern Detection (Multi-Timeframe Analysis)**

**On 15m and 1h Timeframes:**
- Detect **Liquidity Grabs** (recent wick breaks)
- Detect **Break of Structure (BOS)** (swing breaks)

**On 1m and 5m Timeframes:**
- Detect **Fair Value Gaps (FVG)** (price imbalances)
- Detect **Change of Character (CHoCH)** (structure reversals)
- Find **Liquidity Levels** (support/resistance)

#### **3. Trade Setup Detection**

The bot looks for a **complete ICT setup** with this sequence:

```
✅ Step 1: Liquidity Sweep (15m or 1h)
   └── Price wick breaks previous high/low, then reverses
   
✅ Step 2: CHoCH Confirmation (1m or 5m)
   └── Market structure changes direction
   └── Must happen AFTER liquidity sweep
   
✅ Step 3: FVG Mitigation (1m or 5m)
   └── Unfilled FVG in the direction of the trade
   └── Price reaches the FVG zone
```

**Example Bullish Setup:**
1. **Liquidity Grab**: Price wick breaks below recent low on 15m, then closes above
2. **CHoCH**: Bearish BOS followed by bullish BOS on 5m (structure changed to bullish)
3. **FVG**: Bullish FVG detected on 5m that hasn't been filled yet
4. **Entry**: When price reaches the FVG low zone

#### **4. Trade Execution**

When all conditions are met:

```python
Entry Price: FVG low (for bullish) or FVG high (for bearish)
Stop Loss: Below liquidity grab low (bullish) or above liquidity grab high (bearish)
Take Profit: Entry + (Entry - Stop Loss) × 2  (1:2 Risk:Reward ratio)
```

**Risk Management:**
- Lot size calculated based on account balance and risk percentage
- Maximum 1 position at a time (configurable)
- Auto-close all positions before Friday 21:00 GMT

#### **5. Visualization**

The Streamlit dashboard displays:
- **Candlestick Chart** with all detected patterns overlaid
- **FVG Zones**: Green (bullish) or Red (bearish) rectangles
- **Liquidity Levels**: Horizontal dashed lines
- **BOS Markers**: Triangle markers showing structure breaks
- **CHoCH Markers**: Star markers showing character changes
- **Trade Markers**: Yellow arrows showing entry points

---

## Data Flow Diagram

```
┌─────────────────┐
│  Data Source    │
│  (MT5 or CSV)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Multi-Timeframe│
│  Data Fetch     │
│  M1, M5, M15, H1│
└────────┬──────┘
           │
           ▼
┌──────────────────────────┐
│  Pattern Detection       │
│  ├── FVG (M1, M5)        │
│  ├── BOS (M15, H1)       │
│  ├── CHoCH (M1, M5)      │
│  └── Liquidity (M15, H1) │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Trade Setup Detection    │
│  Liquidity → CHoCH → FVG  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Risk Calculation        │
│  Lot Size, SL, TP        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Order Execution (MT5)   │
│  or Signal Display (CSV) │
└──────────────────────────┘
```

---

## Key Market Features Summary

| Feature | What It Captures | Timeframe | Trading Purpose |
|---------|-----------------|-----------|-----------------|
| **FVG** | Price gaps/imbalances | 1m, 5m | Entry zones |
| **BOS** | Structure breaks | 15m, 1h | Trend confirmation |
| **CHoCH** | Structure reversals | 1m, 5m | Direction confirmation |
| **Liquidity Grab** | Stop loss sweeps | 15m, 1h | Entry trigger |
| **Liquidity Levels** | Support/Resistance | 5m | SL/TP placement |

---

## Example Trade Scenario

**Bullish Trade Example:**

1. **15m Chart**: Price wick breaks below 1.0850 (previous low), then closes at 1.0860
   - ✅ **Liquidity Grab Detected**

2. **5m Chart**: 
   - Bearish BOS at 1.0840, then bullish BOS at 1.0870
   - ✅ **CHoCH Detected** (structure changed to bullish)
   - Bullish FVG zone between 1.0865 - 1.0875 (unfilled)
   - ✅ **FVG Detected**

3. **Trade Setup**:
   - Entry: 1.0865 (FVG low)
   - Stop Loss: 1.0845 (below liquidity grab)
   - Take Profit: 1.0905 (Entry + 2× risk = 1:2 RR)

4. **Execution**: When price reaches 1.0865, bot places BUY order

---

## Why This Approach Works

1. **Multi-Timeframe Confirmation**: Uses higher timeframes (15m, 1h) for trend direction and lower timeframes (1m, 5m) for precise entry
2. **Liquidity First**: Identifies where retail traders' stop losses are, which institutions target
3. **Structure Analysis**: BOS and CHoCH confirm genuine trend changes vs. temporary price movements
4. **FVG Entries**: Price often returns to fill gaps, providing high-probability entry zones
5. **Risk Management**: Strict 1:2 risk-reward ratio and position sizing protects capital

---

## Limitations & Considerations

- **Market Conditions**: Works best in trending markets, may struggle in choppy/ranging markets
- **False Signals**: Not all setups result in profitable trades
- **Timeframe Dependency**: Requires all timeframes to align, which may be rare
- **Execution Speed**: 60-second scan interval means it may miss very fast setups
- **CSV Mode**: Analysis only (no live trading) when using CSV files

---

## Technical Implementation

- **Language**: Python 3
- **Libraries**: pandas, numpy, plotly, streamlit, MetaTrader5
- **Architecture**: Modular design with separate modules for:
  - MT5 connection (`mt5_connector.py`)
  - Pattern detection (`smc_logic.py`)
  - Visualization (`utils.py`)
  - Main application (`main.py`)

