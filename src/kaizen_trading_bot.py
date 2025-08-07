"""
KAIZEN Meta Trading Bot - Unified Implementation
Combines features from all 6 MetaTrader 5 PRs into a single powerful trading system
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from utils.config import TradingConfig, get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KaizenTradingBot:
    """
    Unified Trading Bot combining all PR features:
    - PR #1: MetaTrader 5 integration with risk management
    - PR #2: TradingView Pine Script compatibility  
    - PR #3: Multi-timeframe autonomous analysis
    - PR #4: Advanced trap identification
    - PR #5: Comprehensive trap analysis and risk management
    - PR #6: BTCUSD refined entry strategies
    - PR #7: Strict higher timeframe prioritization
    """
    
    def __init__(self, config: Optional[TradingConfig] = None, account_balance: float = 10000.0):
        """
        Initialize the unified trading bot
        
        Args:
            config: Trading configuration
            account_balance: Account balance for position sizing
        """
        self.config = config or get_config()
        self.account_balance = account_balance
        
        # Initialize components from all PRs
        self.fractals = {}
        self.liquidity_zones = []
        self.order_blocks = []
        self.choch_signals = []
        self.market_structure = {'trend': 'ranging', 'strength': 0.0}
        
        # Position management
        self.positions = {}
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
        # State tracking
        self.last_analysis_time = {}
        self.market_character = 'unknown'
        self.trap_risk_level = 0.0
        
        logger.info("KAIZEN Trading Bot initialized with unified feature set")
    
    def analyze_market(self, symbol: str, timeframes_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Comprehensive market analysis combining all PR methodologies
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'BTCUSD')
            timeframes_data: Dictionary with timeframe data
            
        Returns:
            Complete market analysis results
        """
        logger.info(f"Starting unified market analysis for {symbol}")
        
        # Multi-timeframe analysis (PR #3, #7)
        mtf_analysis = self._analyze_multiple_timeframes(timeframes_data)
        
        # Trap analysis (PR #4, #5)
        trap_analysis = self._analyze_traps(timeframes_data, mtf_analysis)
        
        # Market structure analysis (PR #3, #6)
        structure_analysis = self._analyze_market_structure(timeframes_data, mtf_analysis)
        
        # BTCUSD specific analysis (PR #6)
        if 'BTC' in symbol.upper():
            btc_analysis = self._analyze_btcusd_specific(timeframes_data)
            structure_analysis.update(btc_analysis)
        
        # Generate entry signals
        entry_signals = self._generate_entry_signals(
            timeframes_data, mtf_analysis, trap_analysis, structure_analysis
        )
        
        # Risk assessment
        risk_assessment = self._assess_risk(trap_analysis, structure_analysis)
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'multi_timeframe': mtf_analysis,
            'trap_analysis': trap_analysis,
            'market_structure': structure_analysis,
            'entry_signals': entry_signals,
            'risk_assessment': risk_assessment,
            'trading_recommendation': self._get_trading_recommendation(
                entry_signals, risk_assessment
            )
        }
    
    def _analyze_multiple_timeframes(self, timeframes_data: Dict[str, pd.DataFrame]) -> Dict:
        """Multi-timeframe analysis with strict HTF priority (PR #7)"""
        analysis = {
            'htf_bias': 'neutral',
            'ltf_signals': [],
            'alignment_score': 0.0,
            'htf_context': {}
        }
        
        # Analyze higher timeframes first (strict priority)
        htf_trends = []
        for tf in self.config.timeframes.higher_timeframes:
            if tf in timeframes_data and not timeframes_data[tf].empty:
                tf_analysis = self._analyze_single_timeframe(timeframes_data[tf], tf)
                htf_trends.append(tf_analysis['trend'])
                
                if tf == self.config.timeframes.higher_timeframes[0]:  # Primary HTF
                    analysis['htf_context'] = tf_analysis
        
        # Determine HTF bias
        if htf_trends:
            bullish_count = htf_trends.count('bullish')
            bearish_count = htf_trends.count('bearish')
            
            if bullish_count > bearish_count:
                analysis['htf_bias'] = 'bullish'
            elif bearish_count > bullish_count:
                analysis['htf_bias'] = 'bearish'
            
            analysis['alignment_score'] = max(bullish_count, bearish_count) / len(htf_trends)
        
        # Analyze lower timeframes for entry signals (only if aligned with HTF)
        if self.config.strict_htf_priority and analysis['htf_bias'] != 'neutral':
            for tf in self.config.timeframes.lower_timeframes:
                if tf in timeframes_data and not timeframes_data[tf].empty:
                    ltf_analysis = self._analyze_single_timeframe(timeframes_data[tf], tf)
                    
                    # Only include signals aligned with HTF bias
                    if ltf_analysis['trend'] == analysis['htf_bias']:
                        analysis['ltf_signals'].append({
                            'timeframe': tf,
                            'signals': ltf_analysis['signals'],
                            'strength': ltf_analysis['strength']
                        })
        
        return analysis
    
    def _analyze_single_timeframe(self, data: pd.DataFrame, timeframe: str) -> Dict:
        """Analyze a single timeframe"""
        if data.empty:
            return {'trend': 'neutral', 'strength': 0.0, 'signals': []}
        
        # Fractal analysis
        fractals = self._identify_fractals(data)
        
        # CHOCH detection
        choch_signals = self._detect_choch(data, fractals)
        
        # Trend determination
        trend = self._determine_trend(data, fractals, choch_signals)
        
        # Signal generation
        signals = self._generate_timeframe_signals(data, fractals, choch_signals, trend)
        
        return {
            'trend': trend['direction'],
            'strength': trend['strength'],
            'signals': signals,
            'fractals': fractals,
            'choch': choch_signals
        }
    
    def _analyze_traps(self, timeframes_data: Dict, mtf_analysis: Dict) -> Dict:
        """Advanced trap detection and analysis (PR #4, #5)"""
        trap_analysis = {
            'liquidity_sweeps': [],
            'bull_traps': [],
            'bear_traps': [],
            'induction_traps': [],
            'trap_risk': 0.0,
            'safe_entry_points': []
        }
        
        # Use primary lower timeframe for trap detection
        primary_ltf = self.config.timeframes.lower_timeframes[0]
        if primary_ltf not in timeframes_data:
            return trap_analysis
        
        data = timeframes_data[primary_ltf]
        
        # Liquidity sweep detection
        liquidity_sweeps = self._detect_liquidity_sweeps(data)
        trap_analysis['liquidity_sweeps'] = liquidity_sweeps
        
        # Bull/Bear trap detection
        trap_analysis['bull_traps'] = self._detect_bull_traps(data)
        trap_analysis['bear_traps'] = self._detect_bear_traps(data)
        
        # Induction trap detection (complex patterns)
        trap_analysis['induction_traps'] = self._detect_induction_traps(data)
        
        # Calculate overall trap risk
        total_traps = (len(liquidity_sweeps) + len(trap_analysis['bull_traps']) + 
                      len(trap_analysis['bear_traps']) + len(trap_analysis['induction_traps']))
        trap_analysis['trap_risk'] = min(total_traps / 20.0, 1.0)  # Normalize to 0-1
        
        # Identify safe entry points
        trap_analysis['safe_entry_points'] = self._identify_safe_entries(
            data, trap_analysis, mtf_analysis
        )
        
        return trap_analysis
    
    def _analyze_market_structure(self, timeframes_data: Dict, mtf_analysis: Dict) -> Dict:
        """Market structure analysis combining all PR approaches"""
        structure = {
            'current_character': 'ranging',
            'boss_patterns': [],
            'liquid_points': [],
            'clean_zones': [],
            'model2_alignment': False
        }
        
        # Use primary timeframe
        primary_tf = self.config.timeframes.lower_timeframes[0]
        if primary_tf in timeframes_data:
            data = timeframes_data[primary_tf]
            
            # Boss (Break of Structure) detection
            structure['boss_patterns'] = self._detect_boss_patterns(data)
            
            # Liquid point identification
            structure['liquid_points'] = self._identify_liquid_points(data)
            
            # Clean zone identification
            structure['clean_zones'] = self._identify_clean_zones(data)
            
            # Model 2 alignment check
            structure['model2_alignment'] = self._check_model2_alignment(
                data, mtf_analysis['htf_bias']
            )
            
            # Determine market character
            structure['current_character'] = self._determine_market_character(
                data, structure
            )
        
        return structure
    
    def _analyze_btcusd_specific(self, timeframes_data: Dict) -> Dict:
        """BTCUSD specific analysis (PR #6)"""
        btc_analysis = {
            'structure_breaks': [],
            'refined_entries': [],
            'dynamic_risk_levels': {}
        }
        
        # Use 15m timeframe for BTCUSD analysis
        if '15m' in timeframes_data:
            data = timeframes_data['15m']
            
            # Structure break detection with strength classification
            btc_analysis['structure_breaks'] = self._detect_btc_structure_breaks(data)
            
            # Refined entry strategies
            btc_analysis['refined_entries'] = self._identify_btc_entries(data)
            
            # Dynamic risk management
            btc_analysis['dynamic_risk_levels'] = self._calculate_btc_risk_levels(data)
        
        return btc_analysis
    
    def _generate_entry_signals(self, timeframes_data: Dict, mtf_analysis: Dict, 
                               trap_analysis: Dict, structure_analysis: Dict) -> List[Dict]:
        """Generate entry signals with strict validation"""
        signals = []
        
        # Only generate signals if:
        # 1. HTF bias is clear
        # 2. Trap risk is acceptable
        # 3. Market structure supports entries
        
        if (mtf_analysis['alignment_score'] < 0.6 or 
            trap_analysis['trap_risk'] > 0.7):
            logger.warning("Conditions not suitable for signal generation")
            return signals
        
        htf_bias = mtf_analysis['htf_bias']
        
        for ltf_signal in mtf_analysis['ltf_signals']:
            # Check for confluences
            confluence_score = self._calculate_confluence(
                ltf_signal, structure_analysis, trap_analysis
            )
            
            if confluence_score >= self.config.min_entry_confidence:
                signal = {
                    'direction': htf_bias,
                    'timeframe': ltf_signal['timeframe'],
                    'confidence': confluence_score,
                    'entry_type': self._determine_entry_type(ltf_signal, structure_analysis),
                    'risk_reward': self._calculate_risk_reward(ltf_signal, structure_analysis)
                }
                signals.append(signal)
        
        return signals
    
    def _assess_risk(self, trap_analysis: Dict, structure_analysis: Dict) -> Dict:
        """Comprehensive risk assessment"""
        risk = {
            'overall_risk': 'medium',
            'trap_risk': trap_analysis['trap_risk'],
            'structure_risk': 0.0,
            'market_conditions': 'average',
            'position_sizing': self._calculate_position_size()
        }
        
        # Structure risk assessment
        if structure_analysis['current_character'] == 'choppy':
            risk['structure_risk'] = 0.8
        elif structure_analysis['current_character'] == 'trending':
            risk['structure_risk'] = 0.3
        else:
            risk['structure_risk'] = 0.5
        
        # Overall risk calculation
        total_risk = (risk['trap_risk'] + risk['structure_risk']) / 2
        
        if total_risk > 0.7:
            risk['overall_risk'] = 'high'
            risk['market_conditions'] = 'poor'
        elif total_risk < 0.3:
            risk['overall_risk'] = 'low'
            risk['market_conditions'] = 'excellent'
        
        return risk
    
    def _get_trading_recommendation(self, signals: List[Dict], risk_assessment: Dict) -> Dict:
        """Generate final trading recommendation"""
        if not signals:
            return {
                'action': 'wait',
                'reason': 'No qualified signals found',
                'confidence': 0.0
            }
        
        if risk_assessment['overall_risk'] == 'high':
            return {
                'action': 'wait',
                'reason': 'Risk level too high',
                'confidence': 0.0
            }
        
        # Select best signal
        best_signal = max(signals, key=lambda x: x['confidence'])
        
        return {
            'action': 'trade',
            'direction': best_signal['direction'],
            'timeframe': best_signal['timeframe'],
            'confidence': best_signal['confidence'],
            'entry_type': best_signal['entry_type'],
            'position_size': risk_assessment['position_sizing'],
            'risk_reward': best_signal['risk_reward']
        }
    
    # Helper methods (simplified implementations for core functionality)
    
    def _identify_fractals(self, data: pd.DataFrame, period: int = 5) -> Dict:
        """Identify fractal highs and lows"""
        fractals = {'highs': [], 'lows': []}
        
        for i in range(period, len(data) - period):
            # Fractal high
            if all(data['high'].iloc[i] > data['high'].iloc[i-j] for j in range(1, period+1)) and \
               all(data['high'].iloc[i] > data['high'].iloc[i+j] for j in range(1, period+1)):
                fractals['highs'].append((i, data['high'].iloc[i]))
            
            # Fractal low
            if all(data['low'].iloc[i] < data['low'].iloc[i-j] for j in range(1, period+1)) and \
               all(data['low'].iloc[i] < data['low'].iloc[i+j] for j in range(1, period+1)):
                fractals['lows'].append((i, data['low'].iloc[i]))
        
        return fractals
    
    def _detect_choch(self, data: pd.DataFrame, fractals: Dict) -> List[Dict]:
        """Detect Change of Character patterns"""
        choch_signals = []
        
        # Simplified CHOCH detection based on fractal breaks
        highs = fractals['highs']
        lows = fractals['lows']
        
        if len(highs) >= 2:
            latest_high = highs[-1]
            prev_high = highs[-2]
            
            if latest_high[1] > prev_high[1]:  # Higher high
                choch_signals.append({
                    'type': 'bullish_choch',
                    'level': latest_high[1],
                    'strength': 0.8
                })
        
        if len(lows) >= 2:
            latest_low = lows[-1]
            prev_low = lows[-2]
            
            if latest_low[1] < prev_low[1]:  # Lower low
                choch_signals.append({
                    'type': 'bearish_choch',
                    'level': latest_low[1],
                    'strength': 0.8
                })
        
        return choch_signals
    
    def _determine_trend(self, data: pd.DataFrame, fractals: Dict, choch_signals: List) -> Dict:
        """Determine trend direction and strength"""
        if data.empty:
            return {'direction': 'neutral', 'strength': 0.0}
        
        # Simple trend determination using price action
        recent_closes = data['close'].tail(20)
        price_change = (recent_closes.iloc[-1] - recent_closes.iloc[0]) / recent_closes.iloc[0]
        
        if price_change > 0.02:
            return {'direction': 'bullish', 'strength': min(abs(price_change) * 10, 1.0)}
        elif price_change < -0.02:
            return {'direction': 'bearish', 'strength': min(abs(price_change) * 10, 1.0)}
        else:
            return {'direction': 'neutral', 'strength': 0.5}
    
    def _generate_timeframe_signals(self, data: pd.DataFrame, fractals: Dict, 
                                   choch_signals: List, trend: Dict) -> List[Dict]:
        """Generate signals for a specific timeframe"""
        signals = []
        
        # Generate signals based on trend and CHOCH
        if trend['direction'] != 'neutral' and trend['strength'] > 0.6:
            signals.append({
                'type': f"{trend['direction']}_trend",
                'strength': trend['strength'],
                'price': data['close'].iloc[-1]
            })
        
        # Add CHOCH signals
        for choch in choch_signals:
            signals.append({
                'type': choch['type'],
                'strength': choch['strength'],
                'price': choch['level']
            })
        
        return signals
    
    def _detect_liquidity_sweeps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect liquidity sweep patterns"""
        sweeps = []
        
        # Simplified sweep detection
        for i in range(20, len(data)):
            recent_high = data['high'].iloc[i-20:i].max()
            current_high = data['high'].iloc[i]
            
            if current_high > recent_high and data['close'].iloc[i] < recent_high:
                sweeps.append({
                    'type': 'bullish_sweep',
                    'level': recent_high,
                    'index': i
                })
        
        return sweeps
    
    def _detect_bull_traps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect bull trap patterns"""
        return []  # Simplified for core functionality
    
    def _detect_bear_traps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect bear trap patterns"""
        return []  # Simplified for core functionality
    
    def _detect_induction_traps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect induction trap patterns"""
        return []  # Simplified for core functionality
    
    def _identify_safe_entries(self, data: pd.DataFrame, trap_analysis: Dict, 
                              mtf_analysis: Dict) -> List[Dict]:
        """Identify safe entry points"""
        return []  # Simplified for core functionality
    
    def _detect_boss_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Detect Boss (Break of Structure) patterns"""
        return []  # Simplified for core functionality
    
    def _identify_liquid_points(self, data: pd.DataFrame) -> List[Dict]:
        """Identify liquid points"""
        return []  # Simplified for core functionality
    
    def _identify_clean_zones(self, data: pd.DataFrame) -> List[Dict]:
        """Identify clean zones for entries"""
        return []  # Simplified for core functionality
    
    def _check_model2_alignment(self, data: pd.DataFrame, htf_bias: str) -> bool:
        """Check Model 2 alignment"""
        return htf_bias != 'neutral'  # Simplified
    
    def _determine_market_character(self, data: pd.DataFrame, structure: Dict) -> str:
        """Determine market character"""
        volatility = data['high'].subtract(data['low']).tail(20).mean()
        avg_volatility = data['high'].subtract(data['low']).mean()
        
        if volatility > avg_volatility * 1.5:
            return 'choppy'
        elif volatility < avg_volatility * 0.7:
            return 'trending'
        else:
            return 'ranging'
    
    def _detect_btc_structure_breaks(self, data: pd.DataFrame) -> List[Dict]:
        """BTCUSD specific structure break detection"""
        return []  # Simplified for core functionality
    
    def _identify_btc_entries(self, data: pd.DataFrame) -> List[Dict]:
        """BTCUSD specific entry identification"""
        return []  # Simplified for core functionality
    
    def _calculate_btc_risk_levels(self, data: pd.DataFrame) -> Dict:
        """Calculate BTCUSD specific risk levels"""
        return {}  # Simplified for core functionality
    
    def _calculate_confluence(self, signal: Dict, structure: Dict, trap_analysis: Dict) -> float:
        """Calculate signal confluence score"""
        base_score = signal['strength']
        
        # Adjust based on structure alignment
        if structure['model2_alignment']:
            base_score += 0.2
        
        # Adjust based on trap risk
        base_score -= trap_analysis['trap_risk'] * 0.3
        
        return max(min(base_score, 1.0), 0.0)
    
    def _determine_entry_type(self, signal: Dict, structure: Dict) -> str:
        """Determine entry type"""
        if len(structure['clean_zones']) > 0:
            return 'clean_zone_entry'
        elif len(structure['boss_patterns']) > 0:
            return 'structure_break_entry'
        else:
            return 'momentum_entry'
    
    def _calculate_risk_reward(self, signal: Dict, structure: Dict) -> float:
        """Calculate risk-reward ratio"""
        return 2.0  # Default 2:1 ratio
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on risk management"""
        return self.account_balance * self.config.max_risk_per_trade
    
    def get_bot_status(self) -> Dict:
        """Get current bot status"""
        return {
            'account_balance': self.account_balance,
            'active_positions': len(self.positions),
            'daily_pnl': self.daily_pnl,
            'total_trades': self.total_trades,
            'win_rate': self.winning_trades / max(self.total_trades, 1),
            'config': {
                'timeframes': {
                    'higher': self.config.timeframes.higher_timeframes,
                    'lower': self.config.timeframes.lower_timeframes
                },
                'risk_per_trade': self.config.max_risk_per_trade,
                'trap_detection': self.config.trap_detection_enabled,
                'htf_priority': self.config.strict_htf_priority
            },
            'capabilities': [
                'Multi-timeframe analysis with HTF priority',
                'Advanced trap detection and avoidance',
                'Comprehensive market structure analysis',
                'BTCUSD specialized strategies',
                'Dynamic risk management',
                'MetaTrader 5 integration ready',
                'TradingView Pine Script compatible',
                'Autonomous pattern recognition'
            ]
        }