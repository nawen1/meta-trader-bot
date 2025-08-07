"""
Structural Analyzer - Higher timeframe analysis and clean zone identification
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta

from ..core.models import (
    MarketStructure, TimeFrame, TradeDirection, TradingConfig
)


class StructuralAnalyzer:
    """
    Analyzes market structure across multiple timeframes to provide context
    for trading decisions.
    
    Key Features:
    - Multi-timeframe structural analysis
    - Clean zone identification
    - Higher timeframe trend context
    - Structure strength assessment
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.structure_cache: Dict[TimeFrame, MarketStructure] = {}
        self.cache_expiry = timedelta(minutes=15)  # Cache structures for 15 minutes
        
    def analyze_market_structure(
        self, 
        price_data_dict: Dict[TimeFrame, pd.DataFrame]
    ) -> Dict[TimeFrame, MarketStructure]:
        """
        Analyze market structure across multiple timeframes.
        
        Args:
            price_data_dict: Dict of timeframe -> price data
            
        Returns:
            Dict of timeframe -> market structure analysis
        """
        structures = {}
        
        for timeframe, price_data in price_data_dict.items():
            if timeframe in self.config.timeframes_to_analyze:
                structure = self._analyze_single_timeframe(timeframe, price_data)
                structures[timeframe] = structure
                
                # Cache the structure
                self.structure_cache[timeframe] = structure
                
        return structures
    
    def _analyze_single_timeframe(self, timeframe: TimeFrame, price_data: pd.DataFrame) -> MarketStructure:
        """Analyze market structure for a single timeframe."""
        
        # Determine higher timeframe trend
        trend = self._determine_trend(price_data)
        
        # Identify clean zones
        clean_zones = self._identify_clean_zones(price_data)
        
        # Find key structural levels
        key_levels = self._find_key_levels(price_data)
        
        # Calculate overall structure strength
        structure_strength = self._calculate_structure_strength(price_data, trend, clean_zones)
        
        return MarketStructure(
            higher_timeframe_trend=trend,
            clean_zones=clean_zones,
            key_levels=key_levels,
            structure_strength=structure_strength,
            last_updated=datetime.now()
        )
    
    def _determine_trend(self, price_data: pd.DataFrame) -> TradeDirection:
        """Determine the overall trend direction for the timeframe."""
        if len(price_data) < 20:
            return TradeDirection.LONG  # Default
            
        # Use multiple trend indicators
        
        # 1. Moving average trend
        short_ma = price_data['Close'].rolling(10).mean()
        long_ma = price_data['Close'].rolling(20).mean()
        ma_trend = short_ma.iloc[-1] > long_ma.iloc[-1]
        
        # 2. Price slope trend
        closes = price_data['Close'].values
        slope = np.polyfit(range(len(closes)), closes, 1)[0]
        slope_trend = slope > 0
        
        # 3. Higher highs and higher lows
        structure_trend = self._check_trend_structure(price_data)
        
        # Combine indicators
        bullish_votes = sum([ma_trend, slope_trend, structure_trend])
        
        return TradeDirection.LONG if bullish_votes >= 2 else TradeDirection.SHORT
    
    def _check_trend_structure(self, price_data: pd.DataFrame) -> bool:
        """Check for higher highs and higher lows (bullish structure)."""
        if len(price_data) < 20:
            return True
            
        # Find recent swing points
        swing_highs = []
        swing_lows = []
        
        window = 5
        for i in range(window, len(price_data) - window):
            high = price_data.iloc[i]['High']
            low = price_data.iloc[i]['Low']
            
            # Check for swing high
            left_highs = price_data.iloc[i-window:i]['High'].values
            right_highs = price_data.iloc[i+1:i+window+1]['High'].values
            
            if all(high >= h for h in left_highs) and all(high >= h for h in right_highs):
                swing_highs.append((i, high))
                
            # Check for swing low
            left_lows = price_data.iloc[i-window:i]['Low'].values
            right_lows = price_data.iloc[i+1:i+window+1]['Low'].values
            
            if all(low <= l for l in left_lows) and all(low <= l for l in right_lows):
                swing_lows.append((i, low))
        
        # Check for higher highs and higher lows
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = swing_highs[-2:]
            recent_lows = swing_lows[-2:]
            
            higher_high = recent_highs[1][1] > recent_highs[0][1]
            higher_low = recent_lows[1][1] > recent_lows[0][1]
            
            return higher_high and higher_low
            
        return True  # Default to bullish if insufficient data
    
    def _identify_clean_zones(self, price_data: pd.DataFrame) -> List[Tuple[float, float]]:
        """
        Identify clean zones - areas with minimal price action congestion.
        
        Clean zones are characterized by:
        - Low consolidation/ranging
        - Clear directional movement
        - Minimal overlapping price ranges
        """
        clean_zones = []
        
        if len(price_data) < 30:
            return clean_zones
            
        # Analyze price action in segments
        segment_size = 10
        
        for i in range(0, len(price_data) - segment_size, segment_size // 2):
            segment = price_data.iloc[i:i + segment_size]
            
            if self._is_clean_zone_segment(segment):
                zone_low = segment['Low'].min()
                zone_high = segment['High'].max()
                clean_zones.append((zone_low, zone_high))
                
        # Merge overlapping zones
        merged_zones = self._merge_overlapping_zones(clean_zones)
        
        return merged_zones[:10]  # Limit to top 10 cleanest zones
    
    def _is_clean_zone_segment(self, segment: pd.DataFrame) -> bool:
        """Determine if a price segment represents a clean zone."""
        if len(segment) < 5:
            return False
            
        # Calculate metrics for cleanliness
        
        # 1. Directional consistency
        closes = segment['Close'].values
        price_changes = np.diff(closes)
        directional_consistency = abs(np.sum(np.sign(price_changes))) / len(price_changes)
        
        # 2. Low consolidation (tight range relative to movement)
        total_range = segment['High'].max() - segment['Low'].min()
        total_movement = np.sum(np.abs(price_changes))
        
        consolidation_ratio = total_range / total_movement if total_movement > 0 else 1
        
        # 3. Clean price action (low wick ratios)
        avg_wick_ratio = self._calculate_average_wick_ratio(segment)
        
        # Criteria for clean zone
        is_directional = directional_consistency > 0.6
        is_trending = consolidation_ratio < 0.8
        is_clean_action = avg_wick_ratio < 0.4
        
        return is_directional and is_trending and is_clean_action
    
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
    
    def _merge_overlapping_zones(self, zones: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Merge overlapping or adjacent clean zones."""
        if not zones:
            return []
            
        # Sort zones by low price
        sorted_zones = sorted(zones, key=lambda x: x[0])
        merged = []
        
        current_low, current_high = sorted_zones[0]
        
        for low, high in sorted_zones[1:]:
            # Check for overlap or adjacency
            if low <= current_high * 1.001:  # Small tolerance for adjacency
                # Merge zones
                current_high = max(current_high, high)
            else:
                # Add current zone and start new one
                merged.append((current_low, current_high))
                current_low, current_high = low, high
                
        # Add final zone
        merged.append((current_low, current_high))
        
        return merged
    
    def _find_key_levels(self, price_data: pd.DataFrame) -> List[float]:
        """Find key structural levels (support/resistance)."""
        levels = []
        
        if len(price_data) < 20:
            return levels
            
        # Find swing points
        swing_points = self._find_swing_points(price_data)
        
        # Group nearby levels
        level_groups = self._group_nearby_levels(swing_points)
        
        # Calculate strength of each level
        key_levels = []
        for group in level_groups:
            level_strength = len(group)  # Number of touches
            avg_price = np.mean(group)
            
            if level_strength >= 2:  # At least 2 touches to be significant
                key_levels.append(avg_price)
                
        return sorted(key_levels)[:20]  # Limit to top 20 levels
    
    def _find_swing_points(self, price_data: pd.DataFrame) -> List[float]:
        """Find swing high and low points."""
        swing_points = []
        
        window = 5
        for i in range(window, len(price_data) - window):
            high = price_data.iloc[i]['High']
            low = price_data.iloc[i]['Low']
            
            # Check for swing high
            left_highs = price_data.iloc[i-window:i]['High'].values
            right_highs = price_data.iloc[i+1:i+window+1]['High'].values
            
            if all(high >= h for h in left_highs) and all(high >= h for h in right_highs):
                swing_points.append(high)
                
            # Check for swing low
            left_lows = price_data.iloc[i-window:i]['Low'].values
            right_lows = price_data.iloc[i+1:i+window+1]['Low'].values
            
            if all(low <= l for l in left_lows) and all(low <= l for l in right_lows):
                swing_points.append(low)
                
        return swing_points
    
    def _group_nearby_levels(self, levels: List[float]) -> List[List[float]]:
        """Group nearby price levels together."""
        if not levels:
            return []
            
        sorted_levels = sorted(levels)
        groups = []
        current_group = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            # Check if level is close to current group
            group_avg = np.mean(current_group)
            distance_ratio = abs(level - group_avg) / group_avg
            
            if distance_ratio <= 0.005:  # Within 0.5%
                current_group.append(level)
            else:
                groups.append(current_group)
                current_group = [level]
                
        groups.append(current_group)
        return groups
    
    def _calculate_structure_strength(
        self, 
        price_data: pd.DataFrame, 
        trend: TradeDirection, 
        clean_zones: List[Tuple[float, float]]
    ) -> float:
        """Calculate overall structural strength of the market."""
        strength = 0.0
        
        # Trend consistency component
        if len(price_data) >= 20:
            closes = price_data['Close'].tail(20).values
            trend_consistency = self._calculate_trend_consistency(closes)
            strength += trend_consistency * 0.4
        
        # Clean zone component
        clean_zone_ratio = len(clean_zones) / max(len(price_data) / 10, 1)
        strength += min(clean_zone_ratio, 0.3)
        
        # Volatility component (moderate volatility is good)
        if len(price_data) >= 10:
            volatility = np.std(price_data['Close'].tail(10)) / np.mean(price_data['Close'].tail(10))
            optimal_volatility = 0.01  # 1% volatility is optimal
            volatility_score = 1 - abs(volatility - optimal_volatility) / optimal_volatility
            strength += max(0, min(volatility_score, 0.3))
            
        return min(strength, 1.0)
    
    def _calculate_trend_consistency(self, closes: np.ndarray) -> float:
        """Calculate how consistent the trend direction is."""
        if len(closes) < 5:
            return 0.5
            
        price_changes = np.diff(closes)
        positive_moves = np.sum(price_changes > 0)
        negative_moves = np.sum(price_changes < 0)
        
        total_moves = len(price_changes)
        dominant_direction_ratio = max(positive_moves, negative_moves) / total_moves
        
        return dominant_direction_ratio
    
    def get_higher_timeframe_context(self, current_timeframe: TimeFrame) -> Optional[MarketStructure]:
        """Get higher timeframe context for decision making."""
        # Define timeframe hierarchy
        timeframe_hierarchy = [
            TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, 
            TimeFrame.M30, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1
        ]
        
        current_index = timeframe_hierarchy.index(current_timeframe)
        
        # Look for higher timeframes
        for i in range(current_index + 1, len(timeframe_hierarchy)):
            higher_tf = timeframe_hierarchy[i]
            if higher_tf in self.structure_cache:
                # Check if cache is still valid
                structure = self.structure_cache[higher_tf]
                if datetime.now() - structure.last_updated < self.cache_expiry:
                    return structure
                    
        return None
    
    def is_price_in_clean_zone(self, price: float, timeframe: TimeFrame) -> bool:
        """Check if current price is within a clean zone."""
        if timeframe not in self.structure_cache:
            return True  # Assume clean if no data
            
        structure = self.structure_cache[timeframe]
        
        for zone_low, zone_high in structure.clean_zones:
            if zone_low <= price <= zone_high:
                return True
                
        return False
    
    def get_nearest_key_level(self, price: float, timeframe: TimeFrame) -> Optional[float]:
        """Get the nearest key structural level to current price."""
        if timeframe not in self.structure_cache:
            return None
            
        structure = self.structure_cache[timeframe]
        
        if not structure.key_levels:
            return None
            
        # Find closest level
        distances = [abs(level - price) for level in structure.key_levels]
        min_distance_index = np.argmin(distances)
        
        return structure.key_levels[min_distance_index]
    
    def validate_trade_against_structure(
        self, 
        entry_price: float, 
        direction: TradeDirection, 
        timeframe: TimeFrame
    ) -> Dict[str, any]:
        """
        Validate a potential trade against structural analysis.
        
        Returns:
            Dict with validation results and recommendations
        """
        validation = {
            'valid': True,
            'warnings': [],
            'recommendations': [],
            'structure_alignment': 0.0
        }
        
        # Check higher timeframe context
        higher_tf_structure = self.get_higher_timeframe_context(timeframe)
        
        if higher_tf_structure:
            # Check trend alignment
            if direction != higher_tf_structure.higher_timeframe_trend:
                validation['warnings'].append('Trade against higher timeframe trend')
                validation['structure_alignment'] -= 0.3
            else:
                validation['structure_alignment'] += 0.4
                
        # Check clean zone
        if not self.is_price_in_clean_zone(entry_price, timeframe):
            validation['warnings'].append('Entry not in clean zone')
            validation['structure_alignment'] -= 0.2
        else:
            validation['structure_alignment'] += 0.3
            
        # Check proximity to key levels
        nearest_level = self.get_nearest_key_level(entry_price, timeframe)
        if nearest_level:
            distance_ratio = abs(entry_price - nearest_level) / entry_price
            if distance_ratio < 0.002:  # Very close to key level
                validation['warnings'].append('Entry very close to key structural level')
                validation['structure_alignment'] -= 0.1
                
        # Overall validation
        if validation['structure_alignment'] < 0:
            validation['valid'] = False
            validation['recommendations'].append('Wait for better structural setup')
        elif validation['structure_alignment'] < 0.3:
            validation['recommendations'].append('Consider reducing position size')
            
        return validation