"""
Support and resistance level analyzer.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from config import SUPPORT_RESISTANCE_CONFIG


class SupportResistanceAnalyzer:
    """
    Analyzes and identifies support and resistance levels in price data.
    """
    
    def __init__(self):
        self.config = SUPPORT_RESISTANCE_CONFIG
        self.touch_tolerance = self.config['touch_tolerance']
        self.min_touches = self.config['min_touches']
        self.lookback_periods = self.config['lookback_periods']
    
    def analyze_support_resistance(self, data: pd.DataFrame) -> Dict:
        """
        Comprehensive support and resistance analysis.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary containing S/R analysis
        """
        if data.empty or len(data) < self.lookback_periods:
            return self._empty_sr_analysis()
        
        # Identify potential levels
        potential_levels = self._identify_potential_levels(data)
        
        # Validate levels based on touches
        validated_levels = self._validate_levels(data, potential_levels)
        
        # Classify levels as support or resistance
        classified_levels = self._classify_levels(data, validated_levels)
        
        # Assess level strength
        level_strengths = self._assess_level_strengths(data, classified_levels)
        
        # Identify key levels (most significant)
        key_levels = self._identify_key_levels(level_strengths)
        
        # Find nearest levels to current price
        current_price = data['close'].iloc[-1]
        nearest_levels = self._find_nearest_levels(level_strengths, current_price)
        
        return {
            'support_levels': [l for l in level_strengths if l['type'] == 'support'],
            'resistance_levels': [l for l in level_strengths if l['type'] == 'resistance'],
            'key_levels': key_levels,
            'nearest_support': nearest_levels.get('support'),
            'nearest_resistance': nearest_levels.get('resistance'),
            'level_confluence': self._find_level_confluence(level_strengths),
            'broken_levels': self._identify_broken_levels(data, level_strengths),
            'current_price': current_price
        }
    
    def _identify_potential_levels(self, data: pd.DataFrame) -> List[float]:
        """
        Identify potential support/resistance levels using various methods.
        """
        potential_levels = set()
        
        # Method 1: Significant highs and lows
        highs = data['high'].values
        lows = data['low'].values
        
        # Find local maxima and minima
        for i in range(5, len(data) - 5):
            # Local high
            if (highs[i] > max(highs[i-5:i]) and 
                highs[i] > max(highs[i+1:i+6])):
                potential_levels.add(highs[i])
            
            # Local low
            if (lows[i] < min(lows[i-5:i]) and 
                lows[i] < min(lows[i+1:i+6])):
                potential_levels.add(lows[i])
        
        # Method 2: Round numbers (psychological levels)
        price_range = data['high'].max() - data['low'].min()
        step = self._get_round_number_step(price_range)
        
        min_price = data['low'].min()
        max_price = data['high'].max()
        
        # Add round numbers within price range
        current_level = (min_price // step) * step
        while current_level <= max_price:
            if min_price <= current_level <= max_price:
                potential_levels.add(current_level)
            current_level += step
        
        # Method 3: Previous close levels (often act as S/R)
        closes = data['close'].values
        for close in closes[-self.lookback_periods:]:
            potential_levels.add(close)
        
        return list(potential_levels)
    
    def _get_round_number_step(self, price_range: float) -> float:
        """
        Determine appropriate step size for round numbers based on price range.
        """
        if price_range < 1:
            return 0.01  # Penny increments
        elif price_range < 10:
            return 0.1   # Dime increments
        elif price_range < 100:
            return 1.0   # Dollar increments
        elif price_range < 1000:
            return 10.0  # Ten dollar increments
        else:
            return 100.0 # Hundred dollar increments
    
    def _validate_levels(self, data: pd.DataFrame, potential_levels: List[float]) -> List[Dict]:
        """
        Validate potential levels by counting touches.
        """
        validated_levels = []
        
        for level in potential_levels:
            touches = self._count_level_touches(data, level)
            
            if touches >= self.min_touches:
                validated_levels.append({
                    'price': level,
                    'touches': touches,
                    'touch_indices': self._get_touch_indices(data, level)
                })
        
        return validated_levels
    
    def _count_level_touches(self, data: pd.DataFrame, level: float) -> int:
        """
        Count how many times price touched a specific level.
        """
        touches = 0
        tolerance = level * self.touch_tolerance
        
        for _, candle in data.iterrows():
            # Check if high touched the level
            if abs(candle['high'] - level) <= tolerance:
                touches += 1
                continue
            
            # Check if low touched the level
            if abs(candle['low'] - level) <= tolerance:
                touches += 1
                continue
            
            # Check if candle crossed through the level
            if candle['low'] <= level <= candle['high']:
                touches += 1
        
        return touches
    
    def _get_touch_indices(self, data: pd.DataFrame, level: float) -> List[int]:
        """
        Get indices where price touched the level.
        """
        touch_indices = []
        tolerance = level * self.touch_tolerance
        
        for i, (_, candle) in enumerate(data.iterrows()):
            touched = False
            
            # Check if high touched the level
            if abs(candle['high'] - level) <= tolerance:
                touched = True
            
            # Check if low touched the level
            elif abs(candle['low'] - level) <= tolerance:
                touched = True
            
            # Check if candle crossed through the level
            elif candle['low'] <= level <= candle['high']:
                touched = True
            
            if touched:
                touch_indices.append(i)
        
        return touch_indices
    
    def _classify_levels(self, data: pd.DataFrame, validated_levels: List[Dict]) -> List[Dict]:
        """
        Classify levels as support or resistance based on price behavior.
        """
        classified_levels = []
        
        for level_data in validated_levels:
            level = level_data['price']
            touch_indices = level_data['touch_indices']
            
            # Analyze price behavior around touches
            bounce_count = 0
            break_count = 0
            
            for touch_idx in touch_indices:
                if touch_idx + 5 < len(data):  # Need future data to analyze bounce/break
                    behavior = self._analyze_touch_behavior(data, touch_idx, level)
                    if behavior == 'bounce':
                        bounce_count += 1
                    elif behavior == 'break':
                        break_count += 1
            
            # Classify based on behavior
            if bounce_count > break_count:
                # More bounces suggest support/resistance
                current_price = data['close'].iloc[-1]
                level_type = 'support' if current_price > level else 'resistance'
            else:
                # More breaks suggest the level is weak or broken
                current_price = data['close'].iloc[-1]
                level_type = 'resistance' if current_price > level else 'support'
            
            classified_levels.append({
                'price': level,
                'type': level_type,
                'touches': level_data['touches'],
                'touch_indices': touch_indices,
                'bounce_count': bounce_count,
                'break_count': break_count
            })
        
        return classified_levels
    
    def _analyze_touch_behavior(self, data: pd.DataFrame, touch_idx: int, level: float) -> str:
        """
        Analyze what happened after price touched a level.
        """
        if touch_idx + 5 >= len(data):
            return 'insufficient_data'
        
        touch_candle = data.iloc[touch_idx]
        
        # Look at next 5 candles
        future_candles = data.iloc[touch_idx+1:touch_idx+6]
        
        # Determine if it bounced or broke through
        tolerance = level * self.touch_tolerance * 2  # Wider tolerance for break/bounce
        
        # Check for bounce (price moved away from level)
        if touch_candle['low'] <= level <= touch_candle['high']:
            # Price was at level, check direction after
            future_closes = future_candles['close'].values
            
            if level > touch_candle['close']:  # Level is above, expect bounce down
                if any(close < level - tolerance for close in future_closes):
                    return 'bounce'
            else:  # Level is below, expect bounce up
                if any(close > level + tolerance for close in future_closes):
                    return 'bounce'
        
        # Check for break (price continued through level)
        future_highs = future_candles['high'].values
        future_lows = future_candles['low'].values
        
        if any(high > level + tolerance for high in future_highs) or \
           any(low < level - tolerance for low in future_lows):
            return 'break'
        
        return 'neutral'
    
    def _assess_level_strengths(self, data: pd.DataFrame, classified_levels: List[Dict]) -> List[Dict]:
        """
        Assess the strength of each level based on multiple factors.
        """
        strengthened_levels = []
        
        for level_data in classified_levels:
            strength_factors = {
                'touch_count': level_data['touches'],
                'bounce_ratio': level_data['bounce_count'] / max(level_data['touches'], 1),
                'age': self._calculate_level_age(data, level_data['touch_indices']),
                'volume_confirmation': self._check_volume_confirmation(data, level_data),
                'confluence': 0  # Will be calculated separately
            }
            
            # Calculate overall strength (0-100)
            strength = self._calculate_strength_score(strength_factors)
            
            strengthened_levels.append({
                **level_data,
                'strength': strength,
                'strength_factors': strength_factors
            })
        
        return strengthened_levels
    
    def _calculate_level_age(self, data: pd.DataFrame, touch_indices: List[int]) -> float:
        """
        Calculate how old the level is (older levels may be stronger).
        """
        if not touch_indices:
            return 0.0
        
        first_touch = min(touch_indices)
        last_touch = max(touch_indices)
        total_periods = len(data) - 1
        
        # Age as percentage of total data range
        age = (total_periods - first_touch) / total_periods
        # Persistence as how long it remained relevant
        persistence = (last_touch - first_touch) / total_periods
        
        return (age + persistence) / 2
    
    def _check_volume_confirmation(self, data: pd.DataFrame, level_data: Dict) -> float:
        """
        Check if volume confirmed the level (higher volume at touches).
        """
        if 'volume' not in data.columns:
            return 0.5  # Neutral if no volume data
        
        touch_indices = level_data['touch_indices']
        if not touch_indices:
            return 0.0
        
        # Get average volume at touches
        touch_volumes = [data['volume'].iloc[idx] for idx in touch_indices if idx < len(data)]
        avg_touch_volume = np.mean(touch_volumes) if touch_volumes else 0
        
        # Get average volume overall
        avg_volume = data['volume'].mean()
        
        if avg_volume > 0:
            volume_ratio = avg_touch_volume / avg_volume
            return min(volume_ratio, 2.0) / 2.0  # Normalize to 0-1
        
        return 0.5
    
    def _calculate_strength_score(self, strength_factors: Dict) -> float:
        """
        Calculate overall strength score from individual factors.
        """
        # Weighted scoring
        weights = {
            'touch_count': 0.3,
            'bounce_ratio': 0.25,
            'age': 0.2,
            'volume_confirmation': 0.15,
            'confluence': 0.1
        }
        
        # Normalize factors to 0-1 scale
        normalized_factors = {
            'touch_count': min(strength_factors['touch_count'] / 10, 1.0),
            'bounce_ratio': strength_factors['bounce_ratio'],
            'age': strength_factors['age'],
            'volume_confirmation': strength_factors['volume_confirmation'],
            'confluence': strength_factors['confluence']
        }
        
        # Calculate weighted score
        score = sum(normalized_factors[factor] * weights[factor] 
                   for factor in weights.keys())
        
        return score * 100  # Return as percentage
    
    def _identify_key_levels(self, level_strengths: List[Dict]) -> List[Dict]:
        """
        Identify the most significant support and resistance levels.
        """
        if not level_strengths:
            return []
        
        # Sort by strength
        sorted_levels = sorted(level_strengths, key=lambda x: x['strength'], reverse=True)
        
        # Take top levels (max 5 of each type)
        key_supports = [l for l in sorted_levels if l['type'] == 'support'][:5]
        key_resistances = [l for l in sorted_levels if l['type'] == 'resistance'][:5]
        
        return key_supports + key_resistances
    
    def _find_nearest_levels(self, level_strengths: List[Dict], 
                           current_price: float) -> Dict:
        """
        Find nearest support and resistance levels to current price.
        """
        nearest = {'support': None, 'resistance': None}
        
        supports = [l for l in level_strengths if l['type'] == 'support' and l['price'] < current_price]
        resistances = [l for l in level_strengths if l['type'] == 'resistance' and l['price'] > current_price]
        
        if supports:
            nearest['support'] = max(supports, key=lambda x: x['price'])
        
        if resistances:
            nearest['resistance'] = min(resistances, key=lambda x: x['price'])
        
        return nearest
    
    def _find_level_confluence(self, level_strengths: List[Dict]) -> List[Dict]:
        """
        Find areas where multiple levels converge (confluence zones).
        """
        confluences = []
        
        if len(level_strengths) < 2:
            return confluences
        
        # Group levels that are close together
        tolerance = 0.01  # 1% tolerance for confluence
        
        for i, level1 in enumerate(level_strengths):
            confluent_levels = [level1]
            
            for j, level2 in enumerate(level_strengths):
                if i != j and abs(level1['price'] - level2['price']) / level1['price'] < tolerance:
                    confluent_levels.append(level2)
            
            if len(confluent_levels) > 1:
                # Calculate confluence zone
                prices = [l['price'] for l in confluent_levels]
                avg_strength = sum(l['strength'] for l in confluent_levels) / len(confluent_levels)
                
                confluences.append({
                    'center_price': np.mean(prices),
                    'high_price': max(prices),
                    'low_price': min(prices),
                    'level_count': len(confluent_levels),
                    'average_strength': avg_strength,
                    'levels': confluent_levels
                })
        
        # Remove duplicates and sort by strength
        unique_confluences = []
        seen_centers = set()
        
        for conf in sorted(confluences, key=lambda x: x['average_strength'], reverse=True):
            center = round(conf['center_price'], 4)
            if center not in seen_centers:
                unique_confluences.append(conf)
                seen_centers.add(center)
        
        return unique_confluences[:5]  # Top 5 confluence zones
    
    def _identify_broken_levels(self, data: pd.DataFrame, 
                              level_strengths: List[Dict]) -> List[Dict]:
        """
        Identify levels that have been recently broken.
        """
        broken_levels = []
        current_price = data['close'].iloc[-1]
        
        # Look at recent price action (last 10 candles)
        recent_data = data.tail(10)
        
        for level_data in level_strengths:
            level_price = level_data['price']
            level_type = level_data['type']
            
            # Check if level was broken in recent data
            for i, (_, candle) in enumerate(recent_data.iterrows()):
                broken = False
                break_type = None
                
                if level_type == 'resistance' and candle['close'] > level_price:
                    # Resistance broken to upside
                    if candle['high'] > level_price * 1.001:  # 0.1% margin
                        broken = True
                        break_type = 'upside_break'
                
                elif level_type == 'support' and candle['close'] < level_price:
                    # Support broken to downside
                    if candle['low'] < level_price * 0.999:  # 0.1% margin
                        broken = True
                        break_type = 'downside_break'
                
                if broken:
                    broken_levels.append({
                        **level_data,
                        'break_type': break_type,
                        'break_candle_index': len(data) - len(recent_data) + i,
                        'break_price': candle['close'],
                        'distance_from_break': abs(current_price - level_price) / level_price * 100
                    })
                    break
        
        return broken_levels
    
    def _empty_sr_analysis(self) -> Dict:
        """Return empty S/R analysis structure."""
        return {
            'support_levels': [],
            'resistance_levels': [],
            'key_levels': [],
            'nearest_support': None,
            'nearest_resistance': None,
            'level_confluence': [],
            'broken_levels': [],
            'current_price': 0.0
        }