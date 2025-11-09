"""
Smart Money Concept (ICT) Detection Logic
Implements detection for FVG, BOS, CHoCH, and Liquidity Grab patterns
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ICTDetector:
    """Detects Smart Money Concept patterns"""
    
    def __init__(self):
        """Initialize ICT detector"""
        pass
    
    def detect_fvg(self, df: pd.DataFrame, lookback: int = 3) -> List[Dict]:
        """
        Detect Fair Value Gaps (FVG)
        FVG is an imbalance gap where no overlap exists between candle highs/lows
        across three consecutive bars
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to look back
            
        Returns:
            List of FVG dictionaries with 'start', 'end', 'high', 'low', 'type'
        """
        if len(df) < lookback + 1:
            return []
        
        fvgs = []
        
        for i in range(lookback, len(df)):
            # Get three consecutive candles
            c1 = df.iloc[i - 2]  # First candle
            c2 = df.iloc[i - 1]  # Middle candle (gap)
            c3 = df.iloc[i]      # Third candle
            
            # Bullish FVG: gap up - no overlap between c1 high and c3 low
            if c2.low > c1.high and c3.low > c1.high:
                fvg_high = min(c2.low, c3.low)
                fvg_low = max(c1.high, c2.open)
                if fvg_high > fvg_low:
                    fvgs.append({
                        'index': i - 1,
                        'start': df.index[i - 2],
                        'end': df.index[i],
                        'high': fvg_high,
                        'low': fvg_low,
                        'type': 'bullish',
                        'filled': False
                    })
            
            # Bearish FVG: gap down - no overlap between c1 low and c3 high
            elif c2.high < c1.low and c3.high < c1.low:
                fvg_high = min(c1.low, c2.open)
                fvg_low = max(c2.high, c3.high)
                if fvg_high > fvg_low:
                    fvgs.append({
                        'index': i - 1,
                        'start': df.index[i - 2],
                        'end': df.index[i],
                        'high': fvg_high,
                        'low': fvg_low,
                        'type': 'bearish',
                        'filled': False
                    })
        
        return fvgs
    
    def check_fvg_filled(self, fvg: Dict, df: pd.DataFrame, start_idx: int) -> bool:
        """
        Check if FVG has been filled (price has moved through it)
        
        Args:
            fvg: FVG dictionary
            df: DataFrame with OHLCV data
            start_idx: Starting index to check from
            
        Returns:
            True if FVG is filled, False otherwise
        """
        if start_idx >= len(df):
            return False
        
        for i in range(start_idx, len(df)):
            candle = df.iloc[i]
            
            if fvg['type'] == 'bullish':
                # Bullish FVG filled if price goes below FVG low
                if candle.low <= fvg['low']:
                    return True
            else:
                # Bearish FVG filled if price goes above FVG high
                if candle.high >= fvg['high']:
                    return True
        
        return False
    
    def detect_bos(self, df: pd.DataFrame, swing_lookback: int = 10) -> List[Dict]:
        """
        Detect Break of Structure (BOS)
        BOS occurs when a candle closes beyond a previous swing point
        
        Args:
            df: DataFrame with OHLCV data
            swing_lookback: Number of bars to look back for swing points
            
        Returns:
            List of BOS dictionaries
        """
        if len(df) < swing_lookback + 1:
            return []
        
        bos_list = []
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(swing_lookback, len(df) - swing_lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(i - swing_lookback, i + swing_lookback + 1):
                if j != i and df.iloc[j].high >= df.iloc[i].high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': df.iloc[i].high,
                    'time': df.index[i]
                })
            
            # Check for swing low
            is_swing_low = True
            for j in range(i - swing_lookback, i + swing_lookback + 1):
                if j != i and df.iloc[j].low <= df.iloc[i].low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': df.iloc[i].low,
                    'time': df.index[i]
                })
        
        # Detect BOS
        for i in range(swing_lookback, len(df)):
            candle = df.iloc[i]
            
            # Bullish BOS: close above previous swing high
            for swing in swing_highs:
                if swing['index'] < i and candle.close > swing['price']:
                    # Check if this is a new BOS (not already detected)
                    is_new = True
                    for existing_bos in bos_list:
                        if existing_bos['swing_index'] == swing['index']:
                            is_new = False
                            break
                    
                    if is_new:
                        bos_list.append({
                            'index': i,
                            'time': df.index[i],
                            'type': 'bullish',
                            'swing_index': swing['index'],
                            'swing_price': swing['price'],
                            'break_price': candle.close
                        })
                    break
            
            # Bearish BOS: close below previous swing low
            for swing in swing_lows:
                if swing['index'] < i and candle.close < swing['price']:
                    # Check if this is a new BOS
                    is_new = True
                    for existing_bos in bos_list:
                        if existing_bos['swing_index'] == swing['index']:
                            is_new = False
                            break
                    
                    if is_new:
                        bos_list.append({
                            'index': i,
                            'time': df.index[i],
                            'type': 'bearish',
                            'swing_index': swing['index'],
                            'swing_price': swing['price'],
                            'break_price': candle.close
                        })
                    break
        
        return bos_list
    
    def detect_choch(self, df: pd.DataFrame, swing_lookback: int = 10) -> List[Dict]:
        """
        Detect Change of Character (CHoCH)
        CHoCH is the first structure shift opposite to the existing trend
        
        Args:
            df: DataFrame with OHLCV data
            swing_lookback: Number of bars to look back for swing points
            
        Returns:
            List of CHoCH dictionaries
        """
        if len(df) < swing_lookback * 2:
            return []
        
        choch_list = []
        
        # First, detect BOS to understand structure
        bos_list = self.detect_bos(df, swing_lookback)
        
        if len(bos_list) < 2:
            return []
        
        # CHoCH occurs when structure changes direction
        for i in range(1, len(bos_list)):
            prev_bos = bos_list[i - 1]
            curr_bos = bos_list[i]
            
            # Bullish CHoCH: previous bearish BOS followed by bullish BOS
            if prev_bos['type'] == 'bearish' and curr_bos['type'] == 'bullish':
                choch_list.append({
                    'index': curr_bos['index'],
                    'time': curr_bos['time'],
                    'type': 'bullish',
                    'from_bearish': prev_bos,
                    'to_bullish': curr_bos
                })
            
            # Bearish CHoCH: previous bullish BOS followed by bearish BOS
            elif prev_bos['type'] == 'bullish' and curr_bos['type'] == 'bearish':
                choch_list.append({
                    'index': curr_bos['index'],
                    'time': curr_bos['time'],
                    'type': 'bearish',
                    'from_bullish': prev_bos,
                    'to_bearish': curr_bos
                })
        
        return choch_list
    
    def detect_liquidity_grab(self, df: pd.DataFrame, lookback: int = 20) -> List[Dict]:
        """
        Detect Liquidity Grab
        Liquidity grab: wick breaks previous high/low and closes back inside
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to look back for previous highs/lows
            
        Returns:
            List of liquidity grab dictionaries
        """
        if len(df) < lookback + 1:
            return []
        
        liquidity_grabs = []
        
        for i in range(lookback, len(df)):
            candle = df.iloc[i]
            
            # Look back for previous highs and lows
            prev_data = df.iloc[i - lookback:i]
            prev_high = prev_data['high'].max()
            prev_low = prev_data['low'].min()
            
            # Bullish liquidity grab: wick breaks previous low, closes above
            if candle.low < prev_low and candle.close > prev_low:
                liquidity_grabs.append({
                    'index': i,
                    'time': df.index[i],
                    'type': 'bullish',
                    'liquidity_level': prev_low,
                    'wick_low': candle.low,
                    'close': candle.close,
                    'swept': True
                })
            
            # Bearish liquidity grab: wick breaks previous high, closes below
            elif candle.high > prev_high and candle.close < prev_high:
                liquidity_grabs.append({
                    'index': i,
                    'time': df.index[i],
                    'type': 'bearish',
                    'liquidity_level': prev_high,
                    'wick_high': candle.high,
                    'close': candle.close,
                    'swept': True
                })
        
        return liquidity_grabs
    
    def find_liquidity_levels(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Find current liquidity levels (recent highs and lows)
        
        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to look back
            
        Returns:
            Dictionary with 'high' and 'low' liquidity levels
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_data = df.iloc[-lookback:]
        
        return {
            'high': recent_data['high'].max(),
            'low': recent_data['low'].min(),
            'high_time': recent_data['high'].idxmax(),
            'low_time': recent_data['low'].idxmin()
        }
    
    def detect_trade_setup(self, df_1m: pd.DataFrame, df_5m: pd.DataFrame,
                          df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Optional[Dict]:
        """
        Detect complete trade setup based on ICT rules:
        - Entry Trigger: Liquidity sweep → CHoCH confirmation → FVG mitigation
        
        Args:
            df_1m: 1-minute data
            df_5m: 5-minute data
            df_15m: 15-minute data
            df_1h: 1-hour data
            
        Returns:
            Trade setup dictionary or None
        """
        try:
            # Detect liquidity grab on 15m or 1h
            liquidity_15m = self.detect_liquidity_grab(df_15m)
            liquidity_1h = self.detect_liquidity_grab(df_1h)
            
            # Check for recent liquidity grab
            recent_liquidity = None
            if liquidity_15m:
                recent_liquidity = liquidity_15m[-1]
            elif liquidity_1h:
                recent_liquidity = liquidity_1h[-1]
            
            if recent_liquidity is None:
                return None
            
            # Detect CHoCH on 1m or 5m
            choch_1m = self.detect_choch(df_1m)
            choch_5m = self.detect_choch(df_5m)
            
            # Check for recent CHoCH
            recent_choch = None
            if choch_5m:
                recent_choch = choch_5m[-1]
            elif choch_1m:
                recent_choch = choch_1m[-1]
            
            if recent_choch is None:
                return None
            
            # Detect FVG on 1m or 5m
            fvg_1m = self.detect_fvg(df_1m)
            fvg_5m = self.detect_fvg(df_5m)
            
            # Check for unfilled FVG
            all_fvgs = fvg_1m + fvg_5m
            unfilled_fvg = None
            
            for fvg in reversed(all_fvgs):
                if not fvg.get('filled', False):
                    # Check if FVG is in the direction of the trade
                    if recent_choch['type'] == 'bullish' and fvg['type'] == 'bullish':
                        unfilled_fvg = fvg
                        break
                    elif recent_choch['type'] == 'bearish' and fvg['type'] == 'bearish':
                        unfilled_fvg = fvg
                        break
            
            if unfilled_fvg is None:
                return None
            
            # Check if liquidity grab happened before CHoCH
            if recent_liquidity['time'] > recent_choch['time']:
                return None
            
            # Determine trade direction
            direction = recent_choch['type']  # 'bullish' or 'bearish'
            
            # Get current price
            current_price = df_5m.iloc[-1]['close']
            
            # Calculate entry, stop loss, and take profit
            if direction == 'bullish':
                entry = unfilled_fvg['low']  # Enter at FVG low
                stop_loss = recent_liquidity['liquidity_level'] - 0.0001  # Below liquidity
                take_profit = entry + (entry - stop_loss) * 2  # 1:2 RR
            else:
                entry = unfilled_fvg['high']  # Enter at FVG high
                stop_loss = recent_liquidity['liquidity_level'] + 0.0001  # Above liquidity
                take_profit = entry - (stop_loss - entry) * 2  # 1:2 RR
            
            return {
                'direction': direction,
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'liquidity_grab': recent_liquidity,
                'choch': recent_choch,
                'fvg': unfilled_fvg,
                'confidence': 'high'  # All conditions met
            }
            
        except Exception as e:
            logger.error(f"Error detecting trade setup: {e}")
            return None

