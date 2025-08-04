"""
Main Trading Bot Class
Integrates all analysis components for autonomous trading decisions
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from utils.config import TradingConfig, get_config
from utils.data_handler import DataHandler
from analysis.timeframe_analyzer import TimeframeAnalyzer
from analysis.market_structure import MarketStructureAnalyzer
from analysis.fractals import FractalAnalyzer
from analysis.choch_detector import CHOCHDetector
from analysis.liquidity_zones import LiquidityZoneDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaTradingBot:
    """
    Advanced Trading Bot with Multi-Timeframe Analysis and Autonomous Decision Making
    
    Features:
    - Multi-timeframe analysis (higher TF context for lower TF entries)
    - Independent identification of key points (liquidity zones, fractals, CHOCH)
    - Proper fractal identification within market structure
    - False break vs legitimate momentum differentiation
    - Adaptive trap and misleading setup detection
    """
    
    def __init__(self, config: Optional[TradingConfig] = None):
        """
        Initialize the trading bot
        
        Args:
            config: Trading configuration (uses default if None)
        """
        self.config = config or get_config()
        self.data_handler = DataHandler()
        
        # Initialize analysis components
        self.timeframe_analyzer = TimeframeAnalyzer(self.config)
        self.market_structure_analyzer = MarketStructureAnalyzer(
            false_break_threshold=self.config.false_break_threshold,
            momentum_confirmation_period=self.config.momentum_confirmation_period
        )
        self.fractal_analyzer = FractalAnalyzer(period=self.config.fractal_period)
        self.choch_detector = CHOCHDetector(confirmation_period=self.config.choch_confirmation_period)
        self.liquidity_detector = LiquidityZoneDetector(zone_buffer=self.config.liquidity_zone_buffer)
        
        # State management
        self.current_positions = {}
        self.analysis_cache = {}
        self.last_analysis_time = {}
        self.reassessment_counter = 0
        
        logger.info("Meta Trading Bot initialized with advanced analysis capabilities")
    
    def analyze_and_trade(self, symbol: str) -> Dict:
        """
        Main trading function - analyzes market and makes trading decisions
        
        Args:
            symbol: Trading symbol to analyze
            
        Returns:
            Dictionary with analysis results and trading decisions
        """
        logger.info(f"Starting comprehensive analysis for {symbol}")
        
        try:
            # Perform multi-timeframe analysis
            mtf_analysis = self.timeframe_analyzer.analyze_symbol(symbol)
            
            # Extract key levels from all timeframes
            key_levels = self._extract_key_levels(mtf_analysis)
            
            # Get lower timeframe data for detailed analysis
            ltf_data = self._get_primary_ltf_data(symbol, mtf_analysis)
            
            # Perform market structure analysis
            structure_analysis = self._perform_structure_analysis(ltf_data, key_levels)
            
            # Assess current market conditions
            market_assessment = self._assess_market_conditions(mtf_analysis, structure_analysis)
            
            # Generate trading signals
            trading_signals = self._generate_trading_signals(
                mtf_analysis, structure_analysis, market_assessment
            )
            
            # Apply adaptive logic and trap detection
            filtered_signals = self._apply_adaptive_filtering(trading_signals, market_assessment)
            
            # Risk management
            final_decisions = self._apply_risk_management(filtered_signals, symbol)
            
            # Update state
            self._update_bot_state(symbol, mtf_analysis, market_assessment)
            
            # Prepare comprehensive results
            results = {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'market_analysis': {
                    'multi_timeframe': mtf_analysis,
                    'market_structure': structure_analysis,
                    'market_assessment': market_assessment
                },
                'trading_signals': trading_signals,
                'filtered_signals': filtered_signals,
                'final_decisions': final_decisions,
                'bot_state': {
                    'current_positions': self.current_positions.get(symbol, {}),
                    'last_analysis': self.last_analysis_time.get(symbol),
                    'reassessment_count': self.reassessment_counter
                }
            }
            
            logger.info(f"Analysis completed for {symbol}. Found {len(final_decisions)} trading decisions.")
            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_and_trade for {symbol}: {str(e)}")
            return self._error_response(symbol, str(e))
    
    def _extract_key_levels(self, mtf_analysis: Dict) -> List[Dict]:
        """Extract key levels from multi-timeframe analysis"""
        key_levels = []
        
        # Get levels from each timeframe (prioritize higher timeframes)
        higher_tfs = self.config.timeframes.higher_timeframes
        lower_tfs = self.config.timeframes.lower_timeframes
        
        for tf in higher_tfs + lower_tfs:
            if tf in mtf_analysis['timeframe_analysis']:
                tf_data = mtf_analysis['timeframe_analysis'][tf]
                if 'key_levels' in tf_data:
                    # Add timeframe weight (higher TF = higher weight)
                    weight = 1.0 if tf in higher_tfs else 0.7
                    
                    for level_type in ['support', 'resistance']:
                        for level in tf_data['key_levels'].get(level_type, []):
                            key_levels.append({
                                'price': level['price'],
                                'type': level['type'],
                                'strength': level['strength'] * weight,
                                'timeframe': tf,
                                'source': level_type
                            })
        
        # Remove duplicates and sort by strength
        key_levels = self._consolidate_levels(key_levels)
        return sorted(key_levels, key=lambda x: x['strength'], reverse=True)[:20]  # Top 20 levels
    
    def _consolidate_levels(self, levels: List[Dict]) -> List[Dict]:
        """Consolidate nearby levels to avoid duplicates"""
        if not levels:
            return []
        
        consolidated = []
        tolerance = 0.001  # 0.1% tolerance for level consolidation
        
        for level in sorted(levels, key=lambda x: x['price']):
            merged = False
            
            for existing in consolidated:
                price_diff = abs(level['price'] - existing['price']) / existing['price']
                if price_diff <= tolerance:
                    # Merge levels - keep stronger one
                    if level['strength'] > existing['strength']:
                        existing.update(level)
                    merged = True
                    break
            
            if not merged:
                consolidated.append(level)
        
        return consolidated
    
    def _get_primary_ltf_data(self, symbol: str, mtf_analysis: Dict) -> pd.DataFrame:
        """Get primary lower timeframe data for detailed analysis"""
        primary_ltf = self.config.timeframes.lower_timeframes[0]  # Use first LTF as primary
        
        if primary_ltf in mtf_analysis['timeframe_analysis']:
            return mtf_analysis['timeframe_analysis'][primary_ltf]['data']
        else:
            # Fallback: fetch data directly
            return self.data_handler.fetch_data(symbol, primary_ltf, 500)
    
    def _perform_structure_analysis(self, data: pd.DataFrame, key_levels: List[Dict]) -> Dict:
        """Perform comprehensive market structure analysis"""
        if data.empty:
            return {'status': 'no_data'}
        
        # Analyze breaks and momentum
        analyzed_data = self.market_structure_analyzer.analyze_breaks_and_momentum(data, key_levels)
        
        # Get market structure summary
        structure_summary = self.market_structure_analyzer.get_market_structure_summary(analyzed_data)
        
        # Add additional analysis
        return {
            'data': analyzed_data,
            'summary': structure_summary,
            'key_observations': self._extract_key_observations(analyzed_data),
            'current_character': structure_summary.get('market_character', 'unknown')
        }
    
    def _extract_key_observations(self, data: pd.DataFrame) -> List[str]:
        """Extract key observations from analyzed data"""
        observations = []
        
        if data.empty:
            return observations
        
        recent_data = data.tail(20)
        
        # Check for recent traps
        if 'trap_detected' in recent_data.columns:
            recent_traps = recent_data[recent_data['trap_detected']]
            if not recent_traps.empty:
                trap_types = recent_traps['trap_type'].value_counts()
                for trap_type, count in trap_types.items():
                    observations.append(f"Recent {trap_type} detected ({count} occurrences)")
        
        # Check for momentum shifts
        if 'momentum_shift' in recent_data.columns:
            momentum_shifts = recent_data[recent_data['momentum_shift']]
            if not momentum_shifts.empty:
                latest_shift = momentum_shifts.iloc[-1]
                direction = latest_shift.get('momentum_direction', 'unknown')
                strength = latest_shift.get('momentum_strength', 0)
                observations.append(f"Momentum shift detected: {direction} (strength: {strength:.2f})")
        
        # Check for break patterns
        if 'break_type' in recent_data.columns:
            break_types = recent_data[recent_data['level_break']]['break_type'].value_counts()
            for break_type, count in break_types.items():
                observations.append(f"Recent {break_type}: {count} occurrences")
        
        return observations
    
    def _assess_market_conditions(self, mtf_analysis: Dict, structure_analysis: Dict) -> Dict:
        """Assess overall market conditions and trading environment"""
        assessment = {
            'overall_bias': mtf_analysis['context_analysis']['overall_bias'],
            'timeframe_alignment': mtf_analysis['context_analysis']['alignment'],
            'market_character': structure_analysis['current_character'],
            'reliability_score': structure_analysis['summary'].get('reliability_score', 0.5),
            'trap_risk': self._assess_trap_risk(structure_analysis),
            'momentum_clarity': self._assess_momentum_clarity(mtf_analysis),
            'trading_conditions': 'unknown'
        }
        
        # Determine trading conditions
        assessment['trading_conditions'] = self._determine_trading_conditions(assessment)
        
        return assessment
    
    def _assess_trap_risk(self, structure_analysis: Dict) -> float:
        """Assess current trap risk level"""
        summary = structure_analysis.get('summary', {})
        
        # High trap risk indicators
        risk_factors = 0
        
        # Too many recent false breaks
        false_breaks = summary.get('false_breaks', 0)
        total_breaks = summary.get('recent_breaks', 1)
        false_ratio = false_breaks / max(total_breaks, 1)
        if false_ratio > 0.6:
            risk_factors += 1
        
        # High sweep activity
        sweeps = summary.get('sweeps', 0)
        if sweeps > 2:
            risk_factors += 1
        
        # Choppy market character
        if summary.get('market_character') == 'choppy':
            risk_factors += 1
        
        # Manipulative character
        if summary.get('market_character') == 'manipulative':
            risk_factors += 2
        
        return min(risk_factors / 5.0, 1.0)  # Normalize to 0-1
    
    def _assess_momentum_clarity(self, mtf_analysis: Dict) -> float:
        """Assess clarity of momentum across timeframes"""
        alignment = mtf_analysis['context_analysis']['alignment']
        htf_context = mtf_analysis['context_analysis']['htf_context']
        
        # Clear momentum indicators
        clarity_score = 0.0
        
        # Timeframe alignment
        clarity_score += alignment.get('score', 0.5) * 0.4
        
        # HTF trend strength
        clarity_score += htf_context.get('trend_strength', 0.5) * 0.3
        
        # HTF consensus
        clarity_score += htf_context.get('consensus', 0.5) * 0.3
        
        return min(clarity_score, 1.0)
    
    def _determine_trading_conditions(self, assessment: Dict) -> str:
        """Determine overall trading conditions"""
        reliability = assessment['reliability_score']
        trap_risk = assessment['trap_risk']
        momentum_clarity = assessment['momentum_clarity']
        alignment_score = assessment['timeframe_alignment']['score']
        
        # Excellent conditions
        if (reliability > 0.7 and trap_risk < 0.3 and 
            momentum_clarity > 0.7 and alignment_score > 0.7):
            return 'excellent'
        
        # Good conditions
        elif (reliability > 0.6 and trap_risk < 0.4 and 
              momentum_clarity > 0.6 and alignment_score > 0.6):
            return 'good'
        
        # Fair conditions
        elif (reliability > 0.4 and trap_risk < 0.6 and 
              momentum_clarity > 0.4):
            return 'fair'
        
        # Poor conditions
        elif trap_risk > 0.7 or reliability < 0.3:
            return 'poor'
        
        # Average conditions
        else:
            return 'average'
    
    def _generate_trading_signals(self, mtf_analysis: Dict, structure_analysis: Dict,
                                market_assessment: Dict) -> List[Dict]:
        """Generate trading signals based on comprehensive analysis"""
        signals = []
        
        # Only generate signals if conditions are reasonable
        if market_assessment['trading_conditions'] in ['poor']:
            logger.warning("Poor trading conditions detected. Limiting signal generation.")
            return signals
        
        # Get opportunities from multi-timeframe analysis
        opportunities = mtf_analysis.get('opportunities', [])
        
        for opportunity in opportunities:
            signal = self._create_signal_from_opportunity(opportunity, market_assessment)
            if signal:
                signals.append(signal)
        
        # Look for additional patterns
        additional_signals = self._identify_additional_patterns(structure_analysis, market_assessment)
        signals.extend(additional_signals)
        
        return signals
    
    def _create_signal_from_opportunity(self, opportunity: Dict, market_assessment: Dict) -> Optional[Dict]:
        """Create trading signal from identified opportunity"""
        # Base signal structure
        signal = {
            'type': opportunity['type'],
            'direction': opportunity['direction'],
            'timeframe': opportunity['timeframe'],
            'setup': opportunity['setup'],
            'entry_price': opportunity['entry_price'],
            'quality_score': opportunity['quality_score'],
            'confidence': 0.0,
            'risk_level': 'medium'
        }
        
        # Adjust confidence based on market conditions
        base_confidence = opportunity['quality_score']
        
        # Market condition adjustments
        if market_assessment['trading_conditions'] == 'excellent':
            confidence_multiplier = 1.2
        elif market_assessment['trading_conditions'] == 'good':
            confidence_multiplier = 1.0
        elif market_assessment['trading_conditions'] == 'fair':
            confidence_multiplier = 0.8
        else:
            confidence_multiplier = 0.6
        
        # Alignment bonus
        alignment_score = market_assessment['timeframe_alignment']['score']
        alignment_bonus = alignment_score * 0.2
        
        # Trap risk penalty
        trap_penalty = market_assessment['trap_risk'] * 0.3
        
        final_confidence = base_confidence * confidence_multiplier + alignment_bonus - trap_penalty
        signal['confidence'] = max(min(final_confidence, 1.0), 0.0)
        
        # Determine risk level
        if market_assessment['trap_risk'] > 0.6:
            signal['risk_level'] = 'high'
        elif market_assessment['reliability_score'] > 0.7:
            signal['risk_level'] = 'low'
        
        # Only return signal if confidence is acceptable
        return signal if signal['confidence'] > 0.4 else None
    
    def _identify_additional_patterns(self, structure_analysis: Dict, market_assessment: Dict) -> List[Dict]:
        """Identify additional trading patterns"""
        additional_signals = []
        
        # Look for momentum continuation patterns
        if 'data' in structure_analysis:
            data = structure_analysis['data']
            
            # Momentum continuation after pullback
            momentum_signals = self._find_momentum_continuation(data, market_assessment)
            additional_signals.extend(momentum_signals)
            
            # Liquidity sweep reversal
            sweep_signals = self._find_sweep_reversals(data, market_assessment)
            additional_signals.extend(sweep_signals)
        
        return additional_signals
    
    def _find_momentum_continuation(self, data: pd.DataFrame, market_assessment: Dict) -> List[Dict]:
        """Find momentum continuation patterns"""
        signals = []
        
        if len(data) < 20:
            return signals
        
        recent_data = data.tail(10)
        overall_bias = market_assessment['overall_bias']
        
        # Look for momentum shifts aligned with bias
        if 'momentum_shift' in recent_data.columns:
            momentum_shifts = recent_data[recent_data['momentum_shift']]
            
            for idx in momentum_shifts.index:
                shift_data = momentum_shifts.loc[idx]
                direction = shift_data.get('momentum_direction', '')
                strength = shift_data.get('momentum_strength', 0)
                
                # Check alignment with overall bias
                if direction == overall_bias and strength > 0.6:
                    signals.append({
                        'type': 'momentum_continuation',
                        'direction': direction,
                        'timeframe': 'lower',
                        'setup': 'momentum_shift_continuation',
                        'entry_price': data.loc[idx, 'close'],
                        'quality_score': strength,
                        'confidence': strength * 0.8,
                        'risk_level': 'medium'
                    })
        
        return signals
    
    def _find_sweep_reversals(self, data: pd.DataFrame, market_assessment: Dict) -> List[Dict]:
        """Find liquidity sweep reversal opportunities"""
        signals = []
        
        if len(data) < 10:
            return signals
        
        recent_data = data.tail(5)
        
        # Look for recent sweeps that could reverse
        if 'break_type' in recent_data.columns:
            sweeps = recent_data[recent_data['break_type'] == 'sweep']
            
            for idx in sweeps.index:
                # Sweeps often provide good reversal opportunities
                sweep_price = data.loc[idx, 'close']
                
                # Determine reversal direction based on break direction
                # This would need more sophisticated logic in practice
                direction = 'bullish' if sweep_price < data['close'].iloc[-1] else 'bearish'
                
                signals.append({
                    'type': 'sweep_reversal',
                    'direction': direction,
                    'timeframe': 'lower',
                    'setup': 'liquidity_sweep_reversal',
                    'entry_price': sweep_price,
                    'quality_score': 0.7,
                    'confidence': 0.6,
                    'risk_level': 'medium'
                })
        
        return signals
    
    def _apply_adaptive_filtering(self, signals: List[Dict], market_assessment: Dict) -> List[Dict]:
        """Apply adaptive filtering to remove low-quality signals"""
        if not self.config.trap_detection_enabled:
            return signals
        
        filtered_signals = []
        
        for signal in signals:
            # Apply adaptive filters
            if self._passes_adaptive_filters(signal, market_assessment):
                filtered_signals.append(signal)
            else:
                logger.info(f"Signal filtered out: {signal['setup']} due to adaptive filtering")
        
        return filtered_signals
    
    def _passes_adaptive_filters(self, signal: Dict, market_assessment: Dict) -> bool:
        """Check if signal passes adaptive filters"""
        # Minimum confidence threshold (adaptive based on conditions)
        min_confidence = self._get_adaptive_confidence_threshold(market_assessment)
        if signal['confidence'] < min_confidence:
            return False
        
        # Trap risk filter
        if market_assessment['trap_risk'] > 0.7 and signal['risk_level'] == 'high':
            return False
        
        # Market character filter
        if (market_assessment['market_character'] == 'choppy' and 
            signal['type'] in ['breakout', 'momentum_continuation']):
            return False
        
        # Alignment filter for counter-trend signals
        alignment_direction = market_assessment['timeframe_alignment']['direction']
        if (alignment_direction != 'neutral' and 
            signal['direction'] != alignment_direction and 
            signal['confidence'] < 0.8):
            return False
        
        return True
    
    def _get_adaptive_confidence_threshold(self, market_assessment: Dict) -> float:
        """Get adaptive confidence threshold based on market conditions"""
        base_threshold = 0.5
        
        # Adjust based on trading conditions
        conditions = market_assessment['trading_conditions']
        if conditions == 'excellent':
            return base_threshold * 0.8
        elif conditions == 'good':
            return base_threshold * 0.9
        elif conditions == 'fair':
            return base_threshold
        elif conditions == 'average':
            return base_threshold * 1.1
        else:  # poor
            return base_threshold * 1.3
    
    def _apply_risk_management(self, signals: List[Dict], symbol: str) -> List[Dict]:
        """Apply risk management rules to finalize trading decisions"""
        final_decisions = []
        
        for signal in signals:
            # Calculate position size
            position_size = self._calculate_position_size(signal)
            
            # Set stop loss and take profit
            stop_loss, take_profit = self._calculate_stop_take_levels(signal)
            
            # Create final decision
            decision = {
                **signal,
                'symbol': symbol,
                'position_size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward_ratio': self._calculate_risk_reward(signal, stop_loss, take_profit),
                'max_risk': position_size * self.config.max_risk_per_trade,
                'decision_time': datetime.now()
            }
            
            # Final validation
            if self._validate_final_decision(decision):
                final_decisions.append(decision)
        
        return final_decisions
    
    def _calculate_position_size(self, signal: Dict) -> float:
        """Calculate appropriate position size"""
        base_size = 1.0  # Base position size
        
        # Adjust based on confidence
        confidence_multiplier = signal['confidence']
        
        # Adjust based on risk level
        if signal['risk_level'] == 'low':
            risk_multiplier = 1.2
        elif signal['risk_level'] == 'medium':
            risk_multiplier = 1.0
        else:  # high
            risk_multiplier = 0.7
        
        return base_size * confidence_multiplier * risk_multiplier
    
    def _calculate_stop_take_levels(self, signal: Dict) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        entry_price = signal['entry_price']
        
        # Basic stop loss calculation (could be enhanced with ATR, etc.)
        stop_distance = entry_price * 0.01  # 1% basic stop
        
        if signal['direction'] == 'bullish':
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + (stop_distance * 2)  # 2:1 RR
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - (stop_distance * 2)
        
        return stop_loss, take_profit
    
    def _calculate_risk_reward(self, signal: Dict, stop_loss: float, take_profit: float) -> float:
        """Calculate risk-reward ratio"""
        entry_price = signal['entry_price']
        
        if signal['direction'] == 'bullish':
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
        
        return reward / risk if risk > 0 else 0
    
    def _validate_final_decision(self, decision: Dict) -> bool:
        """Final validation of trading decision"""
        # Minimum risk-reward ratio
        if decision['risk_reward_ratio'] < 1.5:
            return False
        
        # Maximum risk per trade
        if decision['max_risk'] > self.config.max_risk_per_trade:
            return False
        
        # Confidence threshold
        if decision['confidence'] < 0.4:
            return False
        
        return True
    
    def _update_bot_state(self, symbol: str, mtf_analysis: Dict, market_assessment: Dict):
        """Update bot internal state"""
        self.last_analysis_time[symbol] = datetime.now()
        self.analysis_cache[symbol] = {
            'mtf_analysis': mtf_analysis,
            'market_assessment': market_assessment,
            'timestamp': datetime.now()
        }
        
        # Increment reassessment counter if conditions suggest reassessment
        if self._should_reassess(market_assessment):
            self.reassessment_counter += 1
            logger.info(f"Market reassessment triggered. Count: {self.reassessment_counter}")
    
    def _should_reassess(self, market_assessment: Dict) -> bool:
        """Determine if market conditions require reassessment"""
        # Reassess if trap risk is high
        if market_assessment['trap_risk'] > 0.7:
            return True
        
        # Reassess if trading conditions deteriorate
        if market_assessment['trading_conditions'] == 'poor':
            return True
        
        # Reassess based on interval
        if self.reassessment_counter % self.config.auto_reassessment_interval == 0:
            return True
        
        return False
    
    def _error_response(self, symbol: str, error_msg: str) -> Dict:
        """Generate error response"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'status': 'error',
            'error': error_msg,
            'market_analysis': {},
            'trading_signals': [],
            'filtered_signals': [],
            'final_decisions': []
        }
    
    def get_bot_status(self) -> Dict:
        """Get current bot status and performance metrics"""
        return {
            'config': {
                'timeframes': {
                    'higher': self.config.timeframes.higher_timeframes,
                    'lower': self.config.timeframes.lower_timeframes
                },
                'risk_settings': {
                    'max_risk_per_trade': self.config.max_risk_per_trade,
                    'max_daily_loss': self.config.max_daily_loss
                },
                'analysis_settings': {
                    'fractal_period': self.config.fractal_period,
                    'false_break_threshold': self.config.false_break_threshold,
                    'trap_detection_enabled': self.config.trap_detection_enabled
                }
            },
            'current_state': {
                'active_symbols': list(self.current_positions.keys()),
                'last_analysis_times': self.last_analysis_time,
                'reassessment_count': self.reassessment_counter,
                'cache_size': len(self.analysis_cache)
            },
            'capabilities': [
                'Multi-timeframe analysis',
                'Independent fractal identification',
                'Autonomous CHOCH detection',
                'Liquidity zone analysis',
                'False break detection',
                'Trap pattern recognition',
                'Adaptive filtering',
                'Risk management'
            ]
        }