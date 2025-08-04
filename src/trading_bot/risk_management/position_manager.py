"""
Risk management system with dynamic trailing stops and multiple take profit levels.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging


class PositionStatus(Enum):
    """Position status enumeration."""
    OPEN = "open"
    PARTIAL_CLOSE = "partial_close"
    CLOSED = "closed"
    STOPPED_OUT = "stopped_out"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


@dataclass
class Position:
    """Represents a trading position with multiple take profit levels."""
    entry_price: float
    size: float
    direction: str  # 'long' or 'short'
    timestamp: pd.Timestamp
    status: PositionStatus = PositionStatus.OPEN
    
    # Take profit levels
    tp1_price: float = 0.0
    tp2_price: float = 0.0
    tp3_price: float = 0.0
    
    # Position allocations (percentages)
    tp1_size: float = 0.0
    tp2_size: float = 0.0
    tp3_size: float = 0.0
    
    # Remaining size after partial closes
    remaining_size: float = 0.0
    
    # Stop loss and trailing stop
    stop_loss_price: float = 0.0
    trailing_stop_price: float = 0.0
    trailing_stop_distance: float = 0.0
    
    # P&L tracking
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Execution tracking
    tp1_filled: bool = False
    tp2_filled: bool = False
    tp3_filled: bool = False
    
    def __post_init__(self):
        if self.remaining_size == 0.0:
            self.remaining_size = self.size


@dataclass
class Order:
    """Represents a trading order."""
    order_type: OrderType
    side: str  # 'buy' or 'sell'
    price: float
    size: float
    timestamp: pd.Timestamp
    position_id: Optional[str] = None
    filled: bool = False
    fill_price: Optional[float] = None
    fill_timestamp: Optional[pd.Timestamp] = None


class RiskManager:
    """Manages position sizing, stop losses, and take profit levels."""
    
    def __init__(self, config):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.daily_pnl = 0.0
        self.max_daily_loss_reached = False
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, account_balance: float, entry_price: float) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            account_balance: Current account balance
            entry_price: Entry price for the position
            
        Returns:
            Position size in base currency
        """
        # Calculate size based on percentage of account
        risk_amount = account_balance * (self.config.position_size_percent / 100)
        
        # Convert to position size
        position_size = risk_amount / entry_price
        
        return position_size
    
    def create_position(self, entry_price: float, size: float, direction: str, 
                       timestamp: pd.Timestamp) -> str:
        """
        Create a new position with multiple take profit levels.
        
        Args:
            entry_price: Entry price
            size: Position size
            direction: 'long' or 'short'
            timestamp: Entry timestamp
            
        Returns:
            Position ID
        """
        position_id = f"{direction}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate take profit prices
        if direction == 'long':
            tp1_price = entry_price * (1 + self.config.tp1_percent / 100)
            tp2_price = entry_price * (1 + self.config.tp2_percent / 100)
            tp3_price = entry_price * (1 + self.config.tp3_percent / 100)
            stop_loss_price = entry_price * (1 - self.config.trailing_stop_percent / 100)
        else:  # short
            tp1_price = entry_price * (1 - self.config.tp1_percent / 100)
            tp2_price = entry_price * (1 - self.config.tp2_percent / 100)
            tp3_price = entry_price * (1 - self.config.tp3_percent / 100)
            stop_loss_price = entry_price * (1 + self.config.trailing_stop_percent / 100)
        
        # Calculate position allocations
        tp1_size = size * (self.config.tp1_allocation / 100)
        tp2_size = size * (self.config.tp2_allocation / 100)
        tp3_size = size * (self.config.tp3_allocation / 100)
        
        position = Position(
            entry_price=entry_price,
            size=size,
            direction=direction,
            timestamp=timestamp,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            tp3_price=tp3_price,
            tp1_size=tp1_size,
            tp2_size=tp2_size,
            tp3_size=tp3_size,
            stop_loss_price=stop_loss_price,
            trailing_stop_price=stop_loss_price,
            trailing_stop_distance=abs(entry_price - stop_loss_price)
        )
        
        self.positions[position_id] = position
        
        # Create take profit orders
        self._create_take_profit_orders(position_id, position)
        
        self.logger.info(f"Created {direction} position {position_id} at {entry_price}")
        return position_id
    
    def update_trailing_stop(self, position_id: str, current_price: float) -> bool:
        """
        Update trailing stop for a position.
        
        Args:
            position_id: Position identifier
            current_price: Current market price
            
        Returns:
            True if trailing stop was updated
        """
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        
        if position.status != PositionStatus.OPEN:
            return False
        
        updated = False
        
        if position.direction == 'long':
            # For long positions, trailing stop moves up
            new_trailing_stop = current_price - position.trailing_stop_distance
            if new_trailing_stop > position.trailing_stop_price:
                position.trailing_stop_price = new_trailing_stop
                updated = True
        else:
            # For short positions, trailing stop moves down
            new_trailing_stop = current_price + position.trailing_stop_distance
            if new_trailing_stop < position.trailing_stop_price:
                position.trailing_stop_price = new_trailing_stop
                updated = True
        
        if updated:
            self.logger.info(f"Updated trailing stop for {position_id} to {position.trailing_stop_price}")
        
        return updated
    
    def check_exit_conditions(self, position_id: str, current_price: float, 
                             timestamp: pd.Timestamp) -> List[Order]:
        """
        Check if any exit conditions are met for a position.
        
        Args:
            position_id: Position identifier
            current_price: Current market price
            timestamp: Current timestamp
            
        Returns:
            List of orders to execute
        """
        if position_id not in self.positions:
            return []
        
        position = self.positions[position_id]
        orders_to_execute = []
        
        # Check trailing stop
        if self._is_trailing_stop_hit(position, current_price):
            # Close entire remaining position
            order = Order(
                order_type=OrderType.TRAILING_STOP,
                side='sell' if position.direction == 'long' else 'buy',
                price=current_price,
                size=position.remaining_size,
                timestamp=timestamp,
                position_id=position_id
            )
            orders_to_execute.append(order)
            position.status = PositionStatus.STOPPED_OUT
            self.logger.info(f"Trailing stop hit for {position_id} at {current_price}")
        
        # Check take profit levels
        else:
            tp_orders = self._check_take_profit_levels(position, current_price, timestamp)
            orders_to_execute.extend(tp_orders)
        
        return orders_to_execute
    
    def execute_order(self, order: Order, fill_price: Optional[float] = None) -> bool:
        """
        Execute an order and update position accordingly.
        
        Args:
            order: Order to execute
            fill_price: Actual fill price (defaults to order price)
            
        Returns:
            True if order was executed successfully
        """
        if fill_price is None:
            fill_price = order.price
        
        order.filled = True
        order.fill_price = fill_price
        order.fill_timestamp = order.timestamp
        
        # Update position if this is a take profit order
        if order.position_id and order.position_id in self.positions:
            position = self.positions[order.position_id]
            
            if order.order_type == OrderType.TAKE_PROFIT:
                self._handle_take_profit_fill(position, order, fill_price)
            elif order.order_type == OrderType.TRAILING_STOP:
                self._handle_stop_loss_fill(position, order, fill_price)
        
        self.orders.append(order)
        return True
    
    def calculate_unrealized_pnl(self, position_id: str, current_price: float) -> float:
        """
        Calculate unrealized P&L for a position.
        
        Args:
            position_id: Position identifier
            current_price: Current market price
            
        Returns:
            Unrealized P&L
        """
        if position_id not in self.positions:
            return 0.0
        
        position = self.positions[position_id]
        
        if position.direction == 'long':
            pnl = (current_price - position.entry_price) * position.remaining_size
        else:
            pnl = (position.entry_price - current_price) * position.remaining_size
        
        position.unrealized_pnl = pnl
        return pnl
    
    def get_total_exposure(self) -> float:
        """Get total position exposure across all open positions."""
        total_exposure = 0.0
        for position in self.positions.values():
            if position.status == PositionStatus.OPEN:
                total_exposure += position.remaining_size * position.entry_price
        return total_exposure
    
    def check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit has been reached."""
        return self.max_daily_loss_reached
    
    def reset_daily_pnl(self):
        """Reset daily P&L tracking (call at start of each trading day)."""
        self.daily_pnl = 0.0
        self.max_daily_loss_reached = False
    
    def _create_take_profit_orders(self, position_id: str, position: Position):
        """Create take profit orders for a position."""
        # Orders will be created as needed when price approaches TP levels
        pass
    
    def _is_trailing_stop_hit(self, position: Position, current_price: float) -> bool:
        """Check if trailing stop is hit."""
        if position.direction == 'long':
            return current_price <= position.trailing_stop_price
        else:
            return current_price >= position.trailing_stop_price
    
    def _check_take_profit_levels(self, position: Position, current_price: float, 
                                 timestamp: pd.Timestamp) -> List[Order]:
        """Check if any take profit levels should be executed."""
        orders = []
        
        # Check TP1
        if not position.tp1_filled and self._is_tp_level_hit(position, current_price, 1):
            order = Order(
                order_type=OrderType.TAKE_PROFIT,
                side='sell' if position.direction == 'long' else 'buy',
                price=position.tp1_price,
                size=position.tp1_size,
                timestamp=timestamp,
                position_id=position.entry_price
            )
            orders.append(order)
        
        # Check TP2
        if not position.tp2_filled and self._is_tp_level_hit(position, current_price, 2):
            order = Order(
                order_type=OrderType.TAKE_PROFIT,
                side='sell' if position.direction == 'long' else 'buy',
                price=position.tp2_price,
                size=position.tp2_size,
                timestamp=timestamp,
                position_id=position.entry_price
            )
            orders.append(order)
        
        # Check TP3
        if not position.tp3_filled and self._is_tp_level_hit(position, current_price, 3):
            order = Order(
                order_type=OrderType.TAKE_PROFIT,
                side='sell' if position.direction == 'long' else 'buy',
                price=position.tp3_price,
                size=position.tp3_size,
                timestamp=timestamp,
                position_id=position.entry_price
            )
            orders.append(order)
        
        return orders
    
    def _is_tp_level_hit(self, position: Position, current_price: float, tp_level: int) -> bool:
        """Check if a specific take profit level is hit."""
        if tp_level == 1:
            target_price = position.tp1_price
        elif tp_level == 2:
            target_price = position.tp2_price
        else:
            target_price = position.tp3_price
        
        if position.direction == 'long':
            return current_price >= target_price
        else:
            return current_price <= target_price
    
    def _handle_take_profit_fill(self, position: Position, order: Order, fill_price: float):
        """Handle the filling of a take profit order."""
        # Determine which TP level was filled
        if abs(order.price - position.tp1_price) < 0.01:
            position.tp1_filled = True
            size_filled = position.tp1_size
        elif abs(order.price - position.tp2_price) < 0.01:
            position.tp2_filled = True
            size_filled = position.tp2_size
        else:
            position.tp3_filled = True
            size_filled = position.tp3_size
        
        # Update remaining size
        position.remaining_size -= size_filled
        
        # Calculate realized P&L for this partial close
        if position.direction == 'long':
            pnl = (fill_price - position.entry_price) * size_filled
        else:
            pnl = (position.entry_price - fill_price) * size_filled
        
        position.realized_pnl += pnl
        self.daily_pnl += pnl
        
        # Update position status
        if position.remaining_size <= 0.01:  # Account for floating point precision
            position.status = PositionStatus.CLOSED
        else:
            position.status = PositionStatus.PARTIAL_CLOSE
        
        # Update trailing stop distance for remaining position
        if position.remaining_size > 0:
            # Tighten trailing stop after partial profit taking
            position.trailing_stop_distance *= 0.8
        
        self.logger.info(f"TP filled for position, realized P&L: {pnl}")
    
    def _handle_stop_loss_fill(self, position: Position, order: Order, fill_price: float):
        """Handle the filling of a stop loss order."""
        # Calculate realized P&L for stop out
        if position.direction == 'long':
            pnl = (fill_price - position.entry_price) * position.remaining_size
        else:
            pnl = (position.entry_price - fill_price) * position.remaining_size
        
        position.realized_pnl += pnl
        self.daily_pnl += pnl
        position.remaining_size = 0.0
        position.status = PositionStatus.STOPPED_OUT
        
        # Check daily loss limit
        if pnl < 0 and abs(pnl) > (self.config.max_daily_loss_percent / 100) * 10000:  # Assuming $10k account
            self.max_daily_loss_reached = True
            self.logger.warning("Daily loss limit reached, stopping trading")
        
        self.logger.info(f"Stop loss filled, realized P&L: {pnl}")