"""
Risk Manager - Dynamic risk management with trailing stops and position management
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict
from datetime import datetime

from ..core.models import (
    TradePosition, TradeDirection, TradingConfig, RiskLevel
)


class RiskManager:
    """
    Manages risk for all trading positions with dynamic trailing stops 
    and multi-level profit taking (TP1, TP2, TP3).
    
    Key Features:
    - Dynamic trailing stops for all trades
    - Position division into TP1, TP2, TP3 levels
    - Risk-based position sizing
    - Real-time risk monitoring
    """
    
    def __init__(self, config: TradingConfig, account_balance: float = 10000.0):
        self.config = config
        self.account_balance = account_balance
        self.active_positions: Dict[str, TradePosition] = {}
        self.position_counter = 0
        
    def calculate_position_size(self, entry_price: float, stop_loss: float, risk_level: RiskLevel) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            entry_price: Entry price for the trade
            stop_loss: Stop loss price
            risk_level: Risk level assessment
            
        Returns:
            Position size in base currency units
        """
        # Adjust risk based on risk level
        risk_multiplier = self._get_risk_multiplier(risk_level)
        adjusted_risk = self.config.max_risk_per_trade * risk_multiplier
        
        # Calculate dollar risk amount
        dollar_risk = self.account_balance * adjusted_risk
        
        # Calculate price risk per unit
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
            
        # Calculate position size
        position_size = dollar_risk / price_risk
        
        # Apply maximum position size limits
        max_position_value = self.account_balance * 0.1  # Max 10% of account per trade
        max_position_size = max_position_value / entry_price
        
        return min(position_size, max_position_size)
    
    def _get_risk_multiplier(self, risk_level: RiskLevel) -> float:
        """Get risk multiplier based on risk level."""
        multipliers = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 0.75,
            RiskLevel.HIGH: 0.5,
            RiskLevel.EXTREME: 0.25
        }
        return multipliers.get(risk_level, 0.5)
    
    def create_position(
        self, 
        entry_price: float, 
        direction: TradeDirection, 
        stop_loss: float,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        is_trap_trade: bool = False
    ) -> str:
        """
        Create a new trading position with proper risk management.
        
        Args:
            entry_price: Entry price
            direction: Trade direction (LONG/SHORT)
            stop_loss: Initial stop loss
            risk_level: Risk assessment level
            is_trap_trade: Whether this is a trap trade
            
        Returns:
            Position ID
        """
        # Calculate position size
        position_size = self.calculate_position_size(entry_price, stop_loss, risk_level)
        
        if position_size <= 0:
            raise ValueError("Invalid position size calculated")
            
        # Calculate TP levels
        tp1_price, tp2_price, tp3_price = self._calculate_tp_levels(
            entry_price, stop_loss, direction
        )
        
        # Create position
        position_id = f"pos_{self.position_counter}"
        self.position_counter += 1
        
        position = TradePosition(
            entry_price=entry_price,
            direction=direction,
            size=position_size,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            tp3_price=tp3_price,
            stop_loss=stop_loss,
            trailing_stop=None,  # Will be set dynamically
            entry_time=datetime.now(),
            is_trap_trade=is_trap_trade
        )
        
        self.active_positions[position_id] = position
        return position_id
    
    def _calculate_tp_levels(self, entry_price: float, stop_loss: float, direction: TradeDirection) -> Tuple[float, float, float]:
        """Calculate TP1, TP2, and TP3 levels based on risk/reward ratios."""
        risk_amount = abs(entry_price - stop_loss)
        
        if direction == TradeDirection.LONG:
            tp1_price = entry_price + (risk_amount * self.config.tp1_ratio)
            tp2_price = entry_price + (risk_amount * self.config.tp2_ratio)
            tp3_price = entry_price + (risk_amount * self.config.tp3_ratio)
        else:  # SHORT
            tp1_price = entry_price - (risk_amount * self.config.tp1_ratio)
            tp2_price = entry_price - (risk_amount * self.config.tp2_ratio)
            tp3_price = entry_price - (risk_amount * self.config.tp3_ratio)
            
        return tp1_price, tp2_price, tp3_price
    
    def update_trailing_stops(self, current_prices: Dict[str, float]) -> Dict[str, Dict]:
        """
        Update trailing stops for all active positions.
        
        Args:
            current_prices: Dict of position_id -> current_price
            
        Returns:
            Dict of position updates and actions to take
        """
        updates = {}
        
        for position_id, position in self.active_positions.items():
            if position_id not in current_prices:
                continue
                
            current_price = current_prices[position_id]
            
            # Update trailing stop
            new_trailing_stop = self._calculate_trailing_stop(position, current_price)
            
            # Check for TP level hits
            tp_hit = self._check_tp_levels(position, current_price)
            
            # Check for stop loss hit
            stop_hit = self._check_stop_loss(position, current_price)
            
            # Update position
            if new_trailing_stop != position.trailing_stop:
                position.trailing_stop = new_trailing_stop
                
            # Record updates
            updates[position_id] = {
                'position': position,
                'trailing_stop_updated': new_trailing_stop != position.trailing_stop,
                'tp_hit': tp_hit,
                'stop_hit': stop_hit,
                'current_price': current_price
            }
            
        return updates
    
    def _calculate_trailing_stop(self, position: TradePosition, current_price: float) -> Optional[float]:
        """Calculate trailing stop based on current price and position direction."""
        if position.direction == TradeDirection.LONG:
            # For long positions, trailing stop moves up only
            trailing_distance = current_price * (self.config.trailing_stop_distance / 100)
            potential_stop = current_price - trailing_distance
            
            # Only move stop up
            if position.trailing_stop is None:
                return max(potential_stop, position.stop_loss)
            else:
                return max(potential_stop, position.trailing_stop)
                
        else:  # SHORT position
            # For short positions, trailing stop moves down only
            trailing_distance = current_price * (self.config.trailing_stop_distance / 100)
            potential_stop = current_price + trailing_distance
            
            # Only move stop down
            if position.trailing_stop is None:
                return min(potential_stop, position.stop_loss)
            else:
                return min(potential_stop, position.trailing_stop)
    
    def _check_tp_levels(self, position: TradePosition, current_price: float) -> Optional[str]:
        """Check if any TP level has been hit."""
        if position.direction == TradeDirection.LONG:
            if current_price >= position.tp3_price:
                return 'TP3'
            elif current_price >= position.tp2_price:
                return 'TP2'
            elif current_price >= position.tp1_price:
                return 'TP1'
        else:  # SHORT
            if current_price <= position.tp3_price:
                return 'TP3'
            elif current_price <= position.tp2_price:
                return 'TP2'
            elif current_price <= position.tp1_price:
                return 'TP1'
                
        return None
    
    def _check_stop_loss(self, position: TradePosition, current_price: float) -> bool:
        """Check if stop loss (including trailing stop) has been hit."""
        active_stop = position.trailing_stop if position.trailing_stop is not None else position.stop_loss
        
        if position.direction == TradeDirection.LONG:
            return current_price <= active_stop
        else:  # SHORT
            return current_price >= active_stop
    
    def process_tp_hit(self, position_id: str, tp_level: str) -> Dict:
        """
        Process a TP level hit by partially closing the position.
        
        Args:
            position_id: ID of the position
            tp_level: Which TP level was hit ('TP1', 'TP2', 'TP3')
            
        Returns:
            Dict with close details
        """
        if position_id not in self.active_positions:
            return {'error': 'Position not found'}
            
        position = self.active_positions[position_id]
        
        # Determine how much to close
        if tp_level == 'TP1':
            close_percentage = self.config.tp1_size_percent
            close_price = position.tp1_price
        elif tp_level == 'TP2':
            close_percentage = self.config.tp2_size_percent
            close_price = position.tp2_price
        elif tp_level == 'TP3':
            close_percentage = self.config.tp3_size_percent
            close_price = position.tp3_price
        else:
            return {'error': 'Invalid TP level'}
            
        # Calculate close amount
        close_amount = position.size * close_percentage
        
        # Update position size
        position.size -= close_amount
        
        # Calculate profit
        if position.direction == TradeDirection.LONG:
            profit = (close_price - position.entry_price) * close_amount
        else:
            profit = (position.entry_price - close_price) * close_amount
            
        # If position is fully closed, remove it
        if position.size <= 0.001:  # Essentially zero
            del self.active_positions[position_id]
            
        return {
            'position_id': position_id,
            'tp_level': tp_level,
            'close_amount': close_amount,
            'close_price': close_price,
            'profit': profit,
            'remaining_size': position.size if position_id in self.active_positions else 0,
            'fully_closed': position_id not in self.active_positions
        }
    
    def close_position(self, position_id: str, current_price: float, reason: str = 'manual') -> Dict:
        """
        Close a position completely.
        
        Args:
            position_id: ID of position to close
            current_price: Current market price
            reason: Reason for closing
            
        Returns:
            Dict with close details
        """
        if position_id not in self.active_positions:
            return {'error': 'Position not found'}
            
        position = self.active_positions[position_id]
        
        # Calculate profit/loss
        if position.direction == TradeDirection.LONG:
            pnl = (current_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - current_price) * position.size
            
        # Remove position
        del self.active_positions[position_id]
        
        return {
            'position_id': position_id,
            'close_price': current_price,
            'close_amount': position.size,
            'pnl': pnl,
            'reason': reason,
            'entry_price': position.entry_price,
            'direction': position.direction.value,
            'hold_time': datetime.now() - position.entry_time
        }
    
    def get_position_status(self, position_id: str) -> Optional[Dict]:
        """Get current status of a position."""
        if position_id not in self.active_positions:
            return None
            
        position = self.active_positions[position_id]
        
        return {
            'position_id': position_id,
            'entry_price': position.entry_price,
            'direction': position.direction.value,
            'size': position.size,
            'tp1_price': position.tp1_price,
            'tp2_price': position.tp2_price,
            'tp3_price': position.tp3_price,
            'stop_loss': position.stop_loss,
            'trailing_stop': position.trailing_stop,
            'entry_time': position.entry_time,
            'is_trap_trade': position.is_trap_trade
        }
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """Get status of all active positions."""
        return {pos_id: self.get_position_status(pos_id) for pos_id in self.active_positions.keys()}
    
    def calculate_total_risk(self) -> float:
        """Calculate total risk exposure across all positions."""
        total_risk = 0.0
        
        for position in self.active_positions.values():
            # Calculate potential loss if stop hit
            active_stop = position.trailing_stop if position.trailing_stop is not None else position.stop_loss
            
            if position.direction == TradeDirection.LONG:
                position_risk = (position.entry_price - active_stop) * position.size
            else:
                position_risk = (active_stop - position.entry_price) * position.size
                
            total_risk += max(0, position_risk)  # Only count positive risk
            
        return total_risk
    
    def get_risk_metrics(self) -> Dict:
        """Get comprehensive risk metrics."""
        total_risk = self.calculate_total_risk()
        total_exposure = sum(pos.size * pos.entry_price for pos in self.active_positions.values())
        
        return {
            'total_positions': len(self.active_positions),
            'total_risk': total_risk,
            'risk_percentage': (total_risk / self.account_balance) * 100,
            'total_exposure': total_exposure,
            'exposure_percentage': (total_exposure / self.account_balance) * 100,
            'account_balance': self.account_balance,
            'trap_trades': sum(1 for pos in self.active_positions.values() if pos.is_trap_trade),
            'regular_trades': sum(1 for pos in self.active_positions.values() if not pos.is_trap_trade)
        }
    
    def update_account_balance(self, new_balance: float):
        """Update account balance (e.g., after profit/loss realization)."""
        self.account_balance = new_balance
        
    def should_take_new_trade(self, estimated_risk: float) -> bool:
        """
        Determine if a new trade should be taken based on current risk exposure.
        
        Args:
            estimated_risk: Estimated risk for the new trade
            
        Returns:
            True if trade should be taken, False otherwise
        """
        current_risk = self.calculate_total_risk()
        total_risk_after = current_risk + estimated_risk
        
        # Don't exceed 10% total risk
        max_total_risk = self.account_balance * 0.1
        
        # Don't take trade if it would exceed risk limits
        if total_risk_after > max_total_risk:
            return False
            
        # Don't take more than 5 positions simultaneously
        if len(self.active_positions) >= 5:
            return False
            
        return True