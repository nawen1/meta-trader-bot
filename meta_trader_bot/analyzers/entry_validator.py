"""
Entry Validator - Strict entry validation based on trading models
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime

from ..core.models import (
    EntrySignal, BossStructure, EntryModel, TradeDirection, 
    TimeFrame, TradingConfig
)


class EntryValidator:
    """
    Validates trade entries based on strict principles and trading models.
    
    Key Features:
    - Ensures entries align with predefined models (especially Model 2)
    - Recognizes Boss structures as critical entry signals
    - Identifies liquid points for precise entry timing
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.boss_structure_lookback = 50  # Bars to analyze for Boss structures
        self.liquid_point_threshold = 0.001  # 0.1% for liquid point detection
        
    def validate_entry(self, price_data: pd.DataFrame, current_price: float) -> Optional[EntrySignal]:
        """
        Main method to validate potential trade entries.
        
        Args:
            price_data: OHLC price data
            current_price: Current market price
            
        Returns:
            EntrySignal if valid entry found, None otherwise
        """
        # Analyze Boss structures
        boss_structure = self._analyze_boss_structures(price_data)
        
        # Identify liquid points
        liquid_points = self._identify_liquid_points(price_data, current_price)
        
        # Check Model 2 alignment
        model_alignment = self._check_model_alignment(price_data, current_price)
        
        # Determine trade direction
        direction = self._determine_trade_direction(price_data, current_price, boss_structure)
        
        # Validate clean zone
        clean_zone = self._validate_clean_zone(price_data, current_price)
        
        # Calculate confidence
        confidence = self._calculate_entry_confidence(
            boss_structure, liquid_points, model_alignment, clean_zone
        )
        
        # Only return signal if confidence meets threshold
        if confidence >= self.config.min_entry_confidence:
            return EntrySignal(
                price=current_price,
                direction=direction,
                model_alignment=model_alignment,
                boss_structure=boss_structure,
                liquid_points=liquid_points,
                confidence=confidence,
                clean_zone=clean_zone,
                timestamp=datetime.now()
            )
            
        return None
    
    def _analyze_boss_structures(self, price_data: pd.DataFrame) -> Optional[BossStructure]:
        """
        Analyze price data to identify Boss structures.
        
        A Boss structure is characterized by:
        - Clear high and low points
        - Strong price rejection or acceptance
        - Significant volume or volatility
        """
        if len(price_data) < self.boss_structure_lookback:
            return None
            
        # Analyze recent price action for Boss patterns
        recent_data = price_data.tail(self.boss_structure_lookback)
        
        # Find significant high and low points
        high_point = recent_data['High'].max()
        low_point = recent_data['Low'].min()
        
        # Find when these points occurred
        high_idx = recent_data['High'].idxmax()
        low_idx = recent_data['Low'].idxmin()
        
        # Calculate structure strength based on:
        # 1. Range size
        # 2. Time between high and low
        # 3. Price reaction strength
        
        price_range = (high_point - low_point) / low_point
        time_separation = abs(recent_data.index.get_loc(high_idx) - recent_data.index.get_loc(low_idx))
        
        # Analyze price reaction at these levels
        reaction_strength = self._calculate_reaction_strength(recent_data, high_point, low_point)
        
        # Calculate overall structure strength
        strength = self._calculate_boss_structure_strength(
            price_range, time_separation, reaction_strength
        )
        
        # Validate if this is a true Boss structure
        is_valid = self._validate_boss_structure(recent_data, high_point, low_point, strength)
        
        if is_valid and strength >= 0.5:  # Minimum strength threshold
            formation_time = max(
                recent_data.loc[high_idx].name if hasattr(recent_data.loc[high_idx], 'name') else datetime.now(),
                recent_data.loc[low_idx].name if hasattr(recent_data.loc[low_idx], 'name') else datetime.now()
            )
            
            return BossStructure(
                high_point=high_point,
                low_point=low_point,
                strength=strength,
                timeframe=TimeFrame.M15,  # Default timeframe
                formation_time=formation_time,
                is_valid=is_valid
            )
            
        return None
    
    def _calculate_reaction_strength(self, data: pd.DataFrame, high_point: float, low_point: float) -> float:
        """Calculate the strength of price reaction at key levels."""
        reaction_strength = 0.0
        
        # Look for strong rejections at high and low points
        tolerance = (high_point - low_point) * 0.02  # 2% tolerance
        
        for _, bar in data.iterrows():
            # Check reaction at high point
            if abs(bar['High'] - high_point) <= tolerance:
                # Strong rejection if close is much lower than high
                if bar['Close'] < bar['High'] * 0.98:
                    reaction_strength += 0.3
                    
            # Check reaction at low point  
            if abs(bar['Low'] - low_point) <= tolerance:
                # Strong rejection if close is much higher than low
                if bar['Close'] > bar['Low'] * 1.02:
                    reaction_strength += 0.3
                    
        return min(reaction_strength, 1.0)
    
    def _calculate_boss_structure_strength(self, price_range: float, time_separation: int, reaction_strength: float) -> float:
        """Calculate overall Boss structure strength."""
        # Range component (larger ranges are stronger)
        range_component = min(price_range * 20, 0.4)  # Max 0.4
        
        # Time component (appropriate separation is stronger)
        optimal_time = 10  # 10 bars is optimal separation
        time_component = 0.3 * (1 - abs(time_separation - optimal_time) / optimal_time)
        time_component = max(0, min(time_component, 0.3))
        
        # Reaction component
        reaction_component = reaction_strength * 0.3
        
        return range_component + time_component + reaction_component
    
    def _validate_boss_structure(self, data: pd.DataFrame, high_point: float, low_point: float, strength: float) -> bool:
        """Validate if the identified structure is a true Boss structure."""
        # Must have sufficient strength
        if strength < 0.3:
            return False
            
        # Must have clear separation between high and low
        range_size = (high_point - low_point) / low_point
        if range_size < 0.005:  # Minimum 0.5% range
            return False
            
        # Must not be in a tight consolidation
        recent_volatility = np.std(data['Close'].tail(10)) / np.mean(data['Close'].tail(10))
        if recent_volatility < 0.001:  # Too low volatility
            return False
            
        return True
    
    def _identify_liquid_points(self, price_data: pd.DataFrame, current_price: float) -> List[float]:
        """
        Identify liquid points - precise levels where liquidity resides.
        
        Liquid points are typically:
        - Previous highs/lows that attracted volume
        - Round numbers
        - Fibonacci levels
        - Order block levels
        """
        liquid_points = []
        
        if len(price_data) < 20:
            return liquid_points
            
        # Identify swing highs and lows
        swing_levels = self._find_swing_levels(price_data)
        
        # Add significant swing levels as liquid points
        for level in swing_levels:
            distance = abs(level - current_price) / current_price
            if distance <= 0.02:  # Within 2% of current price
                liquid_points.append(level)
                
        # Add round numbers near current price
        round_numbers = self._find_round_numbers(current_price)
        liquid_points.extend(round_numbers)
        
        # Remove duplicates and sort
        liquid_points = list(set(liquid_points))
        liquid_points.sort()
        
        return liquid_points[:10]  # Limit to top 10 most relevant
    
    def _find_swing_levels(self, price_data: pd.DataFrame) -> List[float]:
        """Find significant swing high and low levels."""
        levels = []
        
        # Use a simple swing detection algorithm
        window = 5  # Look 5 bars each side
        
        for i in range(window, len(price_data) - window):
            current_high = price_data.iloc[i]['High']
            current_low = price_data.iloc[i]['Low']
            
            # Check if current bar is a swing high
            left_highs = price_data.iloc[i-window:i]['High'].values
            right_highs = price_data.iloc[i+1:i+window+1]['High'].values
            
            if all(current_high >= h for h in left_highs) and all(current_high >= h for h in right_highs):
                levels.append(current_high)
                
            # Check if current bar is a swing low
            left_lows = price_data.iloc[i-window:i]['Low'].values
            right_lows = price_data.iloc[i+1:i+window+1]['Low'].values
            
            if all(current_low <= l for l in left_lows) and all(current_low <= l for l in right_lows):
                levels.append(current_low)
                
        return levels
    
    def _find_round_numbers(self, current_price: float) -> List[float]:
        """Find psychologically significant round numbers near current price."""
        round_numbers = []
        
        # Determine appropriate round number intervals based on price
        if current_price < 1:
            intervals = [0.01, 0.05, 0.1]
        elif current_price < 10:
            intervals = [0.1, 0.5, 1.0]
        elif current_price < 100:
            intervals = [1.0, 5.0, 10.0]
        else:
            intervals = [10.0, 50.0, 100.0]
            
        for interval in intervals:
            # Find round numbers above and below current price
            lower_round = int(current_price / interval) * interval
            upper_round = lower_round + interval
            
            # Add if within reasonable distance
            if abs(lower_round - current_price) / current_price <= 0.02:
                round_numbers.append(lower_round)
            if abs(upper_round - current_price) / current_price <= 0.02:
                round_numbers.append(upper_round)
                
        return round_numbers
    
    def _check_model_alignment(self, price_data: pd.DataFrame, current_price: float) -> EntryModel:
        """
        Check alignment with predefined trading models.
        
        Model 2 characteristics:
        - Clear break of structure
        - Pullback to order block
        - Clean entry with defined risk
        """
        if len(price_data) < 20:
            return EntryModel.MODEL_1
            
        # Check for Model 2 pattern
        if self._validate_model_2_pattern(price_data, current_price):
            return EntryModel.MODEL_2
            
        # Check for Model 1 pattern (basic trend following)
        if self._validate_model_1_pattern(price_data, current_price):
            return EntryModel.MODEL_1
            
        # Default to Model 3 (counter-trend or complex)
        return EntryModel.MODEL_3
    
    def _validate_model_2_pattern(self, price_data: pd.DataFrame, current_price: float) -> bool:
        """
        Validate Model 2 pattern:
        1. Break of structure (BOS)
        2. Pullback to mitigation level
        3. Clean entry setup
        """
        recent_data = price_data.tail(20)
        
        # 1. Check for break of structure
        bos_detected = self._detect_break_of_structure(recent_data)
        
        if not bos_detected:
            return False
            
        # 2. Check for pullback/mitigation
        pullback_detected = self._detect_pullback_to_mitigation(recent_data, current_price)
        
        if not pullback_detected:
            return False
            
        # 3. Check for clean entry setup
        clean_entry = self._validate_clean_entry_setup(recent_data, current_price)
        
        return clean_entry
    
    def _detect_break_of_structure(self, data: pd.DataFrame) -> bool:
        """Detect break of structure in price data."""
        if len(data) < 10:
            return False
            
        # Look for significant price movement breaking previous structure
        highs = data['High'].values
        lows = data['Low'].values
        
        # Check for upward break of structure
        recent_high = np.max(highs[-5:])
        previous_resistance = np.max(highs[:-5]) if len(highs) > 5 else recent_high
        
        upward_break = recent_high > previous_resistance * 1.002  # 0.2% break threshold
        
        # Check for downward break of structure
        recent_low = np.min(lows[-5:])
        previous_support = np.min(lows[:-5]) if len(lows) > 5 else recent_low
        
        downward_break = recent_low < previous_support * 0.998  # 0.2% break threshold
        
        return upward_break or downward_break
    
    def _detect_pullback_to_mitigation(self, data: pd.DataFrame, current_price: float) -> bool:
        """Detect pullback to a mitigation level after break of structure."""
        if len(data) < 10:
            return False
            
        closes = data['Close'].values
        
        # Check if price has pulled back after initial move
        recent_range = np.max(closes[-10:]) - np.min(closes[-10:])
        current_position = (current_price - np.min(closes[-10:])) / recent_range
        
        # Good pullback should be between 30% and 70% of recent range
        return 0.3 <= current_position <= 0.7
    
    def _validate_clean_entry_setup(self, data: pd.DataFrame, current_price: float) -> bool:
        """Validate that current setup provides a clean entry opportunity."""
        if len(data) < 5:
            return False
            
        # Check for clean price action (low wick ratios)
        recent_bars = data.tail(5)
        avg_wick_ratio = self._calculate_average_wick_ratio(recent_bars)
        
        # Check for trending momentum
        closes = data['Close'].values
        momentum_positive = closes[-1] > closes[-3]  # Simple momentum check
        
        return avg_wick_ratio < 0.4 and momentum_positive
    
    def _calculate_average_wick_ratio(self, data: pd.DataFrame) -> float:
        """Calculate average wick-to-body ratio."""
        if len(data) == 0:
            return 1.0
            
        wick_ratios = []
        for _, bar in data.iterrows():
            body_size = abs(bar['Close'] - bar['Open'])
            total_range = bar['High'] - bar['Low']
            
            if total_range > 0:
                wick_ratio = (total_range - body_size) / total_range
                wick_ratios.append(wick_ratio)
                
        return np.mean(wick_ratios) if wick_ratios else 1.0
    
    def _validate_model_1_pattern(self, price_data: pd.DataFrame, current_price: float) -> bool:
        """Validate basic trend following pattern (Model 1)."""
        if len(price_data) < 10:
            return False
            
        closes = price_data['Close'].tail(10).values
        
        # Simple trend detection
        trend_up = closes[-1] > closes[0]
        consistent_trend = np.sum(np.diff(closes) > 0) >= 6  # 60% of moves in trend direction
        
        return trend_up and consistent_trend
    
    def _determine_trade_direction(
        self, 
        price_data: pd.DataFrame, 
        current_price: float, 
        boss_structure: Optional[BossStructure]
    ) -> TradeDirection:
        """Determine optimal trade direction based on analysis."""
        
        # If Boss structure exists, use it for direction
        if boss_structure and boss_structure.is_valid:
            # If current price is closer to low, likely going up
            mid_point = (boss_structure.high_point + boss_structure.low_point) / 2
            if current_price < mid_point:
                return TradeDirection.LONG
            else:
                return TradeDirection.SHORT
                
        # Fall back to trend analysis
        if len(price_data) >= 10:
            recent_closes = price_data['Close'].tail(10).values
            if recent_closes[-1] > recent_closes[0]:
                return TradeDirection.LONG
            else:
                return TradeDirection.SHORT
                
        return TradeDirection.LONG  # Default
    
    def _validate_clean_zone(self, price_data: pd.DataFrame, current_price: float) -> bool:
        """
        Validate that current price is in a clean zone.
        
        Clean zones are areas with:
        - No significant resistance/support overhead
        - Clear price action
        - No conflicting technical signals
        """
        if len(price_data) < 20:
            return True  # Assume clean if insufficient data
            
        # Check for nearby resistance/support levels
        swing_levels = self._find_swing_levels(price_data.tail(50))
        
        # Check if current price is too close to major levels
        for level in swing_levels:
            distance = abs(level - current_price) / current_price
            if distance < 0.005:  # Too close to major level (0.5%)
                return False
                
        # Check recent volatility (clean zones have consistent movement)
        recent_closes = price_data['Close'].tail(10).values
        volatility = np.std(recent_closes) / np.mean(recent_closes)
        
        # Not too volatile, not too quiet
        return 0.002 <= volatility <= 0.03
    
    def _calculate_entry_confidence(
        self, 
        boss_structure: Optional[BossStructure], 
        liquid_points: List[float], 
        model_alignment: EntryModel,
        clean_zone: bool
    ) -> float:
        """Calculate confidence score for entry signal."""
        confidence = 0.0
        
        # Base confidence from model alignment
        if model_alignment == EntryModel.MODEL_2:
            confidence += 0.4  # Model 2 is preferred
        elif model_alignment == EntryModel.MODEL_1:
            confidence += 0.2
        else:
            confidence += 0.1
            
        # Confidence from Boss structure
        if boss_structure and boss_structure.is_valid:
            confidence += boss_structure.strength * 0.3
            
        # Confidence from liquid points
        if liquid_points:
            confidence += min(len(liquid_points) * 0.05, 0.2)  # Max 0.2
            
        # Bonus for clean zone
        if clean_zone:
            confidence += 0.1
            
        return min(confidence, 1.0)