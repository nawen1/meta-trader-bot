"""
Entry signal generator that respects multi-timeframe hierarchy.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from config import ENTRY_CONFIG
from timeframe_analyzer import TimeframeAnalyzer
from market_structure import MarketStructureAnalyzer
from liquidity_analyzer import LiquidityAnalyzer
from support_resistance import SupportResistanceAnalyzer


class EntrySignalGenerator:
    """
    Generates entry signals with strict adherence to higher timeframe context.
    All entries must be aligned with higher timeframe analysis.
    """
    
    def __init__(self):
        self.config = ENTRY_CONFIG
        self.tf_analyzer = TimeframeAnalyzer()
        self.structure_analyzer = MarketStructureAnalyzer()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.sr_analyzer = SupportResistanceAnalyzer()
    
    def generate_entry_signals(self, multi_tf_data: Dict[str, pd.DataFrame], 
                             entry_timeframe: str) -> Dict:
        """
        Generate entry signals for a specific timeframe with multi-TF context.
        
        Args:
            multi_tf_data: Dictionary with timeframe keys and OHLCV data values
            entry_timeframe: The timeframe to generate entry signals for
            
        Returns:
            Dictionary containing entry analysis and signals
        """
        # First, analyze timeframe hierarchy
        tf_analysis = self.tf_analyzer.analyze_timeframe_hierarchy(multi_tf_data)
        
        # Check if entry is allowed on this timeframe
        entry_allowed, reason = self.tf_analyzer.should_allow_entry(
            entry_timeframe, tf_analysis
        )
        
        if not entry_allowed:
            return {
                'entry_allowed': False,
                'reason': reason,
                'signals': [],
                'timeframe_analysis': tf_analysis
            }
        
        # Analyze higher timeframes for context
        higher_tf_context = self._analyze_higher_timeframes(
            multi_tf_data, entry_timeframe
        )
        
        # Analyze entry timeframe in detail
        entry_tf_analysis = self._analyze_entry_timeframe(
            multi_tf_data.get(entry_timeframe, pd.DataFrame()), entry_timeframe
        )
        
        # Generate potential entry signals
        potential_signals = self._generate_potential_signals(
            entry_tf_analysis, higher_tf_context
        )
        
        # Filter signals based on higher TF alignment
        valid_signals = self._filter_signals_by_tf_alignment(
            potential_signals, higher_tf_context, tf_analysis
        )
        
        # Add risk management to valid signals
        final_signals = self._add_risk_management(valid_signals, entry_tf_analysis)
        
        return {
            'entry_allowed': True,
            'reason': reason,
            'signals': final_signals,
            'timeframe_analysis': tf_analysis,
            'higher_tf_context': higher_tf_context,
            'entry_tf_analysis': entry_tf_analysis,
            'signal_count': len(final_signals)
        }
    
    def _analyze_higher_timeframes(self, multi_tf_data: Dict[str, pd.DataFrame], 
                                 entry_timeframe: str) -> Dict:
        """
        Analyze all higher timeframes to provide context.
        """
        higher_tfs = self.tf_analyzer.get_higher_timeframes(entry_timeframe)
        higher_tf_context = {}
        
        for tf in higher_tfs:
            if tf not in multi_tf_data or multi_tf_data[tf].empty:
                continue
            
            tf_data = multi_tf_data[tf]
            
            # Analyze market structure
            structure_analysis = self.structure_analyzer.analyze_market_structure(tf_data)
            
            # Analyze liquidity
            liquidity_analysis = self.liquidity_analyzer.analyze_liquidity(tf_data)
            
            # Analyze support/resistance
            sr_analysis = self.sr_analyzer.analyze_support_resistance(tf_data)
            
            higher_tf_context[tf] = {
                'structure': structure_analysis,
                'liquidity': liquidity_analysis,
                'support_resistance': sr_analysis,
                'priority': self.tf_analyzer.get_timeframe_priority(tf)
            }
        
        return higher_tf_context
    
    def _analyze_entry_timeframe(self, entry_data: pd.DataFrame, 
                               entry_timeframe: str) -> Dict:
        """
        Detailed analysis of the entry timeframe.
        """
        if entry_data.empty:
            return {'valid': False, 'reason': 'No data available'}
        
        # Analyze market structure
        structure_analysis = self.structure_analyzer.analyze_market_structure(entry_data)
        
        # Analyze liquidity
        liquidity_analysis = self.liquidity_analyzer.analyze_liquidity(entry_data)
        
        # Analyze support/resistance
        sr_analysis = self.sr_analyzer.analyze_support_resistance(entry_data)
        
        # Calculate additional entry-specific indicators
        entry_indicators = self._calculate_entry_indicators(entry_data)
        
        return {
            'valid': True,
            'timeframe': entry_timeframe,
            'structure': structure_analysis,
            'liquidity': liquidity_analysis,
            'support_resistance': sr_analysis,
            'indicators': entry_indicators,
            'current_price': entry_data['close'].iloc[-1] if not entry_data.empty else 0
        }
    
    def _calculate_entry_indicators(self, data: pd.DataFrame) -> Dict:
        """
        Calculate additional indicators for entry timing.
        """
        if len(data) < 20:
            return {'valid': False}
        
        # Simple momentum indicators
        close_prices = data['close']
        
        # Moving averages
        ma_fast = close_prices.rolling(window=9).mean()
        ma_slow = close_prices.rolling(window=21).mean()
        
        # Price position relative to MAs
        current_price = close_prices.iloc[-1]
        ma_fast_current = ma_fast.iloc[-1]
        ma_slow_current = ma_slow.iloc[-1]
        
        # Trend direction
        trend = 'bullish' if ma_fast_current > ma_slow_current else 'bearish'
        
        # Price momentum
        momentum = (current_price - close_prices.iloc[-5]) / close_prices.iloc[-5] * 100
        
        # Volatility (simple range-based)
        volatility = ((data['high'] - data['low']) / data['close']).tail(10).mean() * 100
        
        return {
            'valid': True,
            'trend': trend,
            'momentum': momentum,
            'volatility': volatility,
            'price_above_ma_fast': current_price > ma_fast_current,
            'price_above_ma_slow': current_price > ma_slow_current,
            'ma_alignment': trend
        }
    
    def _generate_potential_signals(self, entry_analysis: Dict, 
                                  higher_tf_context: Dict) -> List[Dict]:
        """
        Generate potential entry signals based on entry timeframe analysis.
        """
        potential_signals = []
        
        if not entry_analysis.get('valid'):
            return potential_signals
        
        current_price = entry_analysis['current_price']
        structure = entry_analysis['structure']
        liquidity = entry_analysis['liquidity']
        sr = entry_analysis['support_resistance']
        indicators = entry_analysis['indicators']
        
        # Signal 1: ChoCH confirmation entry
        self._check_choch_entry(potential_signals, structure, current_price, indicators)
        
        # Signal 2: Liquidity sweep reversal entry
        self._check_liquidity_sweep_entry(potential_signals, liquidity, current_price, indicators)
        
        # Signal 3: Support/Resistance bounce entry
        self._check_sr_bounce_entry(potential_signals, sr, current_price, indicators)
        
        # Signal 4: Break of Structure continuation entry
        self._check_bos_continuation_entry(potential_signals, structure, current_price, indicators)
        
        return potential_signals
    
    def _check_choch_entry(self, signals: List[Dict], structure: Dict, 
                          current_price: float, indicators: Dict):
        """Check for Change of Character entry opportunities."""
        choch_signals = structure.get('choch_signals', [])
        
        if not choch_signals:
            return
        
        # Get most recent ChoCH
        recent_choch = choch_signals[-1]
        
        # Only consider very recent ChoCH (within last few candles)
        if recent_choch.get('strength', 0) > 2.0:  # Significant ChoCH
            signal_type = 'long' if recent_choch['type'] == 'bullish_choch' else 'short'
            
            # Check if indicators align
            if self._indicators_align_with_signal(indicators, signal_type):
                signals.append({
                    'type': 'choch_entry',
                    'direction': signal_type,
                    'entry_price': current_price,
                    'trigger': recent_choch,
                    'strength': recent_choch.get('strength', 0),
                    'timeframe_context': 'entry_tf'
                })
    
    def _check_liquidity_sweep_entry(self, signals: List[Dict], liquidity: Dict, 
                                   current_price: float, indicators: Dict):
        """Check for liquidity sweep reversal entries."""
        liquidity_sweeps = liquidity.get('liquidity_sweeps', [])
        
        if not liquidity_sweeps:
            return
        
        # Get most recent sweep
        recent_sweep = liquidity_sweeps[-1]
        
        # Check if sweep suggests reversal opportunity
        if recent_sweep.get('reversal_strength', 0) > 1.0:
            signal_type = 'long' if recent_sweep['type'] == 'buy_side_sweep' else 'short'
            
            if self._indicators_align_with_signal(indicators, signal_type):
                signals.append({
                    'type': 'liquidity_sweep_reversal',
                    'direction': signal_type,
                    'entry_price': current_price,
                    'trigger': recent_sweep,
                    'strength': recent_sweep.get('reversal_strength', 0),
                    'timeframe_context': 'entry_tf'
                })
    
    def _check_sr_bounce_entry(self, signals: List[Dict], sr: Dict, 
                             current_price: float, indicators: Dict):
        """Check for support/resistance bounce entries."""
        nearest_support = sr.get('nearest_support')
        nearest_resistance = sr.get('nearest_resistance')
        
        # Check for support bounce (long signal)
        if nearest_support and abs(current_price - nearest_support['price']) / current_price < 0.005:
            if (nearest_support['strength'] > 50 and 
                self._indicators_align_with_signal(indicators, 'long')):
                signals.append({
                    'type': 'support_bounce',
                    'direction': 'long',
                    'entry_price': current_price,
                    'trigger': nearest_support,
                    'strength': nearest_support['strength'],
                    'timeframe_context': 'entry_tf'
                })
        
        # Check for resistance rejection (short signal)
        if nearest_resistance and abs(current_price - nearest_resistance['price']) / current_price < 0.005:
            if (nearest_resistance['strength'] > 50 and 
                self._indicators_align_with_signal(indicators, 'short')):
                signals.append({
                    'type': 'resistance_rejection',
                    'direction': 'short',
                    'entry_price': current_price,
                    'trigger': nearest_resistance,
                    'strength': nearest_resistance['strength'],
                    'timeframe_context': 'entry_tf'
                })
    
    def _check_bos_continuation_entry(self, signals: List[Dict], structure: Dict, 
                                    current_price: float, indicators: Dict):
        """Check for Break of Structure continuation entries."""
        bos_signals = structure.get('bos_signals', [])
        
        if not bos_signals:
            return
        
        # Get most recent BOS
        recent_bos = bos_signals[-1]
        signal_type = 'long' if recent_bos['type'] == 'bullish_bos' else 'short'
        
        if self._indicators_align_with_signal(indicators, signal_type):
            signals.append({
                'type': 'bos_continuation',
                'direction': signal_type,
                'entry_price': current_price,
                'trigger': recent_bos,
                'strength': 1.0,  # BOS is generally strong
                'timeframe_context': 'entry_tf'
            })
    
    def _indicators_align_with_signal(self, indicators: Dict, signal_type: str) -> bool:
        """Check if indicators align with the proposed signal direction."""
        if not indicators.get('valid'):
            return False
        
        trend = indicators.get('trend')
        momentum = indicators.get('momentum', 0)
        
        if signal_type == 'long':
            return (trend == 'bullish' and momentum > -1.0)  # Allow small negative momentum
        else:  # short
            return (trend == 'bearish' and momentum < 1.0)   # Allow small positive momentum
    
    def _filter_signals_by_tf_alignment(self, potential_signals: List[Dict], 
                                      higher_tf_context: Dict, 
                                      tf_analysis: Dict) -> List[Dict]:
        """
        Filter signals to ensure they align with higher timeframe context.
        """
        if not self.config['require_higher_tf_alignment']:
            return potential_signals
        
        valid_signals = []
        higher_tf_bias = tf_analysis.get('higher_tf_bias')
        
        for signal in potential_signals:
            signal_direction = signal['direction']
            
            # Check alignment with higher TF bias
            if higher_tf_bias:
                bias_aligned = (
                    (signal_direction == 'long' and higher_tf_bias == 'bullish') or
                    (signal_direction == 'short' and higher_tf_bias == 'bearish')
                )
                
                if not bias_aligned:
                    signal['rejection_reason'] = f"Signal direction ({signal_direction}) conflicts with higher TF bias ({higher_tf_bias})"
                    continue
            
            # Check alignment with higher TF structure
            alignment_score = self._calculate_tf_alignment_score(signal, higher_tf_context)
            
            if alignment_score >= 0.6:  # Require 60% alignment
                signal['tf_alignment_score'] = alignment_score
                valid_signals.append(signal)
            else:
                signal['rejection_reason'] = f"Low TF alignment score: {alignment_score:.2f}"
        
        return valid_signals
    
    def _calculate_tf_alignment_score(self, signal: Dict, 
                                    higher_tf_context: Dict) -> float:
        """
        Calculate how well the signal aligns with higher timeframe context.
        """
        if not higher_tf_context:
            return 0.5  # Neutral if no higher TF data
        
        signal_direction = signal['direction']
        alignment_factors = []
        
        for tf, context in higher_tf_context.items():
            # Check structure alignment
            structure_trend = context['structure'].get('current_trend')
            if structure_trend:
                structure_aligned = (
                    (signal_direction == 'long' and structure_trend == 'bullish') or
                    (signal_direction == 'short' and structure_trend == 'bearish')
                )
                alignment_factors.append(1.0 if structure_aligned else 0.0)
            
            # Check liquidity alignment
            liquidity_bias = context['liquidity'].get('liquidity_imbalance', {}).get('direction')
            if liquidity_bias:
                liquidity_aligned = (
                    (signal_direction == 'long' and liquidity_bias == 'bullish') or
                    (signal_direction == 'short' and liquidity_bias == 'bearish')
                )
                alignment_factors.append(1.0 if liquidity_aligned else 0.0)
        
        return sum(alignment_factors) / len(alignment_factors) if alignment_factors else 0.5
    
    def _add_risk_management(self, valid_signals: List[Dict], 
                           entry_analysis: Dict) -> List[Dict]:
        """
        Add risk management parameters to valid signals.
        """
        final_signals = []
        
        for signal in valid_signals:
            # Calculate stop loss and take profit
            stop_loss, take_profit = self._calculate_stop_take_profit(
                signal, entry_analysis
            )
            
            if stop_loss and take_profit:
                # Calculate risk/reward ratio
                entry_price = signal['entry_price']
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                risk_reward = reward / risk if risk > 0 else 0
                
                if risk_reward >= self.config['risk_reward_ratio']:
                    signal.update({
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward_ratio': risk_reward,
                        'risk_amount': risk,
                        'reward_amount': reward
                    })
                    final_signals.append(signal)
                else:
                    signal['rejection_reason'] = f"Poor risk/reward ratio: {risk_reward:.2f}"
        
        return final_signals
    
    def _calculate_stop_take_profit(self, signal: Dict, 
                                  entry_analysis: Dict) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate stop loss and take profit levels for a signal.
        """
        entry_price = signal['entry_price']
        direction = signal['direction']
        sr = entry_analysis['support_resistance']
        
        stop_loss = None
        take_profit = None
        
        if direction == 'long':
            # Stop loss below nearest support or recent low
            nearest_support = sr.get('nearest_support')
            if nearest_support:
                stop_loss = nearest_support['price'] * 0.999  # Slightly below support
            else:
                stop_loss = entry_price * 0.99  # 1% stop loss
            
            # Take profit at nearest resistance
            nearest_resistance = sr.get('nearest_resistance')
            if nearest_resistance:
                take_profit = nearest_resistance['price'] * 0.999  # Slightly below resistance
            else:
                risk = entry_price - stop_loss
                take_profit = entry_price + (risk * self.config['risk_reward_ratio'])
        
        else:  # short
            # Stop loss above nearest resistance or recent high
            nearest_resistance = sr.get('nearest_resistance')
            if nearest_resistance:
                stop_loss = nearest_resistance['price'] * 1.001  # Slightly above resistance
            else:
                stop_loss = entry_price * 1.01  # 1% stop loss
            
            # Take profit at nearest support
            nearest_support = sr.get('nearest_support')
            if nearest_support:
                take_profit = nearest_support['price'] * 1.001  # Slightly above support
            else:
                risk = stop_loss - entry_price
                take_profit = entry_price - (risk * self.config['risk_reward_ratio'])
        
        return stop_loss, take_profit