"""
Main Trading Bot - Orchestrates all trading logic and decision making
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .models import (
    TradingConfig, TimeFrame, TradeDirection, RiskLevel,
    TrapSignal, EntrySignal, MarketStructure
)
from ..analyzers.trap_analyzer import TrapAnalyzer
from ..analyzers.entry_validator import EntryValidator
from ..analyzers.structural_analyzer import StructuralAnalyzer
from ..managers.risk_manager import RiskManager


class TradingBot:
    """
    Main trading bot that orchestrates all trading decisions.
    
    Features:
    - Advanced trap recognition and operation
    - Strict entry validation based on trading models
    - Dynamic risk management with trailing stops
    - Multi-timeframe structural analysis
    """
    
    def __init__(self, config: Optional[TradingConfig] = None, account_balance: float = 10000.0):
        self.config = config or TradingConfig()
        self.account_balance = account_balance
        
        # Initialize analyzers and managers
        self.trap_analyzer = TrapAnalyzer(self.config)
        self.entry_validator = EntryValidator(self.config)
        self.structural_analyzer = StructuralAnalyzer(self.config)
        self.risk_manager = RiskManager(self.config, account_balance)
        
        # Setup logging
        self._setup_logging()
        
        # Trading state
        self.is_running = False
        self.last_analysis_time = {}
        self.market_data_cache = {}
        
        self.logger.info("Trading Bot initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TradingBot')
    
    def start(self):
        """Start the trading bot."""
        self.is_running = True
        self.logger.info("Trading Bot started")
        
    def stop(self):
        """Stop the trading bot."""
        self.is_running = False
        self.logger.info("Trading Bot stopped")
    
    def analyze_market(self, market_data: Dict[TimeFrame, pd.DataFrame]) -> Dict:
        """
        Comprehensive market analysis across all timeframes.
        
        Args:
            market_data: Dict of timeframe -> OHLCV data
            
        Returns:
            Dict containing all analysis results
        """
        if not self.is_running:
            return {'error': 'Bot is not running'}
            
        analysis_results = {
            'timestamp': datetime.now(),
            'trap_signals': [],
            'entry_signals': [],
            'market_structures': {},
            'risk_metrics': self.risk_manager.get_risk_metrics()
        }
        
        try:
            # Update market data cache
            self.market_data_cache.update(market_data)
            
            # Analyze market structure across timeframes
            structures = self.structural_analyzer.analyze_market_structure(market_data)
            analysis_results['market_structures'] = structures
            
            # Analyze primary timeframe for signals
            primary_tf = self.config.timeframes_to_analyze[0]
            if primary_tf in market_data:
                price_data = market_data[primary_tf]
                volume_data = price_data.get('Volume', pd.Series())
                
                # Analyze traps
                trap_signals = self.trap_analyzer.analyze_traps(price_data, volume_data)
                analysis_results['trap_signals'] = trap_signals
                
                # Validate entries
                if len(price_data) > 0:
                    current_price = price_data['Close'].iloc[-1]
                    entry_signal = self.entry_validator.validate_entry(price_data, current_price)
                    if entry_signal:
                        analysis_results['entry_signals'] = [entry_signal]
                        
            self.logger.info(f"Market analysis completed. Found {len(analysis_results['trap_signals'])} trap signals")
            
        except Exception as e:
            self.logger.error(f"Error during market analysis: {str(e)}")
            analysis_results['error'] = str(e)
            
        return analysis_results
    
    def evaluate_trading_opportunity(
        self, 
        market_data: Dict[TimeFrame, pd.DataFrame], 
        force_analysis: bool = False
    ) -> Optional[Dict]:
        """
        Evaluate if current market conditions present a trading opportunity.
        
        Args:
            market_data: Market data across timeframes
            force_analysis: Force analysis even if recently done
            
        Returns:
            Trading opportunity dict if found, None otherwise
        """
        # Check if we should analyze (rate limiting)
        primary_tf = self.config.timeframes_to_analyze[0]
        now = datetime.now()
        
        if not force_analysis and primary_tf in self.last_analysis_time:
            time_since_last = now - self.last_analysis_time[primary_tf]
            if time_since_last < timedelta(minutes=1):  # Rate limit
                return None
                
        self.last_analysis_time[primary_tf] = now
        
        # Perform comprehensive analysis
        analysis = self.analyze_market(market_data)
        
        if 'error' in analysis:
            return None
            
        # Look for high-confidence opportunities
        opportunities = []
        
        # Check trap opportunities
        for trap_signal in analysis['trap_signals']:
            if trap_signal.safe_entry_exists and trap_signal.confidence >= self.config.min_trap_confidence:
                opportunity = self._evaluate_trap_opportunity(trap_signal, analysis)
                if opportunity:
                    opportunities.append(opportunity)
                    
        # Check entry opportunities
        for entry_signal in analysis['entry_signals']:
            if entry_signal.confidence >= self.config.min_entry_confidence:
                opportunity = self._evaluate_entry_opportunity(entry_signal, analysis)
                if opportunity:
                    opportunities.append(opportunity)
                    
        # Return best opportunity
        if opportunities:
            best_opportunity = max(opportunities, key=lambda x: x['total_score'])
            return best_opportunity
            
        return None
    
    def _evaluate_trap_opportunity(self, trap_signal: TrapSignal, analysis: Dict) -> Optional[Dict]:
        """Evaluate a trap trading opportunity."""
        if not trap_signal.entry_price:
            return None
            
        # Calculate stop loss based on trap type and liquidity zones
        stop_loss = self._calculate_trap_stop_loss(trap_signal)
        
        # Determine trade direction based on trap type
        direction = self._determine_trap_direction(trap_signal)
        
        # Validate against structural analysis
        primary_tf = self.config.timeframes_to_analyze[0]
        structure_validation = self.structural_analyzer.validate_trade_against_structure(
            trap_signal.entry_price, direction, primary_tf
        )
        
        if not structure_validation['valid']:
            return None
            
        # Calculate position size and risk
        position_size = self.risk_manager.calculate_position_size(
            trap_signal.entry_price, stop_loss, trap_signal.risk_level
        )
        
        estimated_risk = abs(trap_signal.entry_price - stop_loss) * position_size
        
        # Check if we should take this trade
        if not self.risk_manager.should_take_new_trade(estimated_risk):
            return None
            
        # Calculate total score
        total_score = self._calculate_opportunity_score(
            trap_signal.confidence, 
            structure_validation['structure_alignment'],
            trap_signal.risk_level,
            is_trap_trade=True
        )
        
        return {
            'type': 'trap',
            'signal': trap_signal,
            'entry_price': trap_signal.entry_price,
            'stop_loss': stop_loss,
            'direction': direction,
            'position_size': position_size,
            'estimated_risk': estimated_risk,
            'total_score': total_score,
            'structure_validation': structure_validation
        }
    
    def _evaluate_entry_opportunity(self, entry_signal: EntrySignal, analysis: Dict) -> Optional[Dict]:
        """Evaluate a regular entry opportunity."""
        
        # Calculate stop loss based on entry model and boss structure
        stop_loss = self._calculate_entry_stop_loss(entry_signal)
        
        # Validate against structural analysis
        primary_tf = self.config.timeframes_to_analyze[0]
        structure_validation = self.structural_analyzer.validate_trade_against_structure(
            entry_signal.price, entry_signal.direction, primary_tf
        )
        
        if not structure_validation['valid']:
            return None
            
        # Calculate position size and risk
        risk_level = self._assess_entry_risk_level(entry_signal)
        position_size = self.risk_manager.calculate_position_size(
            entry_signal.price, stop_loss, risk_level
        )
        
        estimated_risk = abs(entry_signal.price - stop_loss) * position_size
        
        # Check if we should take this trade
        if not self.risk_manager.should_take_new_trade(estimated_risk):
            return None
            
        # Calculate total score
        total_score = self._calculate_opportunity_score(
            entry_signal.confidence,
            structure_validation['structure_alignment'],
            risk_level,
            is_trap_trade=False
        )
        
        return {
            'type': 'entry',
            'signal': entry_signal,
            'entry_price': entry_signal.price,
            'stop_loss': stop_loss,
            'direction': entry_signal.direction,
            'position_size': position_size,
            'estimated_risk': estimated_risk,
            'total_score': total_score,
            'structure_validation': structure_validation
        }
    
    def _calculate_trap_stop_loss(self, trap_signal: TrapSignal) -> float:
        """Calculate stop loss for trap trades."""
        if not trap_signal.entry_price:
            return trap_signal.entry_price  # Fallback
            
        # Base stop loss on trap type and liquidity zones
        if trap_signal.trap_type.name in ['LIQUIDITY_ABOVE', 'INDUCTION_TRAP']:
            # For upward traps, stop below entry
            stop_distance = trap_signal.entry_price * 0.005  # 0.5% initial stop
            return trap_signal.entry_price - stop_distance
        else:
            # For downward traps, stop above entry
            stop_distance = trap_signal.entry_price * 0.005  # 0.5% initial stop
            return trap_signal.entry_price + stop_distance
    
    def _determine_trap_direction(self, trap_signal: TrapSignal) -> TradeDirection:
        """Determine trade direction for trap trades."""
        if trap_signal.trap_type.name == 'LIQUIDITY_ABOVE':
            return TradeDirection.LONG  # Targeting liquidity above
        elif trap_signal.trap_type.name == 'LIQUIDITY_BELOW':
            return TradeDirection.SHORT  # Targeting liquidity below
        else:
            # For double traps or induction, determine based on signal characteristics
            return TradeDirection.LONG  # Default, should be refined based on context
    
    def _calculate_entry_stop_loss(self, entry_signal: EntrySignal) -> float:
        """Calculate stop loss for regular entries."""
        base_stop_distance = entry_signal.price * 0.01  # 1% base stop
        
        # Adjust based on entry model
        if entry_signal.model_alignment.name == 'MODEL_2':
            # Tighter stops for Model 2 entries
            stop_distance = entry_signal.price * 0.005  # 0.5%
        else:
            stop_distance = base_stop_distance
            
        # Use boss structure if available
        if entry_signal.boss_structure and entry_signal.boss_structure.is_valid:
            if entry_signal.direction == TradeDirection.LONG:
                # Stop below boss structure low
                structure_stop = entry_signal.boss_structure.low_point * 0.999
                return min(entry_signal.price - stop_distance, structure_stop)
            else:
                # Stop above boss structure high
                structure_stop = entry_signal.boss_structure.high_point * 1.001
                return max(entry_signal.price + stop_distance, structure_stop)
                
        # Default stop calculation
        if entry_signal.direction == TradeDirection.LONG:
            return entry_signal.price - stop_distance
        else:
            return entry_signal.price + stop_distance
    
    def _assess_entry_risk_level(self, entry_signal: EntrySignal) -> RiskLevel:
        """Assess risk level for entry signals."""
        if entry_signal.confidence >= 0.9 and entry_signal.clean_zone:
            return RiskLevel.LOW
        elif entry_signal.confidence >= 0.8:
            return RiskLevel.MEDIUM
        elif entry_signal.confidence >= 0.6:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def _calculate_opportunity_score(
        self, 
        signal_confidence: float, 
        structure_alignment: float, 
        risk_level: RiskLevel,
        is_trap_trade: bool
    ) -> float:
        """Calculate total opportunity score."""
        score = signal_confidence * 0.4  # Base signal confidence
        
        # Structure alignment component
        score += max(0, structure_alignment) * 0.3
        
        # Risk level component
        risk_scores = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.15,
            RiskLevel.HIGH: 0.1,
            RiskLevel.EXTREME: 0.05
        }
        score += risk_scores.get(risk_level, 0.05)
        
        # Bonus for trap trades (if conditions are met)
        if is_trap_trade and signal_confidence >= 0.8:
            score += 0.1
            
        return min(score, 1.0)
    
    def execute_trade(self, opportunity: Dict) -> Optional[str]:
        """
        Execute a trading opportunity.
        
        Args:
            opportunity: Trading opportunity dict from evaluate_trading_opportunity
            
        Returns:
            Position ID if successful, None otherwise
        """
        if not self.is_running:
            self.logger.warning("Cannot execute trade - bot is not running")
            return None
            
        try:
            # Create position through risk manager
            position_id = self.risk_manager.create_position(
                entry_price=opportunity['entry_price'],
                direction=opportunity['direction'],
                stop_loss=opportunity['stop_loss'],
                risk_level=self._get_risk_level_from_score(opportunity['total_score']),
                is_trap_trade=opportunity['type'] == 'trap'
            )
            
            self.logger.info(
                f"Trade executed: {opportunity['type']} trade, "
                f"Position ID: {position_id}, "
                f"Entry: {opportunity['entry_price']}, "
                f"Direction: {opportunity['direction'].value}, "
                f"Size: {opportunity['position_size']}"
            )
            
            return position_id
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {str(e)}")
            return None
    
    def _get_risk_level_from_score(self, score: float) -> RiskLevel:
        """Convert opportunity score to risk level."""
        if score >= 0.8:
            return RiskLevel.LOW
        elif score >= 0.6:
            return RiskLevel.MEDIUM
        elif score >= 0.4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def update_positions(self, current_prices: Dict[str, float]) -> Dict:
        """
        Update all active positions with current market prices.
        
        Args:
            current_prices: Dict of position_id -> current_price
            
        Returns:
            Dict with update results and actions taken
        """
        if not self.is_running:
            return {'error': 'Bot is not running'}
            
        try:
            # Update trailing stops and check for TP/SL hits
            updates = self.risk_manager.update_trailing_stops(current_prices)
            
            actions_taken = []
            
            for position_id, update in updates.items():
                # Process TP hits
                if update['tp_hit']:
                    result = self.risk_manager.process_tp_hit(position_id, update['tp_hit'])
                    actions_taken.append(f"TP{update['tp_hit'][-1]} hit for {position_id}: {result}")
                    
                # Process stop hits
                if update['stop_hit']:
                    result = self.risk_manager.close_position(
                        position_id, update['current_price'], 'stop_loss'
                    )
                    actions_taken.append(f"Stop loss hit for {position_id}: {result}")
                    
            self.logger.info(f"Position updates completed. Actions taken: {len(actions_taken)}")
            
            return {
                'updates': updates,
                'actions_taken': actions_taken,
                'risk_metrics': self.risk_manager.get_risk_metrics()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {str(e)}")
            return {'error': str(e)}
    
    def get_status(self) -> Dict:
        """Get comprehensive bot status."""
        return {
            'is_running': self.is_running,
            'account_balance': self.account_balance,
            'config': self.config.__dict__,
            'active_positions': self.risk_manager.get_all_positions(),
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'last_analysis_times': self.last_analysis_time
        }
    
    def shutdown(self):
        """Gracefully shutdown the bot."""
        self.stop()
        
        # Close all positions (optional - could be left open)
        # This would require current market prices
        
        self.logger.info("Trading Bot shutdown completed")