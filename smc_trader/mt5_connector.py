"""
MT5 Connector Module
Handles MetaTrader 5 connection, data fetching, and order execution
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class MT5Connector:
    """Handles all MT5 operations including connection, data fetching, and trading"""
    
    def __init__(self, login: int = 0, password: str = "", server: str = "", path: str = ""):
        """
        Initialize MT5 connector
        
        Args:
            login: MT5 account login
            password: MT5 account password
            server: MT5 server name
            path: Path to MT5 terminal (optional, uses default if empty)
        """
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.connected = False
        self.account_info = None
        
    def connect(self) -> bool:
        """Connect to MT5 terminal"""
        try:
            # Initialize MT5
            if not mt5.initialize(path=self.path if self.path else None):
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login if credentials provided
            if self.login and self.password and self.server:
                authorized = mt5.login(self.login, password=self.password, server=self.server)
                if not authorized:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
                logger.info(f"Successfully logged in to MT5 account {self.login}")
            else:
                logger.info("Using default MT5 account (no login provided)")
            
            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.error("Failed to get account info")
                mt5.shutdown()
                return False
            
            self.connected = True
            logger.info(f"Connected to MT5. Balance: {self.account_info.balance}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        return self.connected and mt5.terminal_info() is not None
    
    def get_account_info(self) -> Optional[Dict]:
        """Get current account information"""
        if not self.is_connected():
            return None
        
        try:
            account = mt5.account_info()
            if account is None:
                return None
            
            positions = mt5.positions_get()
            open_pnl = sum([pos.profit for pos in positions]) if positions else 0.0
            
            return {
                "balance": account.balance,
                "equity": account.equity,
                "margin": account.margin,
                "free_margin": account.margin_free,
                "open_pnl": open_pnl,
                "number_of_positions": len(positions) if positions else 0
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_rates(self, symbol: str, timeframe: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe string ('M1', 'M5', 'M15', 'H1', etc.)
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        try:
            # Map timeframe string to MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }
            
            if timeframe not in timeframe_map:
                logger.error(f"Unsupported timeframe: {timeframe}")
                return None
            
            mt5_timeframe = timeframe_map[timeframe]
            
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.error(f"Failed to get rates for {symbol} on {timeframe}: {mt5.last_error()}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns to lowercase
            df.columns = [col.lower() for col in df.columns]
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting rates for {symbol} {timeframe}: {e}")
            return None
    
    def get_latest_rates(self, symbol: str, timeframe: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get latest rates (refreshed data)"""
        return self.get_rates(symbol, timeframe, count)
    
    def symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information including point value, digits, etc."""
        if not self.is_connected():
            return None
        
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                logger.error(f"Symbol {symbol} not found")
                return None
            
            return {
                "name": info.name,
                "point": info.point,
                "digits": info.digits,
                "spread": info.spread,
                "trade_mode": info.trade_mode,
                "contract_size": info.trade_contract_size,
                "currency_profit": info.currency_profit,
                "currency_margin": info.currency_margin
            }
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def calculate_lot_size(self, account_balance: float, risk_percent: float, 
                          stop_loss_pips: float, symbol: str) -> float:
        """
        Calculate lot size based on risk percentage
        
        Args:
            account_balance: Account balance
            risk_percent: Risk percentage (e.g., 1.0 for 1%)
            stop_loss_pips: Stop loss in pips
            symbol: Trading symbol
            
        Returns:
            Lot size
        """
        try:
            symbol_info = self.symbol_info(symbol)
            if symbol_info is None:
                return 0.01  # Default
            
            risk_amount = account_balance * (risk_percent / 100.0)
            point_value = symbol_info['point']
            contract_size = symbol_info['contract_size']
            
            # Calculate lot size
            # For forex: pip value = (lot_size * contract_size * point) / quote_currency_rate
            # Simplified calculation
            pip_value = stop_loss_pips * point_value * 10  # Assuming 4-digit quote
            if pip_value == 0:
                return 0.01
            
            lot_size = risk_amount / (pip_value * contract_size)
            
            # Round to valid lot size (usually 0.01 increments)
            lot_size = round(lot_size, 2)
            
            # Ensure minimum lot size
            if lot_size < 0.01:
                lot_size = 0.01
            
            return lot_size
            
        except Exception as e:
            logger.error(f"Error calculating lot size: {e}")
            return 0.01
    
    def place_order(self, symbol: str, order_type: str, lot_size: float, 
                   price: float = 0.0, sl: float = 0.0, tp: float = 0.0,
                   comment: str = "ICT Bot") -> Optional[int]:
        """
        Place a market order
        
        Args:
            symbol: Trading symbol
            order_type: 'BUY' or 'SELL'
            lot_size: Lot size
            price: Entry price (0 for market order)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Order ticket if successful, None otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None
        
        try:
            symbol_info = self.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            # Get current price
            if price == 0.0:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    logger.error(f"Failed to get tick for {symbol}")
                    return None
                price = tick.ask if order_type == "BUY" else tick.bid
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": sl if sl > 0 else 0,
                "tp": tp if tp > 0 else 0,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
            
            logger.info(f"Order placed successfully: {order_type} {lot_size} {symbol} @ {price}")
            return result.order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        if not self.is_connected():
            return False
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                logger.error(f"Position {ticket} not found")
                return False
            
            pos = position[0]
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "deviation": 20,
                "magic": 234000,
                "comment": "Close ICT",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close order failed: {result.retcode} - {result.comment}")
                return False
            
            logger.info(f"Position {ticket} closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """Close all open positions, optionally filtered by symbol"""
        if not self.is_connected():
            return 0
        
        try:
            positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            if positions is None:
                return 0
            
            closed_count = 0
            for pos in positions:
                if self.close_position(pos.ticket):
                    closed_count += 1
            
            return closed_count
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return 0
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open positions"""
        if not self.is_connected():
            return []
        
        try:
            positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            if positions is None:
                return []
            
            return [{
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "profit": pos.profit,
                "sl": pos.sl,
                "tp": pos.tp,
                "time": datetime.fromtimestamp(pos.time),
                "comment": pos.comment
            } for pos in positions]
            
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []

