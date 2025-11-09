"""
Trade Logging Module
Logs trade events and results to file and console
"""

import csv
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import os

logger = logging.getLogger(__name__)


class TradeLogger:
    """Handles trade logging to CSV and console"""
    
    def __init__(self, csv_file: str = "ema_trades.csv", enable_logging: bool = True):
        """
        Initialize trade logger
        
        Args:
            csv_file: Path to CSV file for trade history
            enable_logging: Enable/disable logging
        """
        self.csv_file = csv_file
        self.enable_logging = enable_logging
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not self.enable_logging:
            return
        
        if not os.path.exists(self.csv_file):
            try:
                with open(self.csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'timestamp', 'symbol', 'direction', 'lot_size', 'entry_price',
                        'stop_loss', 'take_profit', 'exit_price', 'profit_loss', 'status',
                        'strategy_mode', 'timeframe', 'comment'
                    ])
            except Exception as e:
                logger.error(f"Error initializing CSV: {e}")
    
    def log_trade(self, symbol: str, direction: str, lot_size: float,
                  entry_price: float, stop_loss: float, take_profit: float,
                  exit_price: Optional[float] = None, profit_loss: Optional[float] = None,
                  status: str = "OPEN", strategy_mode: str = "Intraday",
                  timeframe: str = "M15", comment: str = ""):
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
            strategy_mode: Strategy mode (Scalper, Intraday, Swing)
            timeframe: Entry timeframe
            comment: Additional comment
        """
        if not self.enable_logging:
            return
        
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
                    strategy_mode,
                    timeframe,
                    comment
                ])
            logger.info(f"Trade logged: {direction} {symbol} @ {entry_price} ({status})")
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
    
    def log_trade_event(self, event_type: str, symbol: str, ticket: Optional[int] = None,
                       message: str = "", data: Optional[Dict] = None):
        """
        Log a trade event (entry, exit, SL update, etc.)
        
        Args:
            event_type: Type of event (ENTRY, EXIT, SL_UPDATE, TP_HIT, etc.)
            symbol: Trading symbol
            ticket: Trade ticket number
            message: Event message
            data: Additional event data
        """
        if not self.enable_logging:
            return
        
        try:
            log_message = f"[{event_type}] {symbol}"
            if ticket:
                log_message += f" Ticket: {ticket}"
            if message:
                log_message += f" - {message}"
            if data:
                log_message += f" | Data: {json.dumps(data)}"
            
            logger.info(log_message)
        except Exception as e:
            logger.error(f"Error logging trade event: {e}")
    
    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get trade history from CSV
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        if not os.path.exists(self.csv_file):
            return []
        
        try:
            trades = []
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trades.append(dict(row))
            
            # Return most recent trades first
            trades.reverse()
            
            if limit:
                return trades[:limit]
            
            return trades
            
        except Exception as e:
            logger.error(f"Error reading trade history: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Calculate trade statistics
        
        Returns:
            Dictionary with trade statistics
        """
        trades = self.get_trade_history()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'net_profit': 0.0,
                'average_profit': 0.0,
                'average_loss': 0.0
            }
        
        closed_trades = [t for t in trades if t.get('status') == 'CLOSED']
        
        if not closed_trades:
            return {
                'total_trades': len(trades),
                'open_trades': len([t for t in trades if t.get('status') == 'OPEN']),
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'net_profit': 0.0
            }
        
        profits = [float(t.get('profit_loss', 0)) for t in closed_trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]
        
        return {
            'total_trades': len(trades),
            'closed_trades': len(closed_trades),
            'open_trades': len([t for t in trades if t.get('status') == 'OPEN']),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0.0,
            'total_profit': sum(winning_trades) if winning_trades else 0.0,
            'total_loss': sum(losing_trades) if losing_trades else 0.0,
            'net_profit': sum(profits),
            'average_profit': sum(winning_trades) / len(winning_trades) if winning_trades else 0.0,
            'average_loss': sum(losing_trades) / len(losing_trades) if losing_trades else 0.0
        }

