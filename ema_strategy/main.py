"""
EMA Strategy Main Application
Streamlit-based trading application for EMA8-EMA20 crossover strategy
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time
import json
import logging
import threading
import sys
import os
from pathlib import Path
from typing import Dict, Optional, List

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Import MT5 connector from smc_trader
from smc_trader.mt5_connector import MT5Connector

# Import EMA strategy modules
from ema_strategy.strategy_core import EMAStrategy
from ema_strategy.risk_manager import RiskManager
from ema_strategy.logger import TradeLogger
from ema_strategy.indicators import calculate_ema

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="EMA Strategy Trading Bot",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'mt5_connector' not in st.session_state:
    st.session_state.mt5_connector = None
if 'strategy' not in st.session_state:
    st.session_state.strategy = None
if 'risk_manager' not in st.session_state:
    st.session_state.risk_manager = None
if 'trade_logger' not in st.session_state:
    st.session_state.trade_logger = None
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
if 'config' not in st.session_state:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    try:
        with open(config_path, 'r') as f:
            st.session_state.config = json.load(f)
    except:
        st.session_state.config = {}


def load_config_file():
    """Load configuration from file"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            st.session_state.config = json.load(f)
        return True
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return False


def connect_mt5():
    """Connect to MT5"""
    try:
        config = st.session_state.config
        mt5_config = config.get('mt5', {})
        
        connector = MT5Connector(
            login=mt5_config.get('login', 0),
            password=mt5_config.get('password', ''),
            server=mt5_config.get('server', ''),
            path=mt5_config.get('path', '')
        )
        
        if connector.connect():
            st.session_state.mt5_connector = connector
            
            # Initialize strategy components
            strategy_config = config.get('strategy', {})
            st.session_state.strategy = EMAStrategy(strategy_config)
            st.session_state.risk_manager = RiskManager(strategy_config)
            
            log_file = config.get('logging', {}).get('csv_file', 'ema_trades.csv')
            enable_logging = strategy_config.get('enable_logging', True)
            st.session_state.trade_logger = TradeLogger(log_file, enable_logging)
            
            st.success("✅ Connected to MT5!")
            return True
        else:
            st.error("❌ Failed to connect to MT5. Check your credentials.")
            return False
    except Exception as e:
        st.error(f"Error connecting to MT5: {e}")
        return False


def get_market_data(symbol: str, timeframes: List[str]) -> Dict[str, pd.DataFrame]:
    """Get market data for multiple timeframes"""
    if not st.session_state.mt5_connector or not st.session_state.mt5_connector.is_connected():
        return {}
    
    data = {}
    for tf in timeframes:
        df = st.session_state.mt5_connector.get_latest_rates(symbol, tf, count=500)
        if df is not None and len(df) > 0:
            data[tf] = df
    
    return data


