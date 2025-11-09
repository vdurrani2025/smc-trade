"""
Technical Indicators Module
Implements EMA, ADX, ESI, and other indicators for the EMA crossover strategy
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA)
    
    Args:
        data: Price series (typically close prices)
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
    """
    Calculate Average Directional Index (ADX)
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ADX period (default 14)
        
    Returns:
        Dictionary with 'adx', '+di', '-di' series
    """
    try:
        # Calculate True Range (TR)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Calculate smoothed TR and DM
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Calculate ADX
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx,
            '+di': plus_di,
            '-di': minus_di
        }
    except Exception as e:
        logger.error(f"Error calculating ADX: {e}")
        return {
            'adx': pd.Series(index=close.index, dtype=float),
            '+di': pd.Series(index=close.index, dtype=float),
            '-di': pd.Series(index=close.index, dtype=float)
        }


def calculate_esi(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Entry Strength Index (ESI)
    Custom indicator to measure momentum strength
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ESI period
        
    Returns:
        Series with ESI values (0-100 scale)
    """
    try:
        # Calculate price change
        price_change = close.diff()
        
        # Calculate volatility (True Range)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate momentum strength
        momentum = price_change / tr.replace(0, np.nan)
        
        # Normalize to 0-100 scale
        esi = momentum.rolling(window=period).mean() * 100
        
        # Clip to 0-100 range
        esi = esi.clip(lower=0, upper=100)
        
        return esi.fillna(50)  # Default to neutral (50)
    except Exception as e:
        logger.error(f"Error calculating ESI: {e}")
        return pd.Series(index=close.index, dtype=float).fillna(50)


def detect_engulfing_pattern(df: pd.DataFrame) -> pd.Series:
    """
    Detect bullish and bearish engulfing patterns
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        Series with values: 1 (bullish engulfing), -1 (bearish engulfing), 0 (none)
    """
    try:
        result = pd.Series(0, index=df.index)
        
        for i in range(1, len(df)):
            prev_candle = df.iloc[i - 1]
            curr_candle = df.iloc[i]
            
            # Bullish engulfing: current candle engulfs previous bearish candle
            if (prev_candle['close'] < prev_candle['open'] and  # Previous was bearish
                curr_candle['open'] < prev_candle['close'] and  # Current opens below prev close
                curr_candle['close'] > prev_candle['open']):     # Current closes above prev open
                result.iloc[i] = 1
            
            # Bearish engulfing: current candle engulfs previous bullish candle
            elif (prev_candle['close'] > prev_candle['open'] and  # Previous was bullish
                  curr_candle['open'] > prev_candle['close'] and  # Current opens above prev close
                  curr_candle['close'] < prev_candle['open']):     # Current closes below prev open
                result.iloc[i] = -1
        
        return result
    except Exception as e:
        logger.error(f"Error detecting engulfing patterns: {e}")
        return pd.Series(0, index=df.index)


def detect_pullback(df: pd.DataFrame, ema_fast: pd.Series, ema_slow: pd.Series, 
                    lookback: int = 3) -> pd.Series:
    """
    Detect pullback in trend direction
    
    Args:
        df: DataFrame with OHLC data
        ema_fast: Fast EMA series
        ema_slow: Slow EMA series
        lookback: Number of candles to look back
        
    Returns:
        Series with values: 1 (bullish pullback), -1 (bearish pullback), 0 (none)
    """
    try:
        result = pd.Series(0, index=df.index)
        
        # Determine trend direction
        trend = (ema_fast > ema_slow).astype(int) - (ema_fast < ema_slow).astype(int)
        
        for i in range(lookback, len(df)):
            # Check if we're in an uptrend
            if trend.iloc[i] > 0:  # Uptrend
                # Check for pullback (price dips but stays above EMA)
                recent_lows = df.iloc[i - lookback:i]['low']
                if (recent_lows.min() < df.iloc[i]['close'] and  # Price dipped
                    df.iloc[i]['close'] > ema_fast.iloc[i]):    # But still above EMA
                    result.iloc[i] = 1
            
            # Check if we're in a downtrend
            elif trend.iloc[i] < 0:  # Downtrend
                # Check for pullback (price rallies but stays below EMA)
                recent_highs = df.iloc[i - lookback:i]['high']
                if (recent_highs.max() > df.iloc[i]['close'] and  # Price rallied
                    df.iloc[i]['close'] < ema_fast.iloc[i]):     # But still below EMA
                    result.iloc[i] = -1
        
        return result
    except Exception as e:
        logger.error(f"Error detecting pullback: {e}")
        return pd.Series(0, index=df.index)


def detect_ema_crossover(ema_fast: pd.Series, ema_slow: pd.Series) -> pd.Series:
    """
    Detect EMA crossover signals
    
    Args:
        ema_fast: Fast EMA series
        ema_slow: Slow EMA series
        
    Returns:
        Series with values: 1 (bullish crossover), -1 (bearish crossover), 0 (none)
    """
    try:
        # Calculate crossover
        crossover = pd.Series(0, index=ema_fast.index)
        
        # Bullish crossover: fast EMA crosses above slow EMA
        bullish = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        crossover[bullish] = 1
        
        # Bearish crossover: fast EMA crosses below slow EMA
        bearish = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))
        crossover[bearish] = -1
        
        return crossover
    except Exception as e:
        logger.error(f"Error detecting EMA crossover: {e}")
        return pd.Series(0, index=ema_fast.index)

