"""
Streamlit Trading Bot - Main Entry Point
Smart Money Concept (ICT) Trading Bot using MT5
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import logging
import threading
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from smc_trader.mt5_connector import MT5Connector
from smc_trader.smc_logic import ICTDetector
from smc_trader.utils import (
    TradeLogger, Plotter, load_config, save_config,
    setup_logging, is_friday_close_time, parse_csv_file, resample_to_timeframes
)

# Setup logging
setup_logging()

logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="ICT Trading Bot",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'mt5_connector' not in st.session_state:
    st.session_state.mt5_connector = None
if 'ict_detector' not in st.session_state:
    st.session_state.ict_detector = ICTDetector()
if 'trade_logger' not in st.session_state:
    st.session_state.trade_logger = None
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
if 'trading_thread' not in st.session_state:
    st.session_state.trading_thread = None
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'config' not in st.session_state:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    st.session_state.config = load_config(config_path)
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = 'MT5'  # 'MT5' or 'CSV'


def load_config_file():
    """Load configuration from file"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        if os.path.exists(config_path):
            st.session_state.config = load_config(config_path)
        else:
            st.error("Config file not found!")
    except Exception as e:
        st.error(f"Error loading config: {e}")


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
            log_dir = os.path.dirname(os.path.abspath(__file__))
            csv_file = os.path.join(log_dir, config.get('logging', {}).get('csv_file', 'trade_history.csv'))
            st.session_state.trade_logger = TradeLogger(csv_file=csv_file)
            st.success("✅ Connected to MT5!")
            return True
        else:
            st.error("❌ Failed to connect to MT5. Check your credentials.")
            return False
    except Exception as e:
        st.error(f"Error connecting to MT5: {e}")
        return False


def disconnect_mt5():
    """Disconnect from MT5"""
    if st.session_state.mt5_connector:
        st.session_state.mt5_connector.disconnect()
        st.session_state.mt5_connector = None
        st.session_state.trading_active = False
        st.success("Disconnected from MT5")


def get_market_data(symbol: str, timeframes: List[str]) -> Dict[str, pd.DataFrame]:
    """Get market data for multiple timeframes"""
    # Check data source
    if st.session_state.data_source == 'CSV':
        # Use CSV data
        if st.session_state.csv_data is not None:
            # Resample the 5-minute CSV data to other timeframes
            resampled = resample_to_timeframes(st.session_state.csv_data, base_timeframe='5T')
            return resampled
        else:
            return {}
    else:
        # Use MT5 data
        if not st.session_state.mt5_connector or not st.session_state.mt5_connector.is_connected():
            return {}
        
        data = {}
        for tf in timeframes:
            df = st.session_state.mt5_connector.get_latest_rates(symbol, tf, count=500)
            if df is not None and len(df) > 0:
                data[tf] = df
        
        return data


def detect_signals(symbol: str, market_data: Dict[str, pd.DataFrame]) -> Dict:
    """Detect ICT signals from market data"""
    if not market_data:
        return {}
    
    detector = st.session_state.ict_detector
    
    signals = {
        'fvgs': [],
        'bos': [],
        'choch': [],
        'liquidity': {},
        'trade_setup': None
    }
    
    try:
        # Get data for different timeframes
        df_1m = market_data.get('M1')
        df_5m = market_data.get('M5')
        df_15m = market_data.get('M15')
        df_1h = market_data.get('H1')
        
        # Detect FVG on 1m and 5m
        if df_1m is not None:
            signals['fvgs'].extend(detector.detect_fvg(df_1m))
        if df_5m is not None:
            signals['fvgs'].extend(detector.detect_fvg(df_5m))
        
        # Detect BOS on 15m and 1h
        if df_15m is not None:
            signals['bos'].extend(detector.detect_bos(df_15m))
        if df_1h is not None:
            signals['bos'].extend(detector.detect_bos(df_1h))
        
        # Detect CHoCH on 1m and 5m
        if df_1m is not None:
            signals['choch'].extend(detector.detect_choch(df_1m))
        if df_5m is not None:
            signals['choch'].extend(detector.detect_choch(df_5m))
        
        # Detect liquidity levels
        if df_5m is not None:
            signals['liquidity'] = detector.find_liquidity_levels(df_5m)
        
        # Detect complete trade setup
        if df_1m is not None and df_5m is not None and df_15m is not None and df_1h is not None:
            signals['trade_setup'] = detector.detect_trade_setup(df_1m, df_5m, df_15m, df_1h)
        
    except Exception as e:
        logger.error(f"Error detecting signals: {e}")
    
    return signals


def execute_trade(symbol: str, setup: Dict) -> Optional[int]:
    """Execute a trade based on setup"""
    if not st.session_state.mt5_connector or not st.session_state.mt5_connector.is_connected():
        return None
    
    try:
        config = st.session_state.config
        trading_config = config.get('trading', {})
        
        # Check if we already have a position
        open_positions = st.session_state.mt5_connector.get_open_positions(symbol=symbol)
        if len(open_positions) >= trading_config.get('max_positions', 1):
            logger.info("Max positions reached, skipping trade")
            return None
        
        # Get account info
        account_info = st.session_state.mt5_connector.get_account_info()
        if account_info is None:
            logger.error("Failed to get account info")
            return None
        
        # Calculate lot size
        risk_percent = trading_config.get('risk_percent', 1.0)
        stop_loss_pips = abs(setup['entry'] - setup['stop_loss']) * 10000  # Approximate pips
        
        lot_size = st.session_state.mt5_connector.calculate_lot_size(
            account_info['balance'],
            risk_percent,
            stop_loss_pips,
            symbol
        )
        
        # Use configured lot size if provided
        if trading_config.get('lot_size', 0) > 0:
            lot_size = trading_config.get('lot_size', 0.01)
        
        # Determine order type
        order_type = "BUY" if setup['direction'] == 'bullish' else "SELL"
        
        # Place order
        ticket = st.session_state.mt5_connector.place_order(
            symbol=symbol,
            order_type=order_type,
            lot_size=lot_size,
            price=0.0,  # Market order
            sl=setup['stop_loss'],
            tp=setup['take_profit'],
            comment="ICT Bot"
        )
        
        if ticket:
            # Log trade
            st.session_state.trade_logger.log_trade(
                symbol=symbol,
                direction=order_type,
                lot_size=lot_size,
                entry_price=setup['entry'],
                stop_loss=setup['stop_loss'],
                take_profit=setup['take_profit'],
                status="OPEN",
                comment="ICT Setup"
            )
            
            logger.info(f"Trade executed: {order_type} {lot_size} {symbol} @ {setup['entry']}")
            return ticket
        
        return None
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return None


def trading_loop():
    """Main trading loop running in background thread"""
    while st.session_state.trading_active:
        try:
            config = st.session_state.config
            trading_config = config.get('trading', {})
            symbol = trading_config.get('symbol', 'EURUSD')
            
            # Check if it's Friday close time
            if trading_config.get('close_before_friday', True):
                if is_friday_close_time(datetime.now(), trading_config.get('friday_close_hour', 21)):
                    logger.info("Friday close time reached, closing all positions")
                    if st.session_state.mt5_connector:
                        st.session_state.mt5_connector.close_all_positions(symbol=symbol)
                    st.session_state.trading_active = False
                    break
            
            # Get market data
            timeframes = ['M1', 'M5', 'M15', 'H1']
            market_data = get_market_data(symbol, timeframes)
            
            if not market_data:
                refresh_interval = trading_config.get('data_refresh_interval', 1)
                time.sleep(refresh_interval)  # Wait before retry
                continue
            
            # Detect signals
            signals = detect_signals(symbol, market_data)
            
            # Check for trade setup
            if signals.get('trade_setup'):
                setup = signals['trade_setup']
                
                # Check if we already have a position
                open_positions = st.session_state.mt5_connector.get_open_positions(symbol=symbol)
                if len(open_positions) == 0:
                    # Execute trade
                    ticket = execute_trade(symbol, setup)
                    if ticket:
                        logger.info(f"Trade executed with ticket: {ticket}")
            
            # Update last update time
            st.session_state.last_update = datetime.now()
            
            # Wait before next iteration (configurable refresh interval)
            refresh_interval = trading_config.get('data_refresh_interval', 1)  # Default 1 second
            time.sleep(refresh_interval)
            
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            refresh_interval = trading_config.get('data_refresh_interval', 1)
            time.sleep(refresh_interval)  # Wait before retry on error


def start_trading():
    """Start trading"""
    # Check data source
    if st.session_state.data_source == 'MT5':
        if not st.session_state.mt5_connector or not st.session_state.mt5_connector.is_connected():
            st.error("Please connect to MT5 first!")
            return
    else:  # CSV mode
        if st.session_state.csv_data is None:
            st.error("Please upload a CSV file first!")
            return
    
    if st.session_state.trading_active:
        st.warning("Trading is already active!")
        return
    
    st.session_state.trading_active = True
    if st.session_state.data_source == 'MT5':
        st.session_state.trading_thread = threading.Thread(target=trading_loop, daemon=True)
        st.session_state.trading_thread.start()
    st.success("🚀 Trading started!")


def stop_trading():
    """Stop trading"""
    st.session_state.trading_active = False
    st.success("⏹️ Trading stopped!")


# Main UI
st.title("📈 ICT Trading Bot")
st.markdown("Smart Money Concept Trading Bot using MetaTrader 5")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Load config
    if st.button("Load Config"):
        load_config_file()
        st.success("Config loaded!")
    
    # MT5 Connection
    st.subheader("MT5 Connection")
    
    if st.session_state.mt5_connector and st.session_state.mt5_connector.is_connected():
        st.success("✅ Connected")
        if st.button("Disconnect"):
            disconnect_mt5()
    else:
        mt5_login = st.number_input("MT5 Login", value=st.session_state.config.get('mt5', {}).get('login', 0))
        mt5_password = st.text_input("MT5 Password", type="password", value=st.session_state.config.get('mt5', {}).get('password', ''))
        mt5_server = st.text_input("MT5 Server", value=st.session_state.config.get('mt5', {}).get('server', ''))
        mt5_path = st.text_input("MT5 Path (optional)", value=st.session_state.config.get('mt5', {}).get('path', ''))
        
        if st.button("Connect to MT5"):
            st.session_state.config['mt5'] = {
                'login': int(mt5_login),
                'password': mt5_password,
                'server': mt5_server,
                'path': mt5_path
            }
            connect_mt5()
    
    # Data Source Selection
    st.subheader("📊 Data Source")
    data_source = st.radio(
        "Select Data Source",
        ["MT5", "CSV File"],
        index=0 if st.session_state.data_source == 'MT5' else 1,
        key="data_source_radio"
    )
    st.session_state.data_source = data_source
    
    # CSV File Upload
    if data_source == "CSV File":
        st.subheader("📁 Upload CSV File")
        uploaded_file = st.file_uploader(
            "Upload 5-minute timeframe CSV file",
            type=['csv'],
            help="Upload a CSV file with OHLCV data (Date/Time, Open, High, Low, Close, Volume)"
        )
        
        if uploaded_file is not None:
            try:
                # Read CSV file
                csv_bytes = uploaded_file.read()
                df = parse_csv_file(csv_bytes, uploaded_file.name)
                
                if df is not None and len(df) > 0:
                    st.session_state.csv_data = df
                    st.success(f"✅ CSV file loaded successfully! ({len(df)} rows)")
                    st.info(f"Date range: {df.index[0]} to {df.index[-1]}")
                else:
                    st.error("❌ Failed to parse CSV file. Please check the format.")
            except Exception as e:
                st.error(f"Error loading CSV file: {e}")
                logger.error(f"Error loading CSV: {e}")
        
        if st.session_state.csv_data is not None:
            if st.button("Clear CSV Data"):
                st.session_state.csv_data = None
                st.success("CSV data cleared")
    
    # Trading Parameters
    st.subheader("Trading Parameters")
    
    if st.session_state.config:
        symbol = st.text_input("Symbol", value=st.session_state.config.get('trading', {}).get('symbol', 'EURUSD'))
        risk_percent = st.number_input("Risk %", min_value=0.1, max_value=10.0, value=st.session_state.config.get('trading', {}).get('risk_percent', 1.0))
        lot_size = st.number_input("Lot Size", min_value=0.01, value=st.session_state.config.get('trading', {}).get('lot_size', 0.01))
        
        st.session_state.config['trading'] = {
            'symbol': symbol,
            'risk_percent': risk_percent,
            'lot_size': lot_size,
            **st.session_state.config.get('trading', {})
        }
    
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

# Main content area
# Check if we have data source available
has_data_source = False
if st.session_state.data_source == 'MT5':
    has_data_source = st.session_state.mt5_connector and st.session_state.mt5_connector.is_connected()
else:  # CSV mode
    has_data_source = st.session_state.csv_data is not None

if has_data_source:
    # Account Info (only for MT5)
    if st.session_state.data_source == 'MT5':
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
    
    # Market Data and Signals
    st.header("📊 Market Analysis")
    
    # Show data source info
    if st.session_state.data_source == 'CSV':
        st.info(f"📁 Using CSV data: {len(st.session_state.csv_data)} rows loaded")
    
    symbol = st.session_state.config.get('trading', {}).get('symbol', 'EURUSD')
    
    # Get market data
    timeframes = ['M1', 'M5', 'M15', 'H1']
    market_data = get_market_data(symbol, timeframes)
    
    if market_data:
        # Get 5-minute data for main chart
        df_5m = market_data.get('M5')
        
        if df_5m is not None and len(df_5m) > 0:
            # Detect signals
            signals = detect_signals(symbol, market_data)
            
            # Create chart
            plotter = Plotter()
            fig = plotter.create_candlestick_chart(
                df_5m.tail(100),  # Show last 100 candles
                symbol,
                fvgs=signals.get('fvgs', []),
                bos_list=signals.get('bos', []),
                choch_list=signals.get('choch', []),
                liquidity_levels=signals.get('liquidity', {}),
                trades=st.session_state.trade_history
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display signals
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("FVG Zones", len(signals.get('fvgs', [])))
            
            with col2:
                st.metric("BOS Signals", len(signals.get('bos', [])))
            
            with col3:
                st.metric("CHoCH Signals", len(signals.get('choch', [])))
            
            with col4:
                if signals.get('trade_setup'):
                    st.success("✅ Trade Setup Detected!")
                else:
                    st.info("⏳ No Setup")
            
            # Trade Setup Details
            if signals.get('trade_setup'):
                st.subheader("🎯 Trade Setup")
                setup = signals['trade_setup']
                
                st.json({
                    'Direction': setup['direction'],
                    'Entry': setup['entry'],
                    'Stop Loss': setup['stop_loss'],
                    'Take Profit': setup['take_profit'],
                    'Confidence': setup['confidence']
                })
            
            # Open Positions (only for MT5)
            if st.session_state.data_source == 'MT5':
                st.subheader("📋 Open Positions")
                
                open_positions = st.session_state.mt5_connector.get_open_positions(symbol=symbol)
                
                if open_positions:
                    positions_df = pd.DataFrame(open_positions)
                    st.dataframe(positions_df, use_container_width=True)
                else:
                    st.info("No open positions")
            
            # Last Update
            if st.session_state.last_update:
                st.caption(f"Last update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Auto-refresh (only for MT5 live trading)
            if st.session_state.trading_active and st.session_state.data_source == 'MT5':
                time.sleep(1)
                st.rerun()
    
    else:
        if st.session_state.data_source == 'MT5':
            st.warning("Unable to fetch market data. Please check your MT5 connection.")
        else:
            st.warning("Unable to process CSV data. Please check the file format.")
    
else:
    if st.session_state.data_source == 'MT5':
        st.info("👈 Please connect to MT5 in the sidebar to start trading")
    else:
        st.info("👈 Please upload a CSV file in the sidebar to analyze data")

