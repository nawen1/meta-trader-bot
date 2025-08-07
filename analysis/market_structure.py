"""
Market Structure Analysis
Differentiates between false breaks and legitimate momentum shifts
Considers liquidity sweeps, retests, and trap detection
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MarketStructureAnalyzer:
    """
    Analyzes market structure to identify legitimate moves vs false breaks
    Integrates liquidity sweep detection and trap identification
    """
    
    def __init__(self, false_break_threshold: float = 0.002, momentum_confirmation_period: int = 5):
        """
        Initialize market structure analyzer
        
        Args:
            false_break_threshold: Threshold for identifying false breaks (as percentage)
            momentum_confirmation_period: Candles needed to confirm momentum
        """
        self.false_break_threshold = false_break_threshold
        self.momentum_confirmation_period = momentum_confirmation_period
        self.trap_patterns = []
    
    def analyze_breaks_and_momentum(self, data: pd.DataFrame, key_levels: List[Dict]) -> pd.DataFrame:
        """
        Analyze breaks and determine if they are legitimate or false
        
        Args:
            data: OHLCV DataFrame with technical analysis
            key_levels: List of key support/resistance levels
            
        Returns:
            DataFrame with break analysis
        """
        data = data.copy()
        
        # Initialize columns
        data['level_break'] = False
        data['break_type'] = ''  # 'false_break', 'legitimate_break', 'sweep'
        data['break_strength'] = 0.0
        data['momentum_confirmed'] = False
        data['trap_detected'] = False
        
        # Analyze each potential break
        for level in key_levels:
            breaks = self._detect_level_breaks(data, level)
            for break_info in breaks:
                self._analyze_break_legitimacy(data, break_info, level)
        
        # Detect trap patterns
        data = self._detect_trap_patterns(data)
        
        # Analyze momentum shifts
        data = self._analyze_momentum_shifts(data)
        
        return data
    
    def _detect_level_breaks(self, data: pd.DataFrame, level: Dict) -> List[Dict]:
        """Detect when price breaks a key level"""
        breaks = []
        level_price = level['price']
        level_type = level.get('type', 'unknown')
        
        for i, idx in enumerate(data.index):
            if i < 1:  # Need previous candle for comparison
                continue
            
            current = data.loc[idx]
            previous = data.iloc[i-1]
            
            # Check for break above resistance
            if level_type in ['resistance', 'supply', 'fractal_high', 'session_high']:
                if (previous['high'] <= level_price and current['high'] > level_price) or \
                   (previous['close'] <= level_price and current['close'] > level_price):
                    breaks.append({
                        'index': idx,
                        'direction': 'bullish',
                        'break_price': current['high'],
                        'level_price': level_price,
                        'break_size': (current['high'] - level_price) / level_price,
                        'close_above': current['close'] > level_price
                    })
            
            # Check for break below support
            elif level_type in ['support', 'demand', 'fractal_low', 'session_low']:
                if (previous['low'] >= level_price and current['low'] < level_price) or \
                   (previous['close'] >= level_price and current['close'] < level_price):
                    breaks.append({
                        'index': idx,
                        'direction': 'bearish',
                        'break_price': current['low'],
                        'level_price': level_price,
                        'break_size': (level_price - current['low']) / level_price,
                        'close_below': current['close'] < level_price
                    })
        
        return breaks
    
    def _analyze_break_legitimacy(self, data: pd.DataFrame, break_info: Dict, level: Dict):
        """Analyze if a break is legitimate or false"""
        break_idx = break_info['index']
        direction = break_info['direction']
        
        # Get data after the break for confirmation analysis
        break_position = data.index.get_loc(break_idx)
        end_position = min(break_position + self.momentum_confirmation_period + 1, len(data))
        confirmation_data = data.iloc[break_position:end_position]
        
        # Initial break classification
        is_legitimate = self._classify_break_initial(break_info, confirmation_data)
        
        # Volume confirmation
        volume_confirmation = self._check_volume_confirmation(data, break_idx)
        
        # Momentum confirmation
        momentum_confirmation = self._check_momentum_confirmation(confirmation_data, direction)
        
        # Retest behavior
        retest_behavior = self._analyze_retest_behavior(confirmation_data, break_info)
        
        # Liquidity sweep detection
        is_sweep = self._detect_liquidity_sweep(data, break_info, level)
        
        # Final classification
        final_classification = self._final_break_classification(
            is_legitimate, volume_confirmation, momentum_confirmation, 
            retest_behavior, is_sweep
        )
        
        # Update data
        data.loc[break_idx, 'level_break'] = True
        data.loc[break_idx, 'break_type'] = final_classification['type']
        data.loc[break_idx, 'break_strength'] = final_classification['strength']
        
        # Mark momentum confirmation in subsequent candles
        if final_classification['type'] == 'legitimate_break':
            for i in range(1, min(self.momentum_confirmation_period + 1, len(confirmation_data))):
                if break_position + i < len(data):
                    data.iloc[break_position + i]['momentum_confirmed'] = True
    
    def _classify_break_initial(self, break_info: Dict, confirmation_data: pd.DataFrame) -> bool:
        """Initial classification based on break characteristics"""
        # Strong breaks are more likely to be legitimate
        break_size = break_info['break_size']
        
        # Check if close is in direction of break
        if break_info['direction'] == 'bullish':
            close_confirmation = break_info.get('close_above', False)
        else:
            close_confirmation = break_info.get('close_below', False)
        
        # Large breaks with close confirmation are more likely legitimate
        size_threshold = self.false_break_threshold * 2  # 2x the false break threshold
        
        return break_size > size_threshold and close_confirmation
    
    def _check_volume_confirmation(self, data: pd.DataFrame, break_idx: int) -> float:
        """Check for volume confirmation of the break"""
        if 'volume' not in data.columns or data['volume'].sum() == 0:
            return 0.5  # Neutral if no volume data
        
        break_position = data.index.get_loc(break_idx)
        
        # Compare break volume to recent average
        lookback = min(20, break_position)
        if lookback > 0:
            recent_avg_volume = data['volume'].iloc[break_position-lookback:break_position].mean()
            break_volume = data.loc[break_idx, 'volume']
            
            if recent_avg_volume > 0:
                volume_ratio = break_volume / recent_avg_volume
                # Strong volume (>1.5x avg) suggests legitimate break
                return min(volume_ratio / 1.5, 1.0)
        
        return 0.5
    
    def _check_momentum_confirmation(self, confirmation_data: pd.DataFrame, direction: str) -> float:
        """Check for momentum confirmation after the break"""
        if len(confirmation_data) < 2:
            return 0.0
        
        # Calculate price momentum in the break direction
        start_price = confirmation_data['close'].iloc[0]
        end_price = confirmation_data['close'].iloc[-1]
        
        momentum = (end_price - start_price) / start_price
        
        if direction == 'bullish':
            # Positive momentum confirms bullish break
            return min(max(momentum * 50, 0), 1.0)  # Scale momentum to 0-1
        else:
            # Negative momentum confirms bearish break
            return min(max(-momentum * 50, 0), 1.0)
    
    def _analyze_retest_behavior(self, confirmation_data: pd.DataFrame, break_info: Dict) -> Dict:
        """Analyze how price behaves on retest of broken level"""
        level_price = break_info['level_price']
        direction = break_info['direction']
        
        retest_info = {
            'occurred': False,
            'held': False,
            'strength': 0.0
        }
        
        # Look for retest in confirmation period
        for idx in confirmation_data.index:
            candle = confirmation_data.loc[idx]
            
            # Check if price retested the level
            if direction == 'bullish':
                # For bullish break, look for retest from above
                if candle['low'] <= level_price <= candle['high']:
                    retest_info['occurred'] = True
                    # Check if retest held (price bounced)
                    if candle['close'] > level_price:
                        retest_info['held'] = True
                        retest_info['strength'] = 0.8
                    else:
                        retest_info['held'] = False
                        retest_info['strength'] = 0.2
                    break
            else:
                # For bearish break, look for retest from below
                if candle['low'] <= level_price <= candle['high']:
                    retest_info['occurred'] = True
                    # Check if retest held (price rejected)
                    if candle['close'] < level_price:
                        retest_info['held'] = True
                        retest_info['strength'] = 0.8
                    else:
                        retest_info['held'] = False
                        retest_info['strength'] = 0.2
                    break
        
        return retest_info
    
    def _detect_liquidity_sweep(self, data: pd.DataFrame, break_info: Dict, level: Dict) -> bool:
        """Detect if break is actually a liquidity sweep"""
        break_idx = break_info['index']
        break_position = data.index.get_loc(break_idx)
        direction = break_info['direction']
        level_price = break_info['level_price']
        
        # Look for quick reversal after break (sweep characteristic)
        lookforward = min(5, len(data) - break_position - 1)
        
        for i in range(1, lookforward + 1):
            if break_position + i >= len(data):
                break
            
            future_candle = data.iloc[break_position + i]
            
            if direction == 'bullish':
                # After bullish break, look for quick move back below level
                if future_candle['close'] < level_price:
                    return True
            else:
                # After bearish break, look for quick move back above level
                if future_candle['close'] > level_price:
                    return True
        
        return False
    
    def _final_break_classification(self, initial_legitimate: bool, volume_conf: float,
                                   momentum_conf: float, retest_info: Dict, is_sweep: bool) -> Dict:
        """Final classification of the break"""
        
        if is_sweep:
            return {'type': 'sweep', 'strength': 0.9}
        
        # Calculate composite score
        score = 0.0
        
        # Initial classification (30% weight)
        if initial_legitimate:
            score += 0.3
        
        # Volume confirmation (25% weight)
        score += volume_conf * 0.25
        
        # Momentum confirmation (25% weight)
        score += momentum_conf * 0.25
        
        # Retest behavior (20% weight)
        if retest_info['occurred']:
            if retest_info['held']:
                score += 0.2
            else:
                score -= 0.1  # Failed retest is negative
        else:
            score += 0.1  # No retest yet, slightly positive
        
        # Classify based on score
        if score >= 0.7:
            return {'type': 'legitimate_break', 'strength': score}
        elif score <= 0.3:
            return {'type': 'false_break', 'strength': 1.0 - score}
        else:
            return {'type': 'uncertain_break', 'strength': 0.5}
    
    def _detect_trap_patterns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect common trap patterns in the market"""
        data['trap_detected'] = False
        data['trap_type'] = ''
        
        # Bull trap detection
        bull_traps = self._detect_bull_traps(data)
        for trap in bull_traps:
            data.loc[trap['index'], 'trap_detected'] = True
            data.loc[trap['index'], 'trap_type'] = 'bull_trap'
        
        # Bear trap detection
        bear_traps = self._detect_bear_traps(data)
        for trap in bear_traps:
            data.loc[trap['index'], 'trap_detected'] = True
            data.loc[trap['index'], 'trap_type'] = 'bear_trap'
        
        # Liquidity trap detection
        liquidity_traps = self._detect_liquidity_traps(data)
        for trap in liquidity_traps:
            data.loc[trap['index'], 'trap_detected'] = True
            data.loc[trap['index'], 'trap_type'] = 'liquidity_trap'
        
        return data
    
    def _detect_bull_traps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect bull trap patterns"""
        traps = []
        
        for i in range(10, len(data) - 5):  # Need some history and future data
            current_idx = data.index[i]
            
            # Look for pattern: break above resistance followed by quick reversal
            if data.loc[current_idx, 'level_break'] and data.loc[current_idx, 'break_type'] == 'false_break':
                # Check if it was a bullish break that failed
                lookback_data = data.iloc[i-10:i]
                lookforward_data = data.iloc[i:i+5]
                
                # Bull trap characteristics:
                # 1. Break above recent high
                # 2. Quick reversal below break level
                # 3. Often on lower volume
                
                if self._is_bull_trap_pattern(lookback_data, lookforward_data, data.iloc[i]):
                    traps.append({
                        'index': current_idx,
                        'type': 'bull_trap',
                        'strength': 0.8
                    })
        
        return traps
    
    def _detect_bear_traps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect bear trap patterns"""
        traps = []
        
        for i in range(10, len(data) - 5):
            current_idx = data.index[i]
            
            # Look for pattern: break below support followed by quick reversal
            if data.loc[current_idx, 'level_break'] and data.loc[current_idx, 'break_type'] == 'false_break':
                lookback_data = data.iloc[i-10:i]
                lookforward_data = data.iloc[i:i+5]
                
                if self._is_bear_trap_pattern(lookback_data, lookforward_data, data.iloc[i]):
                    traps.append({
                        'index': current_idx,
                        'type': 'bear_trap',
                        'strength': 0.8
                    })
        
        return traps
    
    def _detect_liquidity_traps(self, data: pd.DataFrame) -> List[Dict]:
        """Detect liquidity trap patterns"""
        traps = []
        
        # Look for sweep patterns
        for i in range(5, len(data)):
            current_idx = data.index[i]
            
            if data.loc[current_idx, 'break_type'] == 'sweep':
                traps.append({
                    'index': current_idx,
                    'type': 'liquidity_trap',
                    'strength': 0.9
                })
        
        return traps
    
    def _is_bull_trap_pattern(self, lookback: pd.DataFrame, lookforward: pd.DataFrame, 
                             current: pd.Series) -> bool:
        """Check if pattern matches bull trap characteristics"""
        if len(lookback) < 5 or len(lookforward) < 3:
            return False
        
        # Check for recent high that was broken
        recent_high = lookback['high'].max()
        break_price = current['high']
        
        # Must break above recent high
        if break_price <= recent_high:
            return False
        
        # Check for quick reversal
        reversal_occurred = False
        for idx in lookforward.index:
            if lookforward.loc[idx, 'close'] < recent_high:
                reversal_occurred = True
                break
        
        return reversal_occurred
    
    def _is_bear_trap_pattern(self, lookback: pd.DataFrame, lookforward: pd.DataFrame,
                             current: pd.Series) -> bool:
        """Check if pattern matches bear trap characteristics"""
        if len(lookback) < 5 or len(lookforward) < 3:
            return False
        
        # Check for recent low that was broken
        recent_low = lookback['low'].min()
        break_price = current['low']
        
        # Must break below recent low
        if break_price >= recent_low:
            return False
        
        # Check for quick reversal
        reversal_occurred = False
        for idx in lookforward.index:
            if lookforward.loc[idx, 'close'] > recent_low:
                reversal_occurred = True
                break
        
        return reversal_occurred
    
    def _analyze_momentum_shifts(self, data: pd.DataFrame) -> pd.DataFrame:
        """Analyze legitimate momentum shifts vs temporary moves"""
        data['momentum_shift'] = False
        data['momentum_strength'] = 0.0
        data['momentum_direction'] = ''
        
        # Use multiple momentum indicators
        if len(data) < 20:
            return data
        
        # Calculate momentum indicators
        data = self._calculate_momentum_indicators(data)
        
        # Detect momentum shifts
        for i in range(10, len(data)):
            momentum_analysis = self._analyze_momentum_at_point(data, i)
            
            idx = data.index[i]
            data.loc[idx, 'momentum_shift'] = momentum_analysis['shift_detected']
            data.loc[idx, 'momentum_strength'] = momentum_analysis['strength']
            data.loc[idx, 'momentum_direction'] = momentum_analysis['direction']
        
        return data
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate various momentum indicators"""
        # Rate of Change
        data['roc_5'] = data['close'].pct_change(5) * 100
        data['roc_10'] = data['close'].pct_change(10) * 100
        
        # Momentum oscillator
        data['momentum_10'] = (data['close'] / data['close'].shift(10)) * 100
        
        # Price velocity (rate of price change acceleration)
        data['price_velocity'] = data['close'].diff().rolling(window=5).mean()
        
        return data
    
    def _analyze_momentum_at_point(self, data: pd.DataFrame, position: int) -> Dict:
        """Analyze momentum at a specific point"""
        current_data = data.iloc[position]
        
        # Get recent momentum values
        roc_5 = current_data.get('roc_5', 0)
        roc_10 = current_data.get('roc_10', 0)
        momentum_10 = current_data.get('momentum_10', 100)
        velocity = current_data.get('price_velocity', 0)
        
        # Analyze momentum alignment
        bullish_signals = 0
        bearish_signals = 0
        
        if roc_5 > 2:  # Strong 5-period momentum
            bullish_signals += 1
        elif roc_5 < -2:
            bearish_signals += 1
        
        if roc_10 > 5:  # Strong 10-period momentum
            bullish_signals += 1
        elif roc_10 < -5:
            bearish_signals += 1
        
        if momentum_10 > 105:  # Above baseline
            bullish_signals += 1
        elif momentum_10 < 95:
            bearish_signals += 1
        
        if velocity > 0:  # Positive velocity
            bullish_signals += 1
        elif velocity < 0:
            bearish_signals += 1
        
        # Determine momentum shift
        total_signals = bullish_signals + bearish_signals
        if total_signals == 0:
            return {'shift_detected': False, 'strength': 0.0, 'direction': 'neutral'}
        
        if bullish_signals > bearish_signals:
            strength = bullish_signals / 4.0  # Normalize to 0-1
            direction = 'bullish'
        elif bearish_signals > bullish_signals:
            strength = bearish_signals / 4.0
            direction = 'bearish'
        else:
            strength = 0.5
            direction = 'neutral'
        
        shift_detected = strength >= 0.6  # Require strong alignment
        
        return {
            'shift_detected': shift_detected,
            'strength': strength,
            'direction': direction
        }
    
    def get_market_structure_summary(self, data: pd.DataFrame) -> Dict:
        """Get summary of current market structure analysis"""
        if data.empty:
            return {'status': 'no_data'}
        
        recent_data = data.tail(50)
        
        # Count recent events
        recent_breaks = len(recent_data[recent_data['level_break']])
        false_breaks = len(recent_data[recent_data['break_type'] == 'false_break'])
        legitimate_breaks = len(recent_data[recent_data['break_type'] == 'legitimate_break'])
        sweeps = len(recent_data[recent_data['break_type'] == 'sweep'])
        traps = len(recent_data[recent_data['trap_detected']])
        
        # Current momentum
        current_momentum = recent_data['momentum_direction'].iloc[-1] if 'momentum_direction' in recent_data.columns else 'neutral'
        momentum_strength = recent_data['momentum_strength'].iloc[-1] if 'momentum_strength' in recent_data.columns else 0.0
        
        # Market character assessment
        if false_breaks > legitimate_breaks:
            market_character = 'choppy'
        elif sweeps > 2:
            market_character = 'manipulative'
        elif legitimate_breaks > false_breaks:
            market_character = 'trending'
        else:
            market_character = 'balanced'
        
        return {
            'status': 'analyzed',
            'market_character': market_character,
            'recent_breaks': recent_breaks,
            'false_breaks': false_breaks,
            'legitimate_breaks': legitimate_breaks,
            'sweeps': sweeps,
            'traps': traps,
            'current_momentum': current_momentum,
            'momentum_strength': momentum_strength,
            'reliability_score': legitimate_breaks / max(recent_breaks, 1)
        }