def trading_loop():
    """Main trading loop running in background thread"""
    while st.session_state.trading_active:
        try:
            config = st.session_state.config
            strategy_config = config.get('strategy', {})
            symbol = config.get('symbol', 'EURUSD')
            
            # Get market data
            timeframe_entry = strategy_config.get('timeframe_entry', 'M15')
            timeframe_confirmation = strategy_config.get('timeframe_confirmation', 'H1')
            
            market_data = get_market_data(symbol, [timeframe_entry, timeframe_confirmation])
            
            if not market_data:
                time.sleep(1)
                continue
            
            df_entry = market_data.get(timeframe_entry)
            df_confirmation = market_data.get(timeframe_confirmation)
            
            if df_entry is None or len(df_entry) < 2:
                time.sleep(1)
                continue
            
            # Detect signals
            signals = st.session_state.strategy.detect_signals(df_entry, df_confirmation)
            
            # Check for signals
            if signals.get('buy_signal') or signals.get('sell_signal'):
                # Check max positions
                open_positions = st.session_state.mt5_connector.get_open_positions(symbol=symbol)
                
                if st.session_state.risk_manager.check_max_positions(len(open_positions)):
                    # Get account info
                    account_info = st.session_state.mt5_connector.get_account_info()
                    if account_info:
                        # Calculate lot size
                        stop_loss_pips = strategy_config.get('stop_loss_pips', 20)
                        lot_size = st.session_state.risk_manager.calculate_lot_size(
                            account_info['balance'],
                            stop_loss_pips,
                            symbol,
                            0.0001
                        )
                        
                        # Place order
                        order_type = signals['direction']
                        ticket = st.session_state.mt5_connector.place_order(
                            symbol=symbol,
                            order_type=order_type,
                            lot_size=lot_size,
                            price=0.0,
                            sl=signals['stop_loss'],
                            tp=signals['take_profit'],
                            comment="EMA Strategy"
                        )
                        
                        if ticket:
                            # Log trade
                            st.session_state.trade_logger.log_trade(
                                symbol=symbol,
                                direction=order_type,
                                lot_size=lot_size,
                                entry_price=signals['entry_price'],
                                stop_loss=signals['stop_loss'],
                                take_profit=signals['take_profit'],
                                status="OPEN",
                                strategy_mode=strategy_config.get('strategy_mode', 'Intraday'),
                                timeframe=timeframe_entry
                            )
                            logger.info(f"Trade executed: {order_type} {lot_size} {symbol}")
            
            # Update trailing stops for open positions
            if strategy_config.get('use_trailing_stop', True):
                open_positions = st.session_state.mt5_connector.get_open_positions(symbol=symbol)
                for pos in open_positions:
                    current_price = pos['price_current']
                    entry_price = pos['price_open']
                    current_sl = pos['sl']
                    direction = pos['type']
                    trailing_pips = strategy_config.get('trailing_stop_pips', 15)
                    
                    if st.session_state.risk_manager.should_update_trailing_stop(
                        entry_price, current_price, current_sl, direction,
                        trailing_pips
                    ):
                        new_sl = st.session_state.risk_manager.calculate_trailing_stop(
                            entry_price, current_price, direction, trailing_pips
                        )
                        if new_sl:
                            # Update stop loss (would need to implement modify_position in MT5Connector)
                            logger.info(f"Trailing stop update: {pos['ticket']} -> {new_sl}")
            
            time.sleep(1)  # Refresh every second
            
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(1)


def start_trading():
    """Start trading"""
    if not st.session_state.mt5_connector or not st.session_state.mt5_connector.is_connected():
        st.error("Please connect to MT5 first!")
        return
    
    if st.session_state.trading_active:
        st.warning("Trading is already active!")
        return
    
    st.session_state.trading_active = True
    st.session_state.trading_thread = threading.Thread(target=trading_loop, daemon=True)
    st.session_state.trading_thread.start()
    st.success("🚀 Trading started!")


def stop_trading():
    """Stop trading"""
    st.session_state.trading_active = False
    st.success("⏹️ Trading stopped!")


# Main UI
st.title("📈 EMA8-EMA20 Strategy Trading Bot")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    if st.button("Load Config"):
        load_config_file()
        st.success("Config loaded!")
    
    # MT5 Connection
    st.subheader("MT5 Connection")
    
    if st.session_state.mt5_connector and st.session_state.mt5_connector.is_connected():
        st.success("✅ Connected")
        if st.button("Disconnect"):
            st.session_state.mt5_connector.disconnect()
            st.session_state.mt5_connector = None
            st.success("Disconnected")
    else:
        mt5_login = st.number_input("MT5 Login", value=st.session_state.config.get('mt5', {}).get('login', 0))
        mt5_password = st.text_input("MT5 Password", type="password", value=st.session_state.config.get('mt5', {}).get('password', ''))
        mt5_server = st.text_input("MT5 Server", value=st.session_state.config.get('mt5', {}).get('server', ''))
        
        if st.button("Connect to MT5"):
            st.session_state.config['mt5'] = {
                'login': int(mt5_login),
                'password': mt5_password,
                'server': mt5_server
            }
            connect_mt5()
    
    # Trading Controls
    st.subheader("Trading Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Trading", type="primary"):
            start_trading()
    with col2:
        if st.button("⏹️ Stop Trading"):
            stop_trading()
    
    if st.session_state.trading_active:
        st.warning("🟢 Trading is ACTIVE")

