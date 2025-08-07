"""
Trade Execution Module - Safe trade execution with comprehensive validation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, NamedTuple
from enum import Enum
import logging
from dataclasses import dataclass
from .market_analysis import TrapSignal, MarketStructure
from .risk_management import RiskManager, Position

logger = logging.getLogger(__name__)


class TradeDirection(Enum):
    """Trade direction types"""
    LONG = "long"
    SHORT = "short"


class TradeValidationResult(Enum):
    """Trade validation results"""
    VALID = "valid"
    INVALID_NO_ENTRY = "invalid_no_entry"
    INVALID_HIGH_RISK = "invalid_high_risk"
    INVALID_MARKET_CONDITIONS = "invalid_market_conditions"
    INVALID_NO_TRAP_ENTRY = "invalid_no_trap_entry"
    INVALID_INSUFFICIENT_CONFIDENCE = "invalid_insufficient_confidence"


@dataclass
class TradeSetup:
    """Represents a complete trade setup"""
    symbol: str
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profits: List[float]
    position_size: float
    confidence: float
    is_trap_trade: bool
    market_context: Dict
    validation_result: TradeValidationResult


class TradeExecutor:
    """Advanced trade execution system with safety checks"""
    
    def __init__(self, config, risk_manager: RiskManager):
        self.config = config
        self.risk_manager = risk_manager
        self.logger = logging.getLogger(__name__)
        self.executed_trades = []
    
    def validate_trap_trade(self, trap_signal: TrapSignal, 
                           market_context: Dict, account_balance: float) -> TradeSetup:
        """
        Validate and prepare a trap trade for execution
        """
        # Check if trap trading is enabled
        if not self.config.enable_trap_trading:
            return TradeSetup(
                symbol="",
                direction=TradeDirection.LONG,
                entry_price=0,
                stop_loss=0,
                take_profits=[],
                position_size=0,
                confidence=0,
                is_trap_trade=True,
                market_context=market_context,
                validation_result=TradeValidationResult.INVALID_NO_TRAP_ENTRY
            )
        
        # Validate confidence level
        if trap_signal.confidence < self.config.min_entry_confidence:
            self.logger.warning(f"Trap signal confidence too low: {trap_signal.confidence:.2f}")
            return self._create_invalid_setup(TradeValidationResult.INVALID_INSUFFICIENT_CONFIDENCE)
        
        # Check for safe entry point
        if not trap_signal.safe_entry_exists:
            self.logger.warning("No safe entry point exists before trap")
            return self._create_invalid_setup(TradeValidationResult.INVALID_NO_TRAP_ENTRY)
        
        # Validate market conditions
        if not self._validate_market_conditions(market_context):
            return self._create_invalid_setup(TradeValidationResult.INVALID_MARKET_CONDITIONS)
        
        # Determine trade direction
        direction = (TradeDirection.LONG if trap_signal.trap_type == 'bull_trap' 
                    else TradeDirection.SHORT)
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            account_balance, trap_signal.entry_price, trap_signal.stop_loss
        )
        
        # Validate risk
        if not self._validate_risk_parameters(trap_signal, position_size, account_balance):
            return self._create_invalid_setup(TradeValidationResult.INVALID_HIGH_RISK)
        
        return TradeSetup(
            symbol="SYMBOL",  # Would be set by calling code
            direction=direction,
            entry_price=trap_signal.entry_price,
            stop_loss=trap_signal.stop_loss,
            take_profits=trap_signal.take_profits,
            position_size=position_size,
            confidence=trap_signal.confidence,
            is_trap_trade=True,
            market_context=market_context,
            validation_result=TradeValidationResult.VALID
        )
    
    def validate_regular_trade(self, entry_price: float, stop_loss: float, 
                             take_profits: List[float], direction: TradeDirection,
                             market_context: Dict, account_balance: float) -> TradeSetup:
        """
        Validate and prepare a regular (non-trap) trade for execution
        """
        # Check if forcing trades is disabled and no clear setup exists
        if not self.config.force_trades and not self._has_clear_setup(market_context):
            return self._create_invalid_setup(TradeValidationResult.INVALID_NO_ENTRY)
        
        # Validate market conditions
        if not self._validate_market_conditions(market_context):
            return self._create_invalid_setup(TradeValidationResult.INVALID_MARKET_CONDITIONS)
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            account_balance, entry_price, stop_loss
        )
        
        # Create temporary trap signal for risk validation
        temp_signal = TrapSignal(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            confidence=0.8,  # Default confidence for regular trades
            trap_type='regular',
            liquidity_above=0,
            liquidity_below=0,
            safe_entry_exists=True
        )
        
        # Validate risk
        if not self._validate_risk_parameters(temp_signal, position_size, account_balance):
            return self._create_invalid_setup(TradeValidationResult.INVALID_HIGH_RISK)
        
        return TradeSetup(
            symbol="SYMBOL",  # Would be set by calling code
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            position_size=position_size,
            confidence=0.8,
            is_trap_trade=False,
            market_context=market_context,
            validation_result=TradeValidationResult.VALID
        )
    
    def execute_trade(self, trade_setup: TradeSetup, symbol: str) -> Optional[str]:
        """
        Execute a validated trade setup
        """
        if trade_setup.validation_result != TradeValidationResult.VALID:
            self.logger.warning(f"Cannot execute invalid trade: {trade_setup.validation_result}")
            return None
        
        # Final risk check
        portfolio_risk = self.risk_manager.get_portfolio_risk()
        if self.risk_manager.should_avoid_trade(portfolio_risk, trade_setup.market_context):
            self.logger.warning("Trade avoided due to portfolio risk conditions")
            return None
        
        # Open position through risk manager
        position_id = self.risk_manager.open_position(
            symbol=symbol,
            entry_price=trade_setup.entry_price,
            size=trade_setup.position_size,
            direction=trade_setup.direction.value,
            stop_loss=trade_setup.stop_loss,
            take_profits=trade_setup.take_profits
        )
        
        # Log trade execution
        self.logger.info(f"Executed {'trap' if trade_setup.is_trap_trade else 'regular'} trade: "
                        f"{trade_setup.direction.value} {symbol} at {trade_setup.entry_price:.6f}")
        
        # Store trade for analysis
        self.executed_trades.append({
            'position_id': position_id,
            'trade_setup': trade_setup,
            'execution_time': pd.Timestamp.now()
        })
        
        return position_id
    
    def _create_invalid_setup(self, validation_result: TradeValidationResult) -> TradeSetup:
        """Create an invalid trade setup"""
        return TradeSetup(
            symbol="",
            direction=TradeDirection.LONG,
            entry_price=0,
            stop_loss=0,
            take_profits=[],
            position_size=0,
            confidence=0,
            is_trap_trade=False,
            market_context={},
            validation_result=validation_result
        )
    
    def _validate_market_conditions(self, market_context: Dict) -> bool:
        """Validate that market conditions are suitable for trading"""
        
        # Check volatility
        volatility = market_context.get('volatility', 1.0)
        if volatility > 3.0:  # Extremely high volatility
            self.logger.warning(f"Market volatility too high: {volatility}")
            return False
        
        # Check spread conditions
        spread = market_context.get('spread', 0.001)
        max_spread = 0.005  # 0.5% max spread
        if spread > max_spread:
            self.logger.warning(f"Spread too wide: {spread:.4f}")
            return False
        
        # Check market structure alignment
        htf_structure = market_context.get('higher_timeframe_structure', {})
        if self._structures_conflicting(htf_structure):
            self.logger.warning("Conflicting higher timeframe structures")
            return False
        
        return True
    
    def _structures_conflicting(self, htf_structure: Dict) -> bool:
        """Check if higher timeframe structures are conflicting"""
        structures = list(htf_structure.values())
        
        if len(structures) < 2:
            return False
        
        # Count different structure types
        bullish_count = sum(1 for s in structures if s == MarketStructure.BULLISH)
        bearish_count = sum(1 for s in structures if s == MarketStructure.BEARISH)
        
        # Consider conflicting if opposing structures are roughly equal
        total_directional = bullish_count + bearish_count
        if total_directional > 0:
            conflict_ratio = min(bullish_count, bearish_count) / total_directional
            return conflict_ratio > 0.4  # More than 40% conflict
        
        return False
    
    def _has_clear_setup(self, market_context: Dict) -> bool:
        """Check if there's a clear trading setup in current market conditions"""
        
        # Check for trend clarity
        trend_strength = market_context.get('trend_strength', 0.5)
        if trend_strength < 0.6:  # Weak trend
            return False
        
        # Check for confluence factors
        confluence_score = self._calculate_confluence_score(market_context)
        return confluence_score >= 0.7  # 70% confluence required
    
    def _calculate_confluence_score(self, market_context: Dict) -> float:
        """Calculate confluence score based on multiple factors"""
        score = 0.0
        factors = 0
        
        # Higher timeframe alignment
        htf_structure = market_context.get('higher_timeframe_structure', {})
        if htf_structure:
            alignment_score = self._calculate_htf_alignment(htf_structure)
            score += alignment_score
            factors += 1
        
        # Volume confirmation
        volume_strength = market_context.get('volume_strength', 0.5)
        score += volume_strength
        factors += 1
        
        # Technical indicator alignment
        indicator_score = market_context.get('indicator_alignment', 0.5)
        score += indicator_score
        factors += 1
        
        # Price action quality
        price_action_score = market_context.get('price_action_quality', 0.5)
        score += price_action_score
        factors += 1
        
        return score / factors if factors > 0 else 0.0
    
    def _calculate_htf_alignment(self, htf_structure: Dict) -> float:
        """Calculate higher timeframe alignment score"""
        structures = list(htf_structure.values())
        
        if not structures:
            return 0.5
        
        # Count each structure type
        bullish_count = sum(1 for s in structures if s == MarketStructure.BULLISH)
        bearish_count = sum(1 for s in structures if s == MarketStructure.BEARISH)
        sideways_count = sum(1 for s in structures if s == MarketStructure.SIDEWAYS)
        
        total = len(structures)
        
        # Calculate alignment (highest proportion wins)
        max_count = max(bullish_count, bearish_count, sideways_count)
        alignment_ratio = max_count / total
        
        # Penalize sideways markets
        if max_count == sideways_count:
            alignment_ratio *= 0.5
        
        return alignment_ratio
    
    def _validate_risk_parameters(self, signal: TrapSignal, position_size: float, 
                                account_balance: float) -> bool:
        """Validate that risk parameters are within acceptable limits"""
        
        # Calculate risk amount
        risk_per_unit = abs(signal.entry_price - signal.stop_loss)
        total_risk = risk_per_unit * position_size
        risk_percentage = total_risk / account_balance
        
        # Check against maximum risk
        max_risk = self.config.risk_management.max_risk_per_trade
        if risk_percentage > max_risk * 1.5:  # Allow 50% buffer for exceptional setups
            self.logger.warning(f"Risk too high: {risk_percentage:.2%} > {max_risk:.2%}")
            return False
        
        # Validate reward-to-risk ratios
        if not self._validate_reward_ratios(signal):
            return False
        
        # Check position size reasonableness
        if position_size <= 0:
            self.logger.warning("Invalid position size calculated")
            return False
        
        return True
    
    def _validate_reward_ratios(self, signal: TrapSignal) -> bool:
        """Validate that reward-to-risk ratios are acceptable"""
        risk = abs(signal.entry_price - signal.stop_loss)
        
        if risk <= 0:
            return False
        
        # Check each take profit level
        min_rr_ratio = 1.0  # Minimum 1:1 risk-reward
        
        for i, tp in enumerate(signal.take_profits):
            reward = abs(tp - signal.entry_price)
            rr_ratio = reward / risk
            
            expected_ratios = [
                self.config.risk_management.tp1_ratio,
                self.config.risk_management.tp2_ratio,
                self.config.risk_management.tp3_ratio
            ]
            
            if i < len(expected_ratios):
                if rr_ratio < expected_ratios[i] * 0.8:  # Allow 20% tolerance
                    self.logger.warning(f"TP{i+1} ratio too low: {rr_ratio:.2f}")
                    return False
        
        return True
    
    def update_active_positions(self, current_prices: Dict[str, float]) -> List:
        """
        Update all active positions with current market prices
        """
        results = []
        
        for trade in self.executed_trades:
            position_id = trade['position_id']
            symbol = trade['trade_setup'].symbol
            
            if symbol in current_prices and position_id in self.risk_manager.positions:
                current_price = current_prices[symbol]
                
                # Update trailing stop
                self.risk_manager.update_trailing_stop(position_id, current_price)
                
                # Check exit conditions
                exit_result = self.risk_manager.check_exit_conditions(position_id, current_price)
                if exit_result:
                    results.append({
                        'position_id': position_id,
                        'exit_result': exit_result
                    })
        
        return results
    
    def get_execution_statistics(self) -> Dict:
        """Get execution and performance statistics"""
        total_executed = len(self.executed_trades)
        trap_trades = sum(1 for t in self.executed_trades if t['trade_setup'].is_trap_trade)
        
        # Get performance metrics from risk manager
        performance = self.risk_manager.get_performance_metrics()
        
        return {
            'total_trades_executed': total_executed,
            'trap_trades': trap_trades,
            'regular_trades': total_executed - trap_trades,
            'active_positions': len(self.risk_manager.positions),
            **performance
        }