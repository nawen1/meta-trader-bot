"""
Risk Management Module - Advanced risk management with trailing stops and TP levels
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, NamedTuple
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Position status types"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


class ExitReason(Enum):
    """Exit reason types"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT_1 = "take_profit_1"
    TAKE_PROFIT_2 = "take_profit_2"
    TAKE_PROFIT_3 = "take_profit_3"
    TRAILING_STOP = "trailing_stop"
    MANUAL_EXIT = "manual_exit"


@dataclass
class Position:
    """Represents a trading position"""
    entry_price: float
    size: float
    direction: str  # 'long' or 'short'
    initial_stop_loss: float
    current_stop_loss: float
    take_profits: List[float]
    entry_time: pd.Timestamp
    status: PositionStatus = PositionStatus.OPEN
    remaining_size: float = None
    max_favorable_price: float = None
    
    def __post_init__(self):
        if self.remaining_size is None:
            self.remaining_size = self.size
        if self.max_favorable_price is None:
            self.max_favorable_price = self.entry_price


class TradeResult(NamedTuple):
    """Represents a trade result"""
    profit_loss: float
    profit_loss_percentage: float
    exit_price: float
    exit_reason: ExitReason
    exit_time: pd.Timestamp
    position_size: float


class RiskManager:
    """Advanced risk management system"""
    
    def __init__(self, config):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.logger = logging.getLogger(__name__)
        self.trade_history: List[TradeResult] = []
    
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                              stop_loss: float, max_risk_percentage: Optional[float] = None) -> float:
        """
        Calculate position size based on risk management rules
        """
        if max_risk_percentage is None:
            max_risk_percentage = self.config.risk_management.max_risk_per_trade
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        
        # Calculate maximum risk amount
        max_risk_amount = account_balance * max_risk_percentage
        
        # Calculate position size
        position_size = max_risk_amount / risk_per_unit
        
        self.logger.info(f"Calculated position size: {position_size:.6f} "
                        f"(Risk: {max_risk_amount:.2f}, Risk per unit: {risk_per_unit:.6f})")
        
        return position_size
    
    def open_position(self, symbol: str, entry_price: float, size: float, 
                     direction: str, stop_loss: float, take_profits: List[float]) -> str:
        """
        Open a new position with risk management parameters
        """
        position = Position(
            entry_price=entry_price,
            size=size,
            direction=direction,
            initial_stop_loss=stop_loss,
            current_stop_loss=stop_loss,
            take_profits=take_profits,
            entry_time=pd.Timestamp.now()
        )
        
        position_id = f"{symbol}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        self.positions[position_id] = position
        
        self.logger.info(f"Opened {direction} position {position_id}: "
                        f"Entry: {entry_price}, Size: {size}, SL: {stop_loss}")
        
        return position_id
    
    def update_trailing_stop(self, position_id: str, current_price: float) -> bool:
        """
        Update trailing stop for a position
        """
        if position_id not in self.positions:
            return False
        
        position = self.positions[position_id]
        
        if not self.config.risk_management.trailing_stop_enabled:
            return False
        
        # Update max favorable price
        if position.direction == 'long':
            if current_price > position.max_favorable_price:
                position.max_favorable_price = current_price
        else:  # short
            if current_price < position.max_favorable_price:
                position.max_favorable_price = current_price
        
        # Calculate new trailing stop
        trailing_distance = self.config.risk_management.trailing_stop_distance
        
        if position.direction == 'long':
            new_stop = position.max_favorable_price * (1 - trailing_distance)
            if new_stop > position.current_stop_loss:
                old_stop = position.current_stop_loss
                position.current_stop_loss = new_stop
                self.logger.info(f"Updated trailing stop for {position_id}: "
                               f"{old_stop:.6f} -> {new_stop:.6f}")
                return True
        else:  # short
            new_stop = position.max_favorable_price * (1 + trailing_distance)
            if new_stop < position.current_stop_loss:
                old_stop = position.current_stop_loss
                position.current_stop_loss = new_stop
                self.logger.info(f"Updated trailing stop for {position_id}: "
                               f"{old_stop:.6f} -> {new_stop:.6f}")
                return True
        
        return False
    
    def check_exit_conditions(self, position_id: str, current_price: float) -> Optional[TradeResult]:
        """
        Check if position should be exited based on stops and take profits
        """
        if position_id not in self.positions:
            return None
        
        position = self.positions[position_id]
        
        # Check stop loss
        if self._should_exit_stop_loss(position, current_price):
            return self._exit_position(position_id, current_price, ExitReason.STOP_LOSS)
        
        # Check take profit levels
        tp_result = self._check_take_profit_levels(position_id, current_price)
        if tp_result:
            return tp_result
        
        return None
    
    def _should_exit_stop_loss(self, position: Position, current_price: float) -> bool:
        """Check if position should be stopped out"""
        if position.direction == 'long':
            return current_price <= position.current_stop_loss
        else:  # short
            return current_price >= position.current_stop_loss
    
    def _check_take_profit_levels(self, position_id: str, current_price: float) -> Optional[TradeResult]:
        """Check and execute take profit levels"""
        position = self.positions[position_id]
        
        for i, tp_level in enumerate(position.take_profits):
            if self._price_hit_tp_level(position, current_price, tp_level):
                # Determine which TP level was hit
                if i == 0:
                    exit_reason = ExitReason.TAKE_PROFIT_1
                    close_percentage = self.config.risk_management.tp1_close_percentage
                elif i == 1:
                    exit_reason = ExitReason.TAKE_PROFIT_2
                    close_percentage = self.config.risk_management.tp2_close_percentage
                else:
                    exit_reason = ExitReason.TAKE_PROFIT_3
                    close_percentage = self.config.risk_management.tp3_close_percentage
                
                # Partial or full exit
                return self._partial_exit_position(position_id, current_price, 
                                                 exit_reason, close_percentage)
        
        return None
    
    def _price_hit_tp_level(self, position: Position, current_price: float, tp_level: float) -> bool:
        """Check if current price has hit a take profit level"""
        if position.direction == 'long':
            return current_price >= tp_level
        else:  # short
            return current_price <= tp_level
    
    def _partial_exit_position(self, position_id: str, exit_price: float, 
                             exit_reason: ExitReason, close_percentage: float) -> TradeResult:
        """Partially close a position"""
        position = self.positions[position_id]
        
        # Calculate size to close
        size_to_close = position.remaining_size * close_percentage
        
        # Calculate profit/loss for this partial exit
        if position.direction == 'long':
            pnl = (exit_price - position.entry_price) * size_to_close
        else:  # short
            pnl = (position.entry_price - exit_price) * size_to_close
        
        pnl_percentage = (pnl / (position.entry_price * size_to_close)) * 100
        
        # Update position
        position.remaining_size -= size_to_close
        
        if position.remaining_size <= 0.0001:  # Close to zero
            position.status = PositionStatus.CLOSED
            del self.positions[position_id]
        else:
            position.status = PositionStatus.PARTIALLY_CLOSED
            # Remove the hit TP level
            if exit_reason == ExitReason.TAKE_PROFIT_1:
                position.take_profits = position.take_profits[1:]
            elif exit_reason == ExitReason.TAKE_PROFIT_2:
                position.take_profits = position.take_profits[2:]
            elif exit_reason == ExitReason.TAKE_PROFIT_3:
                position.take_profits = []
        
        # Create trade result
        trade_result = TradeResult(
            profit_loss=pnl,
            profit_loss_percentage=pnl_percentage,
            exit_price=exit_price,
            exit_reason=exit_reason,
            exit_time=pd.Timestamp.now(),
            position_size=size_to_close
        )
        
        self.trade_history.append(trade_result)
        
        self.logger.info(f"Partial exit {position_id}: {exit_reason.value} at {exit_price:.6f}, "
                        f"Size: {size_to_close:.6f}, PnL: {pnl:.2f} ({pnl_percentage:.2f}%)")
        
        return trade_result
    
    def _exit_position(self, position_id: str, exit_price: float, 
                      exit_reason: ExitReason) -> TradeResult:
        """Fully close a position"""
        position = self.positions[position_id]
        
        # Calculate profit/loss
        if position.direction == 'long':
            pnl = (exit_price - position.entry_price) * position.remaining_size
        else:  # short
            pnl = (position.entry_price - exit_price) * position.remaining_size
        
        pnl_percentage = (pnl / (position.entry_price * position.remaining_size)) * 100
        
        # Create trade result
        trade_result = TradeResult(
            profit_loss=pnl,
            profit_loss_percentage=pnl_percentage,
            exit_price=exit_price,
            exit_reason=exit_reason,
            exit_time=pd.Timestamp.now(),
            position_size=position.remaining_size
        )
        
        self.trade_history.append(trade_result)
        
        # Close position
        position.status = PositionStatus.CLOSED
        del self.positions[position_id]
        
        self.logger.info(f"Closed position {position_id}: {exit_reason.value} at {exit_price:.6f}, "
                        f"PnL: {pnl:.2f} ({pnl_percentage:.2f}%)")
        
        return trade_result
    
    def get_portfolio_risk(self) -> Dict:
        """Calculate current portfolio risk metrics"""
        total_positions = len(self.positions)
        
        if total_positions == 0:
            return {
                'total_positions': 0,
                'total_risk': 0.0,
                'average_risk_per_trade': 0.0,
                'max_drawdown_potential': 0.0
            }
        
        total_risk = 0.0
        max_drawdown_potential = 0.0
        
        for position in self.positions.values():
            # Calculate current risk (difference between entry and current stop)
            risk_per_unit = abs(position.entry_price - position.current_stop_loss)
            position_risk = risk_per_unit * position.remaining_size
            total_risk += position_risk
            
            # Calculate max potential loss if all stops are hit
            max_drawdown_potential += position_risk
        
        return {
            'total_positions': total_positions,
            'total_risk': total_risk,
            'average_risk_per_trade': total_risk / total_positions if total_positions > 0 else 0.0,
            'max_drawdown_potential': max_drawdown_potential
        }
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics from trade history"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0
            }
        
        winning_trades = [t for t in self.trade_history if t.profit_loss > 0]
        losing_trades = [t for t in self.trade_history if t.profit_loss < 0]
        
        total_pnl = sum(t.profit_loss for t in self.trade_history)
        total_wins = sum(t.profit_loss for t in winning_trades)
        total_losses = abs(sum(t.profit_loss for t in losing_trades))
        
        return {
            'total_trades': len(self.trade_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trade_history) * 100,
            'total_pnl': total_pnl,
            'average_win': total_wins / len(winning_trades) if winning_trades else 0.0,
            'average_loss': total_losses / len(losing_trades) if losing_trades else 0.0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else float('inf')
        }
    
    def adjust_risk_for_market_conditions(self, market_volatility: float, 
                                        market_structure: str) -> float:
        """
        Adjust risk parameters based on market conditions
        """
        base_risk = self.config.risk_management.max_risk_per_trade
        
        # Reduce risk in high volatility environments
        volatility_adjustment = 1.0
        if market_volatility > 2.0:  # High volatility
            volatility_adjustment = 0.5
        elif market_volatility > 1.5:  # Medium volatility
            volatility_adjustment = 0.75
        
        # Adjust risk based on market structure
        structure_adjustment = 1.0
        if market_structure == 'sideways':
            structure_adjustment = 0.8  # Reduce risk in choppy markets
        elif market_structure == 'trending':
            structure_adjustment = 1.2  # Increase risk in trending markets
        
        adjusted_risk = base_risk * volatility_adjustment * structure_adjustment
        
        # Ensure risk doesn't exceed maximum
        return min(adjusted_risk, self.config.risk_management.max_risk_per_trade * 1.5)
    
    def should_avoid_trade(self, portfolio_risk: Dict, market_conditions: Dict) -> bool:
        """
        Determine if trading should be avoided based on risk conditions
        """
        # Avoid if too many open positions
        if portfolio_risk['total_positions'] >= 5:
            self.logger.warning("Too many open positions, avoiding new trades")
            return True
        
        # Avoid if total portfolio risk is too high
        max_portfolio_risk = 0.1  # 10% max portfolio risk
        if portfolio_risk['total_risk'] > max_portfolio_risk:
            self.logger.warning(f"Portfolio risk too high: {portfolio_risk['total_risk']:.2%}")
            return True
        
        # Avoid in extreme market conditions
        if market_conditions.get('volatility', 0) > 3.0:
            self.logger.warning("Extreme market volatility, avoiding trades")
            return True
        
        return False