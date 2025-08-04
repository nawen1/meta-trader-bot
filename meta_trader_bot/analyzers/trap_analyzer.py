"""
Trap Analyzer - Advanced trap recognition and operation logic
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from ..core.models import (
    TrapSignal, TrapType, RiskLevel, LiquidityZone, 
    TimeFrame, TradingConfig
)


class TrapAnalyzer:
    """
    Analyzes market data to identify and validate trap trading opportunities.
    
    Key Features:
    - Identifies traps from distance based on liquidity analysis
    - Validates safe entry points before trap operation
    - Analyzes liquidity above/below inductions
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.liquidity_threshold = 1.5  # Minimum liquidity strength
        self.induction_lookback = 20  # Bars to look back for inductions
        
    def analyze_traps(self, price_data: pd.DataFrame, volume_data: pd.DataFrame) -> List[TrapSignal]:
        """
        Main method to analyze and identify trap opportunities.
        
        Args:
            price_data: OHLC price data
            volume_data: Volume data
            
        Returns:
            List of identified trap signals
        """
        trap_signals = []
        
        # Identify liquidity zones
        liquidity_zones = self._identify_liquidity_zones(price_data, volume_data)
        
        # Analyze each potential trap area
        for i in range(len(price_data) - self.induction_lookback):
            current_bar = price_data.iloc[i + self.induction_lookback]
            historical_data = price_data.iloc[i:i + self.induction_lookback]
            
            # Check for trap patterns
            trap_signal = self._detect_trap_pattern(
                current_bar, historical_data, liquidity_zones, i + self.induction_lookback
            )
            
            if trap_signal and trap_signal.confidence >= self.config.min_trap_confidence:
                trap_signals.append(trap_signal)
                
        return trap_signals
    
    def _identify_liquidity_zones(self, price_data: pd.DataFrame, volume_data: pd.DataFrame) -> List[LiquidityZone]:
        """
        Identify key liquidity zones in the market.
        
        Args:
            price_data: OHLC price data
            volume_data: Volume data
            
        Returns:
            List of identified liquidity zones
        """
        zones = []
        
        # Calculate volume-weighted price levels
        high_volume_levels = self._find_high_volume_levels(price_data, volume_data)
        
        # Identify support and resistance levels with high liquidity
        for level in high_volume_levels:
            zone_type = self._classify_liquidity_zone(level, price_data)
            strength = self._calculate_zone_strength(level, price_data, volume_data)
            
            if strength >= self.liquidity_threshold:
                zones.append(LiquidityZone(
                    price=level['price'],
                    volume=level['volume'],
                    strength=strength,
                    timestamp=level['timestamp'],
                    zone_type=zone_type
                ))
                
        return sorted(zones, key=lambda x: x.strength, reverse=True)
    
    def _find_high_volume_levels(self, price_data: pd.DataFrame, volume_data: pd.DataFrame) -> List[dict]:
        """Find price levels with significant volume activity."""
        levels = []
        
        # Use volume profile to identify key levels
        for i in range(len(price_data)):
            bar = price_data.iloc[i]
            volume = volume_data.iloc[i] if not volume_data.empty else bar.get('Volume', 0)
            
            # Check if this is a high volume bar
            avg_volume = volume_data.rolling(20).mean().iloc[i] if not volume_data.empty else 1
            
            if volume > avg_volume * 1.5:  # 50% above average volume
                levels.append({
                    'price': (bar['High'] + bar['Low']) / 2,
                    'volume': volume,
                    'timestamp': bar.name if hasattr(bar, 'name') else datetime.now()
                })
                
        return levels
    
    def _classify_liquidity_zone(self, level: dict, price_data: pd.DataFrame) -> str:
        """Classify if a liquidity zone is support, resistance, or neutral."""
        price = level['price']
        recent_prices = price_data['Close'].tail(10).values
        
        above_count = np.sum(recent_prices > price)
        below_count = np.sum(recent_prices < price)
        
        if above_count > below_count * 1.5:
            return 'support'
        elif below_count > above_count * 1.5:
            return 'resistance'
        else:
            return 'neutral'
    
    def _calculate_zone_strength(self, level: dict, price_data: pd.DataFrame, volume_data: pd.DataFrame) -> float:
        """Calculate the strength of a liquidity zone."""
        price = level['price']
        volume = level['volume']
        
        # Count how many times price has tested this level
        price_range = price * 0.001  # 0.1% range
        tests = 0
        
        for _, bar in price_data.iterrows():
            if abs(bar['Low'] - price) <= price_range or abs(bar['High'] - price) <= price_range:
                tests += 1
                
        # Calculate strength based on volume and tests
        avg_volume = volume_data.mean() if not volume_data.empty else 1
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        
        strength = (volume_ratio * 0.7) + (tests * 0.3)
        return min(strength, 5.0)  # Cap at 5.0
    
    def _detect_trap_pattern(
        self, 
        current_bar: pd.Series, 
        historical_data: pd.DataFrame, 
        liquidity_zones: List[LiquidityZone],
        bar_index: int
    ) -> Optional[TrapSignal]:
        """
        Detect trap patterns in the current market context.
        
        Args:
            current_bar: Current price bar
            historical_data: Historical price data
            liquidity_zones: Identified liquidity zones
            bar_index: Current bar index
            
        Returns:
            TrapSignal if pattern detected, None otherwise
        """
        current_price = current_bar['Close']
        
        # Find relevant liquidity zones
        relevant_zones = self._find_relevant_liquidity_zones(current_price, liquidity_zones)
        
        if not relevant_zones:
            return None
            
        # Check for induction patterns
        induction_detected = self._detect_induction_pattern(historical_data)
        
        if not induction_detected:
            return None
            
        # Determine trap type based on liquidity position
        trap_type = self._determine_trap_type(current_price, relevant_zones)
        
        # Calculate distance to liquidity
        distance_to_liquidity = self._calculate_distance_to_liquidity(current_price, relevant_zones)
        
        # Check if safe entry exists
        safe_entry_exists = self._validate_safe_entry(
            current_bar, historical_data, relevant_zones, trap_type
        )
        
        # Calculate confidence and risk level
        confidence = self._calculate_trap_confidence(
            induction_detected, relevant_zones, distance_to_liquidity, safe_entry_exists
        )
        
        risk_level = self._assess_risk_level(confidence, distance_to_liquidity, relevant_zones)
        
        # Determine entry price if safe entry exists
        entry_price = None
        if safe_entry_exists:
            entry_price = self._calculate_optimal_entry_price(current_bar, trap_type, relevant_zones)
        
        return TrapSignal(
            trap_type=trap_type,
            entry_price=entry_price,
            confidence=confidence,
            risk_level=risk_level,
            liquidity_zones=relevant_zones,
            safe_entry_exists=safe_entry_exists,
            distance_to_liquidity=distance_to_liquidity,
            timestamp=datetime.now()
        )
    
    def _find_relevant_liquidity_zones(self, current_price: float, liquidity_zones: List[LiquidityZone]) -> List[LiquidityZone]:
        """Find liquidity zones relevant to current price action."""
        max_distance = current_price * self.config.max_distance_to_liquidity
        
        relevant_zones = []
        for zone in liquidity_zones:
            distance = abs(zone.price - current_price)
            if distance <= max_distance * 2:  # Look a bit wider for analysis
                relevant_zones.append(zone)
                
        return relevant_zones[:5]  # Limit to top 5 strongest zones
    
    def _detect_induction_pattern(self, historical_data: pd.DataFrame) -> bool:
        """Detect induction patterns in historical data."""
        if len(historical_data) < 5:
            return False
            
        # Look for break of structure followed by pullback
        closes = historical_data['Close'].values
        highs = historical_data['High'].values
        lows = historical_data['Low'].values
        
        # Check for recent break of structure
        recent_high = np.max(highs[-5:])
        recent_low = np.min(lows[-5:])
        
        # Check for pullback after break
        current_close = closes[-1]
        
        # Simple induction detection: price moved significantly then pulled back
        range_break = (recent_high - recent_low) / recent_low > 0.01  # 1% range
        pullback_detected = (current_close < recent_high * 0.98) and (current_close > recent_low * 1.02)
        
        return range_break and pullback_detected
    
    def _determine_trap_type(self, current_price: float, liquidity_zones: List[LiquidityZone]) -> TrapType:
        """Determine the type of trap based on liquidity position."""
        liquidity_above = any(zone.price > current_price for zone in liquidity_zones)
        liquidity_below = any(zone.price < current_price for zone in liquidity_zones)
        
        if liquidity_above and liquidity_below:
            return TrapType.DOUBLE_TRAP
        elif liquidity_above:
            return TrapType.LIQUIDITY_ABOVE
        elif liquidity_below:
            return TrapType.LIQUIDITY_BELOW
        else:
            return TrapType.INDUCTION_TRAP
    
    def _calculate_distance_to_liquidity(self, current_price: float, liquidity_zones: List[LiquidityZone]) -> float:
        """Calculate minimum distance to nearest liquidity zone."""
        if not liquidity_zones:
            return float('inf')
            
        min_distance = float('inf')
        for zone in liquidity_zones:
            distance = abs(zone.price - current_price) / current_price
            min_distance = min(min_distance, distance)
            
        return min_distance
    
    def _validate_safe_entry(
        self, 
        current_bar: pd.Series, 
        historical_data: pd.DataFrame, 
        liquidity_zones: List[LiquidityZone],
        trap_type: TrapType
    ) -> bool:
        """Validate if a safe entry point exists before the trap."""
        current_price = current_bar['Close']
        
        # Check distance to liquidity
        distance = self._calculate_distance_to_liquidity(current_price, liquidity_zones)
        if distance > self.config.max_distance_to_liquidity:
            return False
            
        # Check for clear price action structure
        if len(historical_data) < 10:
            return False
            
        # Look for clean breakout or pullback structure
        recent_data = historical_data.tail(10)
        price_action_clean = self._assess_price_action_clarity(recent_data)
        
        # Check for conflicting signals
        no_conflicting_signals = self._check_for_conflicting_signals(current_bar, historical_data)
        
        return price_action_clean and no_conflicting_signals and distance <= self.config.max_distance_to_liquidity
    
    def _assess_price_action_clarity(self, recent_data: pd.DataFrame) -> bool:
        """Assess if recent price action shows clear structure."""
        if len(recent_data) < 5:
            return False
            
        # Check for trending vs ranging conditions
        closes = recent_data['Close'].values
        
        # Calculate trend consistency
        price_changes = np.diff(closes)
        positive_moves = np.sum(price_changes > 0)
        negative_moves = np.sum(price_changes < 0)
        
        # Clear trend if 70% of moves in same direction
        trend_clarity = max(positive_moves, negative_moves) / len(price_changes) >= 0.7
        
        # Check for clean breakouts (no excessive wicks)
        wick_ratio = self._calculate_average_wick_ratio(recent_data)
        clean_structure = wick_ratio < 0.3  # Less than 30% wick on average
        
        return trend_clarity and clean_structure
    
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
    
    def _check_for_conflicting_signals(self, current_bar: pd.Series, historical_data: pd.DataFrame) -> bool:
        """Check for conflicting technical signals."""
        # Simple conflicting signal detection
        # Check if price is at a major resistance/support without clear break
        
        current_price = current_bar['Close']
        
        # Check recent volatility
        if len(historical_data) >= 10:
            recent_closes = historical_data['Close'].tail(10).values
            volatility = np.std(recent_closes) / np.mean(recent_closes)
            
            # High volatility might indicate conflicting forces
            if volatility > 0.02:  # 2% volatility threshold
                return False
                
        return True
    
    def _calculate_trap_confidence(
        self, 
        induction_detected: bool, 
        liquidity_zones: List[LiquidityZone], 
        distance_to_liquidity: float,
        safe_entry_exists: bool
    ) -> float:
        """Calculate confidence score for trap signal."""
        confidence = 0.0
        
        # Base confidence from induction detection
        if induction_detected:
            confidence += 0.3
            
        # Confidence from liquidity zone strength
        if liquidity_zones:
            avg_strength = np.mean([zone.strength for zone in liquidity_zones])
            confidence += min(avg_strength / 5.0, 0.3)  # Max 0.3 from strength
            
        # Confidence from distance (closer is better)
        if distance_to_liquidity <= self.config.max_distance_to_liquidity:
            distance_score = 1.0 - (distance_to_liquidity / self.config.max_distance_to_liquidity)
            confidence += distance_score * 0.2
            
        # Bonus for safe entry
        if safe_entry_exists:
            confidence += 0.2
            
        return min(confidence, 1.0)
    
    def _assess_risk_level(self, confidence: float, distance_to_liquidity: float, liquidity_zones: List[LiquidityZone]) -> RiskLevel:
        """Assess risk level for the trap trade."""
        if confidence >= 0.8 and distance_to_liquidity <= self.config.max_distance_to_liquidity * 0.5:
            return RiskLevel.LOW
        elif confidence >= 0.6 and distance_to_liquidity <= self.config.max_distance_to_liquidity:
            return RiskLevel.MEDIUM
        elif confidence >= 0.4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def _calculate_optimal_entry_price(
        self, 
        current_bar: pd.Series, 
        trap_type: TrapType, 
        liquidity_zones: List[LiquidityZone]
    ) -> float:
        """Calculate optimal entry price for the trap trade."""
        current_price = current_bar['Close']
        
        # Find nearest liquidity zone in trap direction
        if trap_type == TrapType.LIQUIDITY_ABOVE:
            # Look for entry below current price, targeting liquidity above
            relevant_zones = [zone for zone in liquidity_zones if zone.price > current_price]
        elif trap_type == TrapType.LIQUIDITY_BELOW:
            # Look for entry above current price, targeting liquidity below  
            relevant_zones = [zone for zone in liquidity_zones if zone.price < current_price]
        else:
            # For double traps or induction traps, use current price
            return current_price
            
        if not relevant_zones:
            return current_price
            
        # Entry should be positioned to catch the trap move
        target_zone = min(relevant_zones, key=lambda z: abs(z.price - current_price))
        
        # Entry slightly away from current price towards the trap direction
        if trap_type == TrapType.LIQUIDITY_ABOVE:
            entry_price = current_price * 0.999  # Slightly below for long entry
        else:
            entry_price = current_price * 1.001  # Slightly above for short entry
            
        return entry_price