# Main content
if st.session_state.mt5_connector and st.session_state.mt5_connector.is_connected():
    # Account Info
    st.header("💰 Account Information")
    
    account_info = st.session_state.mt5_connector.get_account_info()
    if account_info:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Balance", f"${account_info['balance']:,.2f}")
        with col2:
            st.metric("Equity", f"${account_info['equity']:,.2f}")
        with col3:
            st.metric("Open P&L", f"${account_info['open_pnl']:,.2f}")
        with col4:
            st.metric("Open Positions", account_info['number_of_positions'])
    
    # Strategy Info
    st.header("📊 Strategy Information")
    
    strategy_config = st.session_state.config.get('strategy', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Strategy Mode", strategy_config.get('strategy_mode', 'Intraday'))
    with col2:
        st.metric("Entry Timeframe", strategy_config.get('timeframe_entry', 'M15'))
    with col3:
        st.metric("Confirmation TF", strategy_config.get('timeframe_confirmation', 'H1'))
    
    # Market Analysis
    st.header("📈 Market Analysis")
    
    symbol = st.session_state.config.get('symbol', 'EURUSD')
    timeframe_entry = strategy_config.get('timeframe_entry', 'M15')
    
    market_data = get_market_data(symbol, [timeframe_entry])
    
    if market_data and timeframe_entry in market_data:
        df = market_data[timeframe_entry]
        
        if len(df) > 0:
            # Calculate EMAs for display
            ema_fast = calculate_ema(df['close'], strategy_config.get('ema_fast', 8))
            ema_slow = calculate_ema(df['close'], strategy_config.get('ema_slow', 20))
            
            # Create chart
            fig = go.Figure()
            
            # Add candlestick
            fig.add_trace(go.Candlestick(
                x=df.index[-100:],
                open=df['open'].iloc[-100:],
                high=df['high'].iloc[-100:],
                low=df['low'].iloc[-100:],
                close=df['close'].iloc[-100:],
                name=symbol
            ))
            
            # Add EMAs
            fig.add_trace(go.Scatter(
                x=df.index[-100:],
                y=ema_fast.iloc[-100:],
                name=f"EMA{strategy_config.get('ema_fast', 8)}",
                line=dict(color='blue', width=1)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index[-100:],
                y=ema_slow.iloc[-100:],
                name=f"EMA{strategy_config.get('ema_slow', 20)}",
                line=dict(color='red', width=1)
            ))
            
            fig.update_layout(
                title=f"{symbol} - EMA Strategy",
                xaxis_title="Time",
                yaxis_title="Price",
                height=600,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detect signals
            if st.session_state.strategy:
                df_confirmation = get_market_data(symbol, [strategy_config.get('timeframe_confirmation', 'H1')]).get(
                    strategy_config.get('timeframe_confirmation', 'H1')
                )
                signals = st.session_state.strategy.detect_signals(df, df_confirmation)
                
                if signals.get('buy_signal'):
                    st.success("✅ BUY Signal Detected!")
                elif signals.get('sell_signal'):
                    st.error("❌ SELL Signal Detected!")
                else:
                    st.info("⏳ No Signal")
    
    # Trade Statistics
    if st.session_state.trade_logger:
        st.header("📊 Trade Statistics")
        stats = st.session_state.trade_logger.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", stats.get('total_trades', 0))
        with col2:
            st.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")
        with col3:
            st.metric("Net Profit", f"${stats.get('net_profit', 0):.2f}")
        with col4:
            st.metric("Open Trades", stats.get('open_trades', 0))
    
else:
    st.info("👈 Please connect to MT5 in the sidebar to start trading")

