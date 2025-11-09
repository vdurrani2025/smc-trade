"""
Risk Management Module
Handles position sizing, risk calculation, and trailing stop management
"""

import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk and position sizing"""
    
    def __init__(self, config: Dict):
        """
        Initialize risk manager
        
        Args:
            config: Strategy configuration dictionary
        """
        self.config = config
        self.lot_size = config.get('lot_size', 0.1)
        self.risk_per_trade = config.get('risk_per_trade', 1.0)  # Percentage
        self.max_open_trades = config.get('max_open_trades', 1)
        self.use_fixed_lot = config.get('use_fixed_lot', False)
        
    def calculate_lot_size(self, account_balance: float, stop_loss_pips: float,
                          symbol: str, point_value: float = 0.0001) -> float:
        """
        Calculate lot size based on risk percentage
        
        Args:
            account_balance: Account balance
            stop_loss_pips: Stop loss in pips
            symbol: Trading symbol
            point_value: Point value (default 0.0001 for most forex pairs)
            
        Returns:
            Lot size
        """
        try:
            if self.use_fixed_lot:
                return self.lot_size
            
            # Calculate risk amount
            risk_amount = account_balance * (self.risk_per_trade / 100.0)
            
            # Calculate pip value
            # For most forex pairs: pip value = lot_size * 100000 * point_value
            # Simplified calculation
            if stop_loss_pips == 0:
                return self.lot_size
            
            # Calculate lot size based on risk
            # Risk = Lot Size * Stop Loss Pips * Pip Value
            # Lot Size = Risk / (Stop Loss Pips * Pip Value)
            pip_value = point_value * 10  # Convert point to pip
            lot_size = risk_amount / (stop_loss_pips * pip_value * 100000)
            
            # Round to valid lot size (usually 0.01 increments)
            lot_size = round(lot_size, 2)
            
            # Ensure minimum lot size
            if lot_size < 0.01:
                lot_size = 0.01
            
            # Ensure maximum lot size (safety limit)
            if lot_size > 10.0:
                lot_size = 10.0
            
            return lot_size
            
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}")
            return self.lot_size
    
    def check_max_positions(self, current_positions: int) -> bool:
        """
        Check if we can open a new position
        
        Args:
            current_positions: Current number of open positions
            
        Returns:
            True if we can open a new position
        """
        return current_positions < self.max_open_trades
    
    def calculate_trailing_stop(self, entry_price: float, current_price: float,
                               direction: str, trailing_pips: float) -> Optional[float]:
        """
        Calculate trailing stop loss price
        
        Args:
            entry_price: Entry price
            current_price: Current market price
            direction: 'BUY' or 'SELL'
            trailing_pips: Trailing stop distance in pips
            
        Returns:
            New stop loss price or None if trailing stop shouldn't be updated
        """
        try:
            trailing_distance = trailing_pips * 0.0001  # Convert pips to price
            
            if direction == 'BUY':
                # For long positions, trailing stop moves up
                new_sl = current_price - trailing_distance
                # Only update if new SL is higher than entry
                if new_sl > entry_price:
                    return new_sl
            else:  # SELL
                # For short positions, trailing stop moves down
                new_sl = current_price + trailing_distance
                # Only update if new SL is lower than entry
                if new_sl < entry_price:
                    return new_sl
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating trailing stop: {e}")
            return None
    
    def should_update_trailing_stop(self, entry_price: float, current_price: float,
                                   current_sl: float, direction: str,
                                   trailing_pips: float) -> bool:
        """
        Check if trailing stop should be updated
        
        Args:
            entry_price: Entry price
            current_price: Current market price
            current_sl: Current stop loss price
            direction: 'BUY' or 'SELL'
            trailing_pips: Trailing stop distance in pips
            
        Returns:
            True if trailing stop should be updated
        """
        try:
            new_sl = self.calculate_trailing_stop(entry_price, current_price, direction, trailing_pips)
            
            if new_sl is None:
                return False
            
            if direction == 'BUY':
                # For long positions, update if new SL is higher than current SL
                return new_sl > current_sl
            else:  # SELL
                # For short positions, update if new SL is lower than current SL
                return new_sl < current_sl
                
        except Exception as e:
            logger.error(f"Error checking trailing stop update: {e}")
            return False

