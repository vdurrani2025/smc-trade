"""
Streamlit Configuration UI for EMA Strategy
Allows users to configure and save strategy parameters
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Configuration loading/saving functions are defined below


def load_config_file(config_path: str = "ema_strategy/config.json") -> dict:
    """Load configuration from file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Config file not found: {config_path}")
        return {}
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return {}


def save_config_file(config: dict, config_path: str = "ema_strategy/config.json"):
    """Save configuration to file"""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False


# Page config
st.set_page_config(
    page_title="EMA Strategy Config",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ EMA8-EMA20 Strategy Configuration")

# Load existing config
config_path = "ema_strategy/config.json"
config = load_config_file(config_path)

if not config:
    st.warning("No existing configuration found. Using defaults.")

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = config

# Sidebar - Mode Presets
with st.sidebar:
    st.header("📋 Mode Presets")
    
    mode_presets = {
        "Scalper": {
            "timeframe_entry": "M5",
            "timeframe_confirmation": "M15",
            "stop_loss_pips": 10,
            "take_profit_pips": 20,
            "trailing_stop_pips": 5
        },
        "Intraday": {
            "timeframe_entry": "M15",
            "timeframe_confirmation": "H1",
            "stop_loss_pips": 20,
            "take_profit_pips": 40,
            "trailing_stop_pips": 15
        },
        "Swing": {
            "timeframe_entry": "H4",
            "timeframe_confirmation": "D1",
            "stop_loss_pips": 50,
            "take_profit_pips": 120,
            "trailing_stop_pips": 40
        }
    }
    
    selected_preset = st.selectbox("Load Preset", ["None"] + list(mode_presets.keys()))
    
    if selected_preset != "None":
        if st.button("Apply Preset"):
            preset = mode_presets[selected_preset]
            if 'strategy' not in st.session_state.config:
                st.session_state.config['strategy'] = {}
            st.session_state.config['strategy'].update(preset)
            st.session_state.config['strategy']['strategy_mode'] = selected_preset
            st.success(f"Applied {selected_preset} preset!")

# Main Configuration Form
st.header("Strategy Parameters")

# Strategy Mode
strategy_mode = st.selectbox(
    "Strategy Mode",
    ["Scalper", "Intraday", "Swing"],
    index=["Scalper", "Intraday", "Swing"].index(
        st.session_state.config.get('strategy', {}).get('strategy_mode', 'Intraday')
    )
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("EMA Settings")
    ema_fast = st.number_input("Fast EMA", min_value=1, max_value=100, 
                               value=st.session_state.config.get('strategy', {}).get('ema_fast', 8))
    ema_slow = st.number_input("Slow EMA", min_value=1, max_value=100,
                              value=st.session_state.config.get('strategy', {}).get('ema_slow', 20))
    
    st.subheader("Timeframes")
    timeframe_entry = st.selectbox(
        "Entry Timeframe",
        ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
        index=["M1", "M5", "M15", "M30", "H1", "H4", "D1"].index(
            st.session_state.config.get('strategy', {}).get('timeframe_entry', 'M15')
        )
    )
    timeframe_confirmation = st.selectbox(
        "Confirmation Timeframe",
        ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
        index=["M1", "M5", "M15", "M30", "H1", "H4", "D1"].index(
            st.session_state.config.get('strategy', {}).get('timeframe_confirmation', 'H1')
        )
    )

with col2:
    st.subheader("Risk Management")
    lot_size = st.number_input("Lot Size", min_value=0.01, value=float(st.session_state.config.get('strategy', {}).get('lot_size', 0.1)), step=0.01)
    risk_per_trade = st.number_input("Risk Per Trade (%)", min_value=0.1, max_value=10.0,
                                     value=float(st.session_state.config.get('strategy', {}).get('risk_per_trade', 1.0)), step=0.1)
    use_fixed_lot = st.checkbox("Use Fixed Lot Size", value=st.session_state.config.get('strategy', {}).get('use_fixed_lot', False))
    max_open_trades = st.number_input("Max Open Trades", min_value=1, max_value=10,
                                     value=st.session_state.config.get('strategy', {}).get('max_open_trades', 1))
    
    st.subheader("Stop Loss & Take Profit")
    stop_loss_pips = st.number_input("Stop Loss (Pips)", min_value=1, max_value=500,
                                     value=st.session_state.config.get('strategy', {}).get('stop_loss_pips', 20))
    take_profit_pips = st.number_input("Take Profit (Pips)", min_value=1, max_value=1000,
                                      value=st.session_state.config.get('strategy', {}).get('take_profit_pips', 40))
    trailing_stop_pips = st.number_input("Trailing Stop (Pips)", min_value=1, max_value=200,
                                         value=st.session_state.config.get('strategy', {}).get('trailing_stop_pips', 15))
    use_trailing_stop = st.checkbox("Enable Trailing Stop", value=st.session_state.config.get('strategy', {}).get('use_trailing_stop', True))

st.header("Technical Filters")

col3, col4 = st.columns(2)

with col3:
    st.subheader("ADX Filter")
    enable_adx_check = st.checkbox("Enable ADX Filter", value=st.session_state.config.get('strategy', {}).get('enable_adx_check', True))
    adx_threshold = st.number_input("ADX Threshold", min_value=1, max_value=100,
                                    value=st.session_state.config.get('strategy', {}).get('adx_threshold', 25),
                                    disabled=not enable_adx_check)
    
    st.subheader("ESI Filter")
    enable_esi_check = st.checkbox("Enable ESI Filter", value=st.session_state.config.get('strategy', {}).get('enable_esi_check', False))

with col4:
    st.subheader("Candle Confirmation")
    pullback_confirmation = st.checkbox("Enable Pullback + Candle Confirmation",
                                       value=st.session_state.config.get('strategy', {}).get('pullback_confirmation', True))
    
    st.subheader("Logging")
    enable_logging = st.checkbox("Enable Trade Logging", value=st.session_state.config.get('strategy', {}).get('enable_logging', True))

# Save Configuration
st.header("💾 Save Configuration")

if st.button("💾 Save Configuration", type="primary"):
    # Build config dictionary
    strategy_config = {
        'strategy_mode': strategy_mode,
        'lot_size': lot_size,
        'ema_fast': int(ema_fast),
        'ema_slow': int(ema_slow),
        'timeframe_entry': timeframe_entry,
        'timeframe_confirmation': timeframe_confirmation,
        'enable_esi_check': enable_esi_check,
        'enable_adx_check': enable_adx_check,
        'adx_threshold': int(adx_threshold),
        'pullback_confirmation': pullback_confirmation,
        'stop_loss_pips': int(stop_loss_pips),
        'take_profit_pips': int(take_profit_pips),
        'trailing_stop_pips': int(trailing_stop_pips),
        'use_trailing_stop': use_trailing_stop,
        'max_open_trades': int(max_open_trades),
        'risk_per_trade': risk_per_trade,
        'use_fixed_lot': use_fixed_lot,
        'enable_logging': enable_logging
    }
    
    # Update config
    if 'strategy' not in st.session_state.config:
        st.session_state.config['strategy'] = {}
    st.session_state.config['strategy'].update(strategy_config)
    
    # Keep MT5 config if exists
    if 'mt5' not in st.session_state.config:
        st.session_state.config['mt5'] = config.get('mt5', {})
    
    # Save to file
    if save_config_file(st.session_state.config, config_path):
        st.success("✅ Configuration saved successfully!")
        st.json(st.session_state.config)
    else:
        st.error("❌ Failed to save configuration")

# Display Current Configuration
st.header("📄 Current Configuration")
st.json(st.session_state.config.get('strategy', {}))

