"""
Market structure analysis for identifying structure breaks, liquidity points, and clean zones.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Trend direction enumeration."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"


class StructureBreakType(Enum):
    """Types of structure breaks."""
    BOSS = "boss"  # Break of structure
    MINOR = "minor"
    MAJOR = "major"


@dataclass
class StructureBreak:
    """Represents a structure break event."""
    timestamp: pd.Timestamp
    price: float
    break_type: StructureBreakType
    direction: TrendDirection
    strength: float
    volume: float


@dataclass
class LiquidityPoint:
    """Represents a liquidity point for potential targeting."""
    price: float
    volume: float
    timestamp: pd.Timestamp
    point_type: str  # 'high', 'low', 'equal_highs', 'equal_lows'
    strength: float


@dataclass
class CleanZone:
    """Represents a clean zone for potential entry."""
    lower_bound: float
    upper_bound: float
    timestamp: pd.Timestamp
    volume_profile: float
    quality_score: float
    respected_count: int


class MarketStructureAnalyzer:
    """Analyzes market structure for trading decisions."""
    
    def __init__(self, config):
        self.config = config
        self.structure_breaks: List[StructureBreak] = []
        self.liquidity_points: List[LiquidityPoint] = []
        self.clean_zones: List[CleanZone] = []
    
    def analyze_structure_breaks(self, df: pd.DataFrame) -> List[StructureBreak]:
        """
        Identify structure breaks in the price data.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of identified structure breaks
        """
        structure_breaks = []
        
        # Calculate swing highs and lows
        swing_highs = self._find_swing_points(df, 'high', True)
        swing_lows = self._find_swing_points(df, 'low', False)
        
        # Analyze breaks of swing highs (bullish structure breaks)
        for i, (timestamp, price) in enumerate(swing_highs[:-1]):
            next_high = swing_highs[i + 1][1]
            if self._is_structure_break(df, timestamp, price, next_high, True):
                strength = self._calculate_break_strength(df, timestamp, price, True)
                if strength >= self.config.min_structure_break_strength:
                    break_type = self._classify_break_type(strength)
                    volume = df.loc[df.index == timestamp, 'volume'].iloc[0]
                    
                    structure_breaks.append(StructureBreak(
                        timestamp=timestamp,
                        price=price,
                        break_type=break_type,
                        direction=TrendDirection.BULLISH,
                        strength=strength,
                        volume=volume
                    ))
        
        # Analyze breaks of swing lows (bearish structure breaks)
        for i, (timestamp, price) in enumerate(swing_lows[:-1]):
            next_low = swing_lows[i + 1][1]
            if self._is_structure_break(df, timestamp, price, next_low, False):
                strength = self._calculate_break_strength(df, timestamp, price, False)
                if strength >= self.config.min_structure_break_strength:
                    break_type = self._classify_break_type(strength)
                    volume = df.loc[df.index == timestamp, 'volume'].iloc[0]
                    
                    structure_breaks.append(StructureBreak(
                        timestamp=timestamp,
                        price=price,
                        break_type=break_type,
                        direction=TrendDirection.BEARISH,
                        strength=strength,
                        volume=volume
                    ))
        
        self.structure_breaks = structure_breaks
        return structure_breaks
    
    def identify_liquidity_points(self, df: pd.DataFrame) -> List[LiquidityPoint]:
        """
        Identify liquidity points that can be targeted for barrages.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of liquidity points
        """
        liquidity_points = []
        
        # Find equal highs and lows
        equal_highs = self._find_equal_levels(df, 'high', True)
        equal_lows = self._find_equal_levels(df, 'low', False)
        
        # Add equal highs as liquidity points
        for price, timestamps, avg_volume in equal_highs:
            strength = self._calculate_liquidity_strength(price, timestamps, avg_volume, df)
            liquidity_points.append(LiquidityPoint(
                price=price,
                volume=avg_volume,
                timestamp=timestamps[-1],
                point_type='equal_highs',
                strength=strength
            ))
        
        # Add equal lows as liquidity points
        for price, timestamps, avg_volume in equal_lows:
            strength = self._calculate_liquidity_strength(price, timestamps, avg_volume, df)
            liquidity_points.append(LiquidityPoint(
                price=price,
                volume=avg_volume,
                timestamp=timestamps[-1],
                point_type='equal_lows',
                strength=strength
            ))
        
        # Add recent swing highs and lows
        recent_highs = self._find_swing_points(df.tail(50), 'high', True)
        recent_lows = self._find_swing_points(df.tail(50), 'low', False)
        
        for timestamp, price in recent_highs:
            volume = df.loc[df.index == timestamp, 'volume'].iloc[0]
            strength = self._calculate_liquidity_strength(price, [timestamp], volume, df)
            liquidity_points.append(LiquidityPoint(
                price=price,
                volume=volume,
                timestamp=timestamp,
                point_type='high',
                strength=strength
            ))
        
        for timestamp, price in recent_lows:
            volume = df.loc[df.index == timestamp, 'volume'].iloc[0]
            strength = self._calculate_liquidity_strength(price, [timestamp], volume, df)
            liquidity_points.append(LiquidityPoint(
                price=price,
                volume=volume,
                timestamp=timestamp,
                point_type='low',
                strength=strength
            ))
        
        self.liquidity_points = liquidity_points
        return liquidity_points
    
    def find_clean_zones(self, df: pd.DataFrame) -> List[CleanZone]:
        """
        Identify clean zones for high-probability entries.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            List of clean zones
        """
        clean_zones = []
        
        # Look for zones with minimal price overlap and good volume
        for i in range(20, len(df) - 5):
            zone = self._analyze_potential_zone(df, i)
            if zone and zone.quality_score > 0.6:
                clean_zones.append(zone)
        
        self.clean_zones = clean_zones
        return clean_zones
    
    def _find_swing_points(self, df: pd.DataFrame, column: str, is_high: bool) -> List[Tuple[pd.Timestamp, float]]:
        """Find swing highs or lows in the data."""
        window = 5
        swing_points = []
        
        for i in range(window, len(df) - window):
            current_value = df.iloc[i][column]
            window_values = df.iloc[i-window:i+window+1][column]
            
            if is_high and current_value == window_values.max():
                swing_points.append((df.index[i], current_value))
            elif not is_high and current_value == window_values.min():
                swing_points.append((df.index[i], current_value))
        
        return swing_points
    
    def _is_structure_break(self, df: pd.DataFrame, timestamp: pd.Timestamp, 
                           price: float, next_price: float, is_bullish: bool) -> bool:
        """Determine if a price level represents a structure break."""
        if is_bullish:
            return next_price > price
        else:
            return next_price < price
    
    def _calculate_break_strength(self, df: pd.DataFrame, timestamp: pd.Timestamp, 
                                 price: float, is_bullish: bool) -> float:
        """Calculate the strength of a structure break."""
        # Find data after the timestamp
        future_data = df[df.index > timestamp].head(10)
        if future_data.empty:
            return 0.0
        
        if is_bullish:
            max_break = future_data['high'].max()
            strength = (max_break - price) / price
        else:
            min_break = future_data['low'].min()
            strength = (price - min_break) / price
        
        # Normalize strength between 0 and 1
        return min(strength * 10, 1.0)
    
    def _classify_break_type(self, strength: float) -> StructureBreakType:
        """Classify the type of structure break based on strength."""
        if strength >= 0.9:
            return StructureBreakType.BOSS
        elif strength >= 0.7:
            return StructureBreakType.MAJOR
        else:
            return StructureBreakType.MINOR
    
    def _find_equal_levels(self, df: pd.DataFrame, column: str, is_high: bool) -> List[Tuple[float, List[pd.Timestamp], float]]:
        """Find equal highs or lows that represent liquidity."""
        swing_points = self._find_swing_points(df, column, is_high)
        equal_levels = []
        tolerance = 0.001  # 0.1% tolerance for "equal" levels
        
        for i, (timestamp1, price1) in enumerate(swing_points):
            equal_timestamps = [timestamp1]
            volumes = [df.loc[df.index == timestamp1, 'volume'].iloc[0]]
            
            for j, (timestamp2, price2) in enumerate(swing_points[i+1:], i+1):
                if abs(price1 - price2) / price1 <= tolerance:
                    equal_timestamps.append(timestamp2)
                    volumes.append(df.loc[df.index == timestamp2, 'volume'].iloc[0])
            
            if len(equal_timestamps) >= 2:  # At least 2 equal levels
                avg_volume = np.mean(volumes)
                equal_levels.append((price1, equal_timestamps, avg_volume))
        
        return equal_levels
    
    def _calculate_liquidity_strength(self, price: float, timestamps: List[pd.Timestamp], 
                                    volume: float, df: pd.DataFrame) -> float:
        """Calculate the strength of a liquidity point."""
        # Base strength on volume and number of touches
        volume_factor = min(volume / df['volume'].mean(), 2.0)
        touch_factor = min(len(timestamps) / 3.0, 1.0)
        
        return (volume_factor + touch_factor) / 2.0
    
    def _analyze_potential_zone(self, df: pd.DataFrame, index: int) -> Optional[CleanZone]:
        """Analyze if a price area represents a clean zone."""
        window = 10
        start_idx = max(0, index - window)
        end_idx = min(len(df), index + window)
        
        zone_data = df.iloc[start_idx:end_idx]
        
        # Calculate zone boundaries
        lower_bound = zone_data['low'].min()
        upper_bound = zone_data['high'].max()
        
        # Check if zone is "clean" (minimal overlapping candles)
        overlap_count = 0
        for i in range(len(zone_data) - 1):
            current_range = zone_data.iloc[i]['high'] - zone_data.iloc[i]['low']
            next_range = zone_data.iloc[i+1]['high'] - zone_data.iloc[i+1]['low']
            
            overlap = min(zone_data.iloc[i]['high'], zone_data.iloc[i+1]['high']) - \
                     max(zone_data.iloc[i]['low'], zone_data.iloc[i+1]['low'])
            
            if overlap > 0:
                overlap_count += 1
        
        # Calculate quality score
        zone_height = upper_bound - lower_bound
        avg_volume = zone_data['volume'].mean()
        overlap_ratio = overlap_count / len(zone_data)
        
        quality_score = (1 - overlap_ratio) * min(avg_volume / df['volume'].mean(), 1.5)
        
        if quality_score > 0.5 and zone_height > 0:
            return CleanZone(
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                timestamp=df.index[index],
                volume_profile=avg_volume,
                quality_score=quality_score,
                respected_count=0  # Will be updated as zone is tested
            )
        
        return None