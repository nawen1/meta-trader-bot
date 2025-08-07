"""
Main Trading Bot - Advanced Meta Trading Bot with trap identification and risk management
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from .config import BotConfig, default_config
from .market_analysis import MarketAnalyzer, TrapSignal, MarketStructure
from .risk_management import RiskManager
from .trade_executor import TradeExecutor, TradeValidationResult, TradeDirection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MetaTradingBot:
    """
    Advanced Meta Trading Bot with sophisticated trap identification and risk management
    
    Key Features:
    - Trap identification based on liquidity analysis
    - Safe trap operation with entry point validation
    - Advanced risk management with trailing stops and multiple TP levels
    - Higher timeframe context analysis
    - Trade avoidance when no valid setup exists
    """
    
    def __init__(self, config: Optional[BotConfig] = None, account_balance: float = 10000.0):
        """
        Initialize the Meta Trading Bot
        
        Args:
            config: Bot configuration (uses default if None)
            account_balance: Starting account balance
        """
        self.config = config or default_config
        self.account_balance = account_balance
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.market_analyzer = MarketAnalyzer(self.config)
        self.risk_manager = RiskManager(self.config)
        self.trade_executor = TradeExecutor(self.config, self.risk_manager)
        
        # State tracking
        self.last_analysis_time = None
        self.market_context = {}
        self.active_signals = []
        
        self.logger.info("Meta Trading Bot initialized successfully")
    
    def analyze_market(self, symbol: str, data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Perform comprehensive market analysis including trap identification
        
        Args:
            symbol: Trading symbol
            data: Dictionary with timeframe keys and DataFrame values
                 Expected keys: '1m', '5m', '15m', '1h', '4h', '1d'
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            self.logger.info(f"Starting market analysis for {symbol}")
            
            # Get primary timeframe data (assume 15m for trap analysis)
            primary_tf = '15m'
            if primary_tf not in data:
                self.logger.error(f"Primary timeframe {primary_tf} not available")
                return {}
            
            df = data[primary_tf]
            
            # 1. Analyze higher timeframes for context
            htf_analysis = self.market_analyzer.analyze_higher_timeframes(data)
            
            # 2. Identify liquidity levels
            liquidity_levels = self.market_analyzer.identify_liquidity_levels(df)
            
            # 3. Identify trap signals
            trap_signals = self.market_analyzer.identify_traps(df, liquidity_levels)
            
            # 4. Calculate market metrics
            market_metrics = self._calculate_market_metrics(df, data)
            
            # 5. Assess overall market context
            market_context = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'higher_timeframe_structure': htf_analysis,
                'liquidity_levels': liquidity_levels,
                'trap_signals': trap_signals,
                'market_metrics': market_metrics,
                'volatility': market_metrics.get('volatility', 1.0),
                'trend_strength': market_metrics.get('trend_strength', 0.5),
                'volume_strength': market_metrics.get('volume_strength', 0.5),
                'spread': market_metrics.get('spread', 0.001),
                'indicator_alignment': market_metrics.get('indicator_alignment', 0.5),
                'price_action_quality': market_metrics.get('price_action_quality', 0.5)
            }
            
            self.market_context = market_context
            self.last_analysis_time = datetime.now()
            
            self.logger.info(f"Market analysis completed. Found {len(trap_signals)} trap signals")
            
            return market_context
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            return {}
    
    def generate_trading_signals(self, market_context: Dict) -> List[Dict]:
        """
        Generate trading signals based on market analysis
        
        Args:
            market_context: Results from analyze_market()
        
        Returns:
            List of trading signals with validation results
        """
        signals = []
        
        try:
            trap_signals = market_context.get('trap_signals', [])
            
            # Process trap signals
            for trap_signal in trap_signals:
                signal_dict = self._process_trap_signal(trap_signal, market_context)
                if signal_dict:
                    signals.append(signal_dict)
            
            # Look for regular trading opportunities if no trap signals
            if not signals and not self.config.force_trades:
                regular_signal = self._look_for_regular_opportunities(market_context)
                if regular_signal:
                    signals.append(regular_signal)
            
            self.active_signals = signals
            self.logger.info(f"Generated {len(signals)} trading signals")
            
        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
        
        return signals
    
    def execute_signals(self, signals: List[Dict], symbol: str) -> List[str]:
        """
        Execute validated trading signals
        
        Args:
            signals: List of trading signals from generate_trading_signals()
            symbol: Trading symbol
        
        Returns:
            List of position IDs for executed trades
        """
        executed_positions = []
        
        try:
            for signal in signals:
                if signal.get('trade_setup') and signal['trade_setup'].validation_result == TradeValidationResult.VALID:
                    position_id = self.trade_executor.execute_trade(signal['trade_setup'], symbol)
                    if position_id:
                        executed_positions.append(position_id)
                        self.logger.info(f"Executed trade: {position_id}")
                else:
                    self.logger.warning(f"Skipping invalid signal: {signal.get('validation_result', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error executing signals: {str(e)}")
        
        return executed_positions
    
    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Update all active positions with current market data
        
        Args:
            current_prices: Dictionary of symbol -> current price
        
        Returns:
            List of position updates/exits
        """
        try:
            results = self.trade_executor.update_active_positions(current_prices)
            
            if results:
                self.logger.info(f"Updated {len(results)} positions")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {str(e)}")
            return []
    
    def run_trading_cycle(self, symbol: str, data: Dict[str, pd.DataFrame], 
                         current_prices: Dict[str, float]) -> Dict:
        """
        Run a complete trading cycle: analyze -> signal -> execute -> update
        
        Args:
            symbol: Trading symbol
            data: Market data for different timeframes
            current_prices: Current market prices
        
        Returns:
            Dictionary with cycle results
        """
        cycle_start = datetime.now()
        self.logger.info(f"Starting trading cycle for {symbol}")
        
        try:
            # 1. Market Analysis
            market_context = self.analyze_market(symbol, data)
            if not market_context:
                return {'error': 'Market analysis failed'}
            
            # 2. Generate Signals
            signals = self.generate_trading_signals(market_context)
            
            # 3. Execute Valid Signals
            executed_positions = self.execute_signals(signals, symbol)
            
            # 4. Update Existing Positions
            position_updates = self.update_positions(current_prices)
            
            # 5. Get Performance Metrics
            portfolio_metrics = self.get_portfolio_status()
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            results = {
                'cycle_start': cycle_start,
                'cycle_duration_seconds': cycle_duration,
                'market_analysis': {
                    'trap_signals_found': len(market_context.get('trap_signals', [])),
                    'liquidity_levels': len(market_context.get('liquidity_levels', [])),
                    'higher_timeframe_structures': market_context.get('higher_timeframe_structure', {}),
                    'market_volatility': market_context.get('volatility', 0),
                    'trend_strength': market_context.get('trend_strength', 0)
                },
                'signals_generated': len(signals),
                'positions_executed': len(executed_positions),
                'position_updates': len(position_updates),
                'portfolio_status': portfolio_metrics,
                'executed_position_ids': executed_positions
            }
            
            self.logger.info(f"Trading cycle completed in {cycle_duration:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {str(e)}")
            return {'error': str(e)}
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status and performance metrics"""
        try:
            portfolio_risk = self.risk_manager.get_portfolio_risk()
            performance_metrics = self.risk_manager.get_performance_metrics()
            execution_stats = self.trade_executor.get_execution_statistics()
            
            return {
                'account_balance': self.account_balance,
                'portfolio_risk': portfolio_risk,
                'performance_metrics': performance_metrics,
                'execution_statistics': execution_stats,
                'last_analysis': self.last_analysis_time,
                'active_signals': len(self.active_signals)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {str(e)}")
            return {}
    
    def _process_trap_signal(self, trap_signal: TrapSignal, market_context: Dict) -> Optional[Dict]:
        """Process a trap signal and create trade setup"""
        try:
            # Validate trap trade
            trade_setup = self.trade_executor.validate_trap_trade(
                trap_signal, market_context, self.account_balance
            )
            
            return {
                'signal_type': 'trap',
                'trap_signal': trap_signal,
                'trade_setup': trade_setup,
                'validation_result': trade_setup.validation_result,
                'confidence': trap_signal.confidence,
                'safe_entry_exists': trap_signal.safe_entry_exists
            }
            
        except Exception as e:
            self.logger.error(f"Error processing trap signal: {str(e)}")
            return None
    
    def _look_for_regular_opportunities(self, market_context: Dict) -> Optional[Dict]:
        """Look for regular (non-trap) trading opportunities"""
        try:
            # This is a simplified example - in practice, you'd implement
            # more sophisticated regular signal detection
            
            market_metrics = market_context.get('market_metrics', {})
            trend_strength = market_metrics.get('trend_strength', 0)
            
            if trend_strength < 0.6:  # Weak trend, no clear opportunity
                return None
            
            # Example regular signal (would be more sophisticated in practice)
            htf_structures = market_context.get('higher_timeframe_structure', {})
            
            # Check for aligned higher timeframe bullish structure
            bullish_count = sum(1 for s in htf_structures.values() if s == MarketStructure.BULLISH)
            bearish_count = sum(1 for s in htf_structures.values() if s == MarketStructure.BEARISH)
            
            if bullish_count > bearish_count and trend_strength > 0.7:
                # Create a sample bullish setup
                current_price = 1.0  # Would get from market data
                entry_price = current_price
                stop_loss = current_price * 0.98  # 2% stop
                take_profits = [
                    current_price * 1.02,  # 2% TP1
                    current_price * 1.04,  # 4% TP2
                    current_price * 1.06   # 6% TP3
                ]
                
                trade_setup = self.trade_executor.validate_regular_trade(
                    entry_price, stop_loss, take_profits, TradeDirection.LONG,
                    market_context, self.account_balance
                )
                
                return {
                    'signal_type': 'regular',
                    'direction': 'long',
                    'trade_setup': trade_setup,
                    'validation_result': trade_setup.validation_result,
                    'confidence': 0.7
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error looking for regular opportunities: {str(e)}")
            return None
    
    def _calculate_market_metrics(self, df: pd.DataFrame, data: Dict[str, pd.DataFrame]) -> Dict:
        """Calculate various market metrics"""
        try:
            metrics = {}
            
            # Volatility (using ATR)
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            atr = df['true_range'].rolling(14).mean().iloc[-1]
            
            # Normalized volatility
            avg_price = df['close'].rolling(20).mean().iloc[-1]
            metrics['volatility'] = atr / avg_price if avg_price > 0 else 1.0
            
            # Trend strength using ADX concept
            df['dm_plus'] = np.where((df['high'] - df['high'].shift()) > (df['low'].shift() - df['low']),
                                   np.maximum(df['high'] - df['high'].shift(), 0), 0)
            df['dm_minus'] = np.where((df['low'].shift() - df['low']) > (df['high'] - df['high'].shift()),
                                    np.maximum(df['low'].shift() - df['low'], 0), 0)
            
            metrics['trend_strength'] = min(1.0, np.abs(df['dm_plus'].rolling(14).mean().iloc[-1] - 
                                                       df['dm_minus'].rolling(14).mean().iloc[-1]) / atr)
            
            # Volume strength
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            metrics['volume_strength'] = min(2.0, current_volume / avg_volume) / 2.0 if avg_volume > 0 else 0.5
            
            # Spread (simplified)
            metrics['spread'] = 0.001  # Would calculate from bid/ask if available
            
            # Indicator alignment (simplified - would use actual indicators)
            metrics['indicator_alignment'] = 0.6
            
            # Price action quality (simplified)
            metrics['price_action_quality'] = 0.7
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating market metrics: {str(e)}")
            return {
                'volatility': 1.0,
                'trend_strength': 0.5,
                'volume_strength': 0.5,
                'spread': 0.001,
                'indicator_alignment': 0.5,
                'price_action_quality': 0.5
            }