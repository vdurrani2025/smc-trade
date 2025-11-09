"""
Utility functions for logging, plotting, and configuration
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional
import os
import io

logger = logging.getLogger(__name__)


class TradeLogger:
    """Handles trade logging to CSV and console"""
    
    def __init__(self, csv_file: str = "trade_history.csv"):
        """
        Initialize trade logger
        
        Args:
            csv_file: Path to CSV file for trade history
        """
        self.csv_file = csv_file
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'symbol', 'direction', 'lot_size', 'entry_price',
                    'stop_loss', 'take_profit', 'exit_price', 'profit_loss', 'status',
                    'comment'
                ])
    
    def log_trade(self, symbol: str, direction: str, lot_size: float,
                  entry_price: float, stop_loss: float, take_profit: float,
                  exit_price: Optional[float] = None, profit_loss: Optional[float] = None,
                  status: str = "OPEN", comment: str = ""):
        """
        Log a trade to CSV
        
        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            lot_size: Lot size
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            exit_price: Exit price (if closed)
            profit_loss: Profit/loss amount (if closed)
            status: 'OPEN' or 'CLOSED'
            comment: Additional comment
        """
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    symbol,
                    direction,
                    lot_size,
                    entry_price,
                    stop_loss,
                    take_profit,
                    exit_price or '',
                    profit_loss or '',
                    status,
                    comment
                ])
            logger.info(f"Trade logged: {direction} {symbol} @ {entry_price}")
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def update_trade(self, symbol: str, entry_price: float, exit_price: float,
                    profit_loss: float, comment: str = ""):
        """Update a trade when it's closed"""
        # This would require reading and updating the CSV
        # For simplicity, we'll just log the close event
        logger.info(f"Trade closed: {symbol} @ {entry_price} -> {exit_price}, P/L: {profit_loss}")


class Plotter:
    """Handles candlestick chart plotting with ICT overlays"""
    
    @staticmethod
    def create_candlestick_chart(df: pd.DataFrame, symbol: str, 
                                fvgs: List[Dict] = None,
                                bos_list: List[Dict] = None,
                                choch_list: List[Dict] = None,
                                liquidity_levels: Dict = None,
                                trades: List[Dict] = None) -> go.Figure:
        """
        Create a candlestick chart with ICT overlays
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            fvgs: List of FVG dictionaries
            bos_list: List of BOS dictionaries
            choch_list: List of CHoCH dictionaries
            liquidity_levels: Dictionary with liquidity levels
            trades: List of trade dictionaries
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # Add candlestick chart
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol
        ))
        
        # Add FVG zones
        if fvgs:
            for fvg in fvgs:
                color = 'rgba(0, 255, 0, 0.3)' if fvg['type'] == 'bullish' else 'rgba(255, 0, 0, 0.3)'
                fig.add_shape(
                    type="rect",
                    x0=fvg['start'],
                    x1=fvg['end'],
                    y0=fvg['low'],
                    y1=fvg['high'],
                    fillcolor=color,
                    line=dict(width=0),
                    layer="below"
                )
        
        # Add liquidity levels
        if liquidity_levels:
            fig.add_hline(
                y=liquidity_levels['high'],
                line_dash="dash",
                line_color="red",
                annotation_text="Liquidity High",
                annotation_position="right"
            )
            fig.add_hline(
                y=liquidity_levels['low'],
                line_dash="dash",
                line_color="blue",
                annotation_text="Liquidity Low",
                annotation_position="right"
            )
        
        # Add BOS markers
        if bos_list:
            for bos in bos_list:
                color = 'green' if bos['type'] == 'bullish' else 'red'
                fig.add_trace(go.Scatter(
                    x=[bos['time']],
                    y=[bos['break_price']],
                    mode='markers',
                    marker=dict(symbol='triangle-up' if bos['type'] == 'bullish' else 'triangle-down',
                              size=10, color=color),
                    name=f"BOS {bos['type']}",
                    showlegend=False
                ))
        
        # Add CHoCH markers
        if choch_list:
            for choch in choch_list:
                color = 'green' if choch['type'] == 'bullish' else 'red'
                fig.add_trace(go.Scatter(
                    x=[choch['time']],
                    y=[choch.get('to_bullish', choch.get('to_bearish', {}))['break_price']],
                    mode='markers',
                    marker=dict(symbol='star', size=12, color=color),
                    name=f"CHoCH {choch['type']}",
                    showlegend=False
                ))
        
        # Add trade markers
        if trades:
            for trade in trades:
                if trade.get('entry_price'):
                    fig.add_trace(go.Scatter(
                        x=[trade.get('entry_time', df.index[-1])],
                        y=[trade['entry_price']],
                        mode='markers',
                        marker=dict(symbol='arrow-up' if trade['direction'] == 'BUY' else 'arrow-down',
                                  size=15, color='yellow'),
                        name=f"Trade {trade['direction']}",
                        showlegend=False
                    ))
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - ICT Analysis",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=600,
            template="plotly_dark"
        )
        
        return fig


def load_config(config_file: str = "config.json") -> Dict:
    """
    Load configuration from JSON file
    
    Args:
        config_file: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_file} not found, using defaults")
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


def save_config(config: Dict, config_file: str = "config.json"):
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary
        config_file: Path to config file
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config: {e}")


def setup_logging(log_file: str = "trades.log", level: int = logging.INFO):
    """
    Setup logging configuration
    
    Args:
        log_file: Path to log file
        level: Logging level
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def is_friday_close_time(current_time: datetime, close_hour: int = 21) -> bool:
    """
    Check if current time is after Friday close time
    
    Args:
        current_time: Current datetime
        close_hour: Close hour (GMT)
        
    Returns:
        True if after Friday close time
    """
    # Check if it's Friday and after close hour
    if current_time.weekday() == 4:  # Friday
        if current_time.hour >= close_hour:
            return True
    # Check if it's Saturday or Sunday
    elif current_time.weekday() >= 5:
        return True
    return False


def calculate_pip_value(symbol: str, point: float) -> float:
    """
    Calculate pip value for a symbol
    
    Args:
        symbol: Trading symbol
        point: Point value from symbol info
        
    Returns:
        Pip value
    """
    # For most forex pairs, pip = point * 10 (for 4-digit quotes)
    # For JPY pairs, pip = point * 100
    if 'JPY' in symbol:
        return point * 100
    else:
        return point * 10


def parse_csv_file(csv_data: bytes, filename: str = "") -> Optional[pd.DataFrame]:
    """
    Parse CSV file with OHLCV data
    
    Supports multiple CSV formats:
    - Standard: Date/Time, Open, High, Low, Close, Volume
    - MT5 format: time, open, high, low, close, tick_volume, spread, real_volume
    - Generic: Any format with date/time and OHLC columns
    
    Args:
        csv_data: CSV file content as bytes
        filename: Optional filename for logging
        
    Returns:
        DataFrame with OHLCV data or None if error
    """
    try:
        # Try to read CSV with common encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    io.BytesIO(csv_data),
                    encoding=encoding,
                    parse_dates=True,
                    index_col=0,
                    infer_datetime_format=True
                )
                break
            except (UnicodeDecodeError, ValueError):
                continue
        
        if df is None:
            # Try without index_col
            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        io.BytesIO(csv_data),
                        encoding=encoding,
                        parse_dates=True,
                        infer_datetime_format=True
                    )
                    break
                except (UnicodeDecodeError, ValueError):
                    continue
        
        if df is None:
            logger.error("Failed to parse CSV file")
            return None
        
        # Normalize column names to lowercase
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Try to identify date/time column
        date_cols = ['date', 'time', 'datetime', 'timestamp', 'time', 'date_time']
        date_col = None
        
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
        
        # If date column found and not already index, set it as index
        if date_col and date_col in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
            except Exception as e:
                logger.warning(f"Could not parse date column {date_col}: {e}")
        
        # Identify OHLC columns (case-insensitive)
        ohlc_map = {
            'open': ['open', 'o'],
            'high': ['high', 'h'],
            'low': ['low', 'l'],
            'close': ['close', 'c'],
            'volume': ['volume', 'vol', 'v', 'tick_volume', 'real_volume']
        }
        
        # Map columns
        column_mapping = {}
        for standard_name, possible_names in ohlc_map.items():
            for col in df.columns:
                if col.lower() in possible_names:
                    column_mapping[col] = standard_name
                    break
        
        # Rename columns
        if column_mapping:
            df.rename(columns=column_mapping, inplace=True)
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            logger.info(f"Available columns: {df.columns.tolist()}")
            return None
        
        # Add volume if missing (set to 0)
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        # Select only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']].copy()
        
        # Ensure numeric types
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with NaN values
        df.dropna(inplace=True)
        
        # Sort by index (date)
        df.sort_index(inplace=True)
        
        logger.info(f"Successfully parsed CSV file: {len(df)} rows loaded")
        return df
        
    except Exception as e:
        logger.error(f"Error parsing CSV file: {e}")
        return None


def resample_to_timeframes(df: pd.DataFrame, base_timeframe: str = '5T') -> Dict[str, pd.DataFrame]:
    """
    Resample a DataFrame to multiple timeframes
    
    Args:
        df: DataFrame with OHLCV data (must have datetime index)
        base_timeframe: Base timeframe of the data (e.g., '5T' for 5 minutes)
        
    Returns:
        Dictionary with resampled DataFrames for different timeframes
    """
    if df is None or len(df) == 0:
        return {}
    
    if not isinstance(df.index, pd.DatetimeIndex):
        logger.error("DataFrame must have a DatetimeIndex for resampling")
        return {}
    
    resampled = {}
    
    try:
        # If base is 5 minutes, use it directly as M5
        if base_timeframe == '5T':
            resampled['M5'] = df.copy()
            logger.info(f"Using base data as M5: {len(df)} candles")
        
        # Define timeframe mappings (only higher timeframes for aggregation)
        timeframe_map = {
            'M15': '15T', # 15 minutes
            'H1': '1H'    # 1 hour
        }
        
        # For 5-minute data, we can only aggregate to higher timeframes
        # We cannot create 1-minute data from 5-minute data
        if base_timeframe == '5T':
            # Only resample to higher timeframes
            for tf_key, tf_value in timeframe_map.items():
                try:
                    # Use OHLC resampling (proper for candlestick data)
                    resampled_df = df.resample(tf_value).agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    
                    if len(resampled_df) > 0:
                        resampled[tf_key] = resampled_df
                        logger.info(f"Resampled to {tf_key}: {len(resampled_df)} candles")
                except Exception as e:
                    logger.warning(f"Could not resample to {tf_key}: {e}")
            
            # For M1, we'll use the 5-minute data (not ideal but better than nothing)
            # In practice, you'd need actual 1-minute data
            resampled['M1'] = df.copy()
            logger.info(f"Using M5 data as M1 (approximation): {len(df)} candles")
        else:
            # For other base timeframes, resample to all timeframes
            timeframe_map_all = {
                'M1': '1T',
                'M5': '5T',
                'M15': '15T',
                'H1': '1H'
            }
            
            for tf_key, tf_value in timeframe_map_all.items():
                try:
                    resampled_df = df.resample(tf_value).agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    
                    if len(resampled_df) > 0:
                        resampled[tf_key] = resampled_df
                        logger.info(f"Resampled to {tf_key}: {len(resampled_df)} candles")
                except Exception as e:
                    logger.warning(f"Could not resample to {tf_key}: {e}")
        
        return resampled
        
    except Exception as e:
        logger.error(f"Error resampling data: {e}")
        return {}

