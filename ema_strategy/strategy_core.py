"""
EMA Crossover Strategy Core Logic
Implements the EMA8-EMA20 crossover strategy with multiple modes and filters
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging
from datetime import datetime

from ema_strategy.indicators import (
    calculate_ema, calculate_adx, calculate_esi,
    detect_engulfing_pattern, detect_pullback, detect_ema_crossover
)

logger = logging.getLogger(__name__)


class EMAStrategy:
    """EMA8-EMA20 Crossover Strategy"""
    
    def __init__(self, config: Dict):
        """
        Initialize strategy with configuration
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config
        self.strategy_mode = config.get('strategy_mode', 'Intraday')
        self.ema_fast = config.get('ema_fast', 8)
        self.ema_slow = config.get('ema_slow', 20)
        self.timeframe_entry = config.get('timeframe_entry', 'M15')
        self.timeframe_confirmation = config.get('timeframe_confirmation', 'H1')
        
        # Filters
        self.enable_esi_check = config.get('enable_esi_check', False)
        self.enable_adx_check = config.get('enable_adx_check', True)
        self.adx_threshold = config.get('adx_threshold', 25)
        self.pullback_confirmation = config.get('pullback_confirmation', True)
        
        # Risk parameters
        self.stop_loss_pips = config.get('stop_loss_pips', 20)
        self.take_profit_pips = config.get('take_profit_pips', 40)
        self.trailing_stop_pips = config.get('trailing_stop_pips', 15)
        self.use_trailing_stop = config.get('use_trailing_stop', True)
        self.max_open_trades = config.get('max_open_trades', 1)
        
    def calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate all required indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with calculated indicators
        """
        try:
            indicators = {}
            
            # Calculate EMAs
            indicators['ema_fast'] = calculate_ema(df['close'], self.ema_fast)
            indicators['ema_slow'] = calculate_ema(df['close'], self.ema_slow)
            
            # Calculate ADX if enabled
            if self.enable_adx_check:
                adx_data = calculate_adx(df['high'], df['low'], df['close'])
                indicators['adx'] = adx_data['adx']
                indicators['+di'] = adx_data['+di']
                indicators['-di'] = adx_data['-di']
            
            # Calculate ESI if enabled
            if self.enable_esi_check:
                indicators['esi'] = calculate_esi(df['high'], df['low'], df['close'])
            
            # Detect patterns
            if self.pullback_confirmation:
                indicators['engulfing'] = detect_engulfing_pattern(df)
                indicators['pullback'] = detect_pullback(df, indicators['ema_fast'], indicators['ema_slow'])
            
            # Detect EMA crossover
            indicators['crossover'] = detect_ema_crossover(indicators['ema_fast'], indicators['ema_slow'])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def check_higher_timeframe_trend(self, df_confirmation: pd.DataFrame) -> Optional[int]:
        """
        Check trend direction on higher timeframe
        
        Args:
            df_confirmation: DataFrame from higher timeframe
            
        Returns:
            1 for uptrend, -1 for downtrend, None if unclear
        """
        try:
            if df_confirmation is None or len(df_confirmation) < 2:
                return None
            
            # Calculate EMAs on higher timeframe
            ema_fast_htf = calculate_ema(df_confirmation['close'], self.ema_fast)
            ema_slow_htf = calculate_ema(df_confirmation['close'], self.ema_slow)
            
            # Check current trend
            if ema_fast_htf.iloc[-1] > ema_slow_htf.iloc[-1]:
                return 1  # Uptrend
            elif ema_fast_htf.iloc[-1] < ema_slow_htf.iloc[-1]:
                return -1  # Downtrend
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error checking higher timeframe trend: {e}")
            return None
    
    def validate_buy_signal(self, df: pd.DataFrame, indicators: Dict, 
                            df_confirmation: Optional[pd.DataFrame] = None) -> bool:
        """
        Validate buy signal with all filters
        
        Args:
            df: DataFrame with OHLCV data
            indicators: Dictionary with calculated indicators
            df_confirmation: Higher timeframe data (optional)
            
        Returns:
            True if buy signal is valid
        """
        try:
            if len(df) < 2:
                return False
            
            current_idx = len(df) - 1
            
            # 1. Check for bullish EMA crossover
            if indicators.get('crossover', pd.Series()).iloc[current_idx] != 1:
                return False
            
            # 2. Check higher timeframe trend (if enabled)
            if df_confirmation is not None:
                htf_trend = self.check_higher_timeframe_trend(df_confirmation)
                if htf_trend is not None and htf_trend != 1:
                    return False
            
            # 3. Check ADX filter (if enabled)
            if self.enable_adx_check:
                adx = indicators.get('adx', pd.Series())
                if len(adx) > current_idx:
                    if adx.iloc[current_idx] < self.adx_threshold:
                        return False
            
            # 4. Check ESI filter (if enabled)
            if self.enable_esi_check:
                esi = indicators.get('esi', pd.Series())
                if len(esi) > current_idx:
                    if esi.iloc[current_idx] < 50:  # ESI should be above neutral
                        return False
            
            # 5. Check pullback confirmation (if enabled)
            if self.pullback_confirmation:
                pullback = indicators.get('pullback', pd.Series())
                engulfing = indicators.get('engulfing', pd.Series())
                
                # Either pullback or bullish engulfing
                if len(pullback) > current_idx and len(engulfing) > current_idx:
                    if pullback.iloc[current_idx] != 1 and engulfing.iloc[current_idx] != 1:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating buy signal: {e}")
            return False
    
    def validate_sell_signal(self, df: pd.DataFrame, indicators: Dict,
                            df_confirmation: Optional[pd.DataFrame] = None) -> bool:
        """
        Validate sell signal with all filters
        
        Args:
            df: DataFrame with OHLCV data
            indicators: Dictionary with calculated indicators
            df_confirmation: Higher timeframe data (optional)
            
        Returns:
            True if sell signal is valid
        """
        try:
            if len(df) < 2:
                return False
            
            current_idx = len(df) - 1
            
            # 1. Check for bearish EMA crossover
            if indicators.get('crossover', pd.Series()).iloc[current_idx] != -1:
                return False
            
            # 2. Check higher timeframe trend (if enabled)
            if df_confirmation is not None:
                htf_trend = self.check_higher_timeframe_trend(df_confirmation)
                if htf_trend is not None and htf_trend != -1:
                    return False
            
            # 3. Check ADX filter (if enabled)
            if self.enable_adx_check:
                adx = indicators.get('adx', pd.Series())
                if len(adx) > current_idx:
                    if adx.iloc[current_idx] < self.adx_threshold:
                        return False
            
            # 4. Check ESI filter (if enabled)
            if self.enable_esi_check:
                esi = indicators.get('esi', pd.Series())
                if len(esi) > current_idx:
                    if esi.iloc[current_idx] > 50:  # ESI should be below neutral
                        return False
            
            # 5. Check pullback confirmation (if enabled)
            if self.pullback_confirmation:
                pullback = indicators.get('pullback', pd.Series())
                engulfing = indicators.get('engulfing', pd.Series())
                
                # Either pullback or bearish engulfing
                if len(pullback) > current_idx and len(engulfing) > current_idx:
                    if pullback.iloc[current_idx] != -1 and engulfing.iloc[current_idx] != -1:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating sell signal: {e}")
            return False
    
    def detect_signals(self, df_entry: pd.DataFrame, 
                      df_confirmation: Optional[pd.DataFrame] = None) -> Dict:
        """
        Detect trading signals
        
        Args:
            df_entry: DataFrame from entry timeframe
            df_confirmation: DataFrame from higher timeframe (optional)
            
        Returns:
            Dictionary with signal information
        """
        try:
            signals = {
                'buy_signal': False,
                'sell_signal': False,
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'direction': None
            }
            
            # Calculate indicators
            indicators = self.calculate_indicators(df_entry)
            
            if not indicators:
                return signals
            
            # Check for buy signal
            if self.validate_buy_signal(df_entry, indicators, df_confirmation):
                current_price = df_entry['close'].iloc[-1]
                signals['buy_signal'] = True
                signals['direction'] = 'BUY'
                signals['entry_price'] = current_price
                signals['stop_loss'] = current_price - (self.stop_loss_pips * 0.0001)  # Approximate for forex
                signals['take_profit'] = current_price + (self.take_profit_pips * 0.0001)
            
            # Check for sell signal
            elif self.validate_sell_signal(df_entry, indicators, df_confirmation):
                current_price = df_entry['close'].iloc[-1]
                signals['sell_signal'] = True
                signals['direction'] = 'SELL'
                signals['entry_price'] = current_price
                signals['stop_loss'] = current_price + (self.stop_loss_pips * 0.0001)
                signals['take_profit'] = current_price - (self.take_profit_pips * 0.0001)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error detecting signals: {e}")
            return {
                'buy_signal': False,
                'sell_signal': False,
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'direction': None
            }

