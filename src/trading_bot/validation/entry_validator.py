"""
Strict validation logic for trade entries to ensure high-probability setups.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from ..analysis.market_structure import (
    StructureBreak, LiquidityPoint, CleanZone, TrendDirection, StructureBreakType
)


class ValidationResult(Enum):
    """Entry validation results."""
    VALID = "valid"
    INVALID_NO_STRUCTURE_BREAK = "invalid_no_structure_break"
    INVALID_NO_LIQUIDITY_SWEEP = "invalid_no_liquidity_sweep"
    INVALID_NO_CLEAN_ZONE = "invalid_no_clean_zone"
    INVALID_TREND_MISMATCH = "invalid_trend_mismatch"
    INVALID_INSUFFICIENT_VOLUME = "invalid_insufficient_volume"
    INVALID_RISK_TOO_HIGH = "invalid_risk_too_high"


@dataclass
class EntrySignal:
    """Represents a potential entry signal."""
    timestamp: pd.Timestamp
    price: float
    direction: TrendDirection
    structure_break: Optional[StructureBreak]
    liquidity_points: List[LiquidityPoint]
    clean_zone: Optional[CleanZone]
    validation_result: ValidationResult
    confidence_score: float
    risk_reward_ratio: float


@dataclass
class LiquiditySweepEvent:
    """Represents a liquidity sweep event."""
    timestamp: pd.Timestamp
    price: float
    liquidity_point: LiquidityPoint
    sweep_strength: float
    confirmed: bool


class EntryValidator:
    """Validates entry points using strict criteria."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.recent_sweeps: List[LiquiditySweepEvent] = []
    
    def validate_entry(self, df: pd.DataFrame, structure_breaks: List[StructureBreak],
                      liquidity_points: List[LiquidityPoint], clean_zones: List[CleanZone],
                      current_price: float, timestamp: pd.Timestamp) -> Optional[EntrySignal]:
        """
        Validate a potential entry point using strict criteria.
        
        Args:
            df: OHLCV data
            structure_breaks: Recent structure breaks
            liquidity_points: Identified liquidity points
            clean_zones: Clean zones for entry
            current_price: Current market price
            timestamp: Current timestamp
            
        Returns:
            EntrySignal if valid, None otherwise
        """
        # Step 1: Check for recent structure break
        recent_break = self._find_recent_structure_break(structure_breaks, timestamp)
        if not recent_break:
            self.logger.debug("No recent structure break found")
            return self._create_invalid_signal(
                timestamp, current_price, ValidationResult.INVALID_NO_STRUCTURE_BREAK
            )
        
        # Step 2: Verify liquidity sweep occurred
        sweep_confirmed = self._check_liquidity_sweep(
            df, liquidity_points, recent_break, timestamp
        )
        if not sweep_confirmed:
            self.logger.debug("No liquidity sweep confirmed")
            return self._create_invalid_signal(
                timestamp, current_price, ValidationResult.INVALID_NO_LIQUIDITY_SWEEP
            )
        
        # Step 3: Ensure we're in a clean zone
        active_clean_zone = self._find_active_clean_zone(clean_zones, current_price, timestamp)
        if not active_clean_zone:
            self.logger.debug("No active clean zone found")
            return self._create_invalid_signal(
                timestamp, current_price, ValidationResult.INVALID_NO_CLEAN_ZONE
            )
        
        # Step 4: Validate trend continuation logic
        if not self._validate_trend_continuation(df, recent_break, current_price):
            self.logger.debug("Trend continuation validation failed")
            return self._create_invalid_signal(
                timestamp, current_price, ValidationResult.INVALID_TREND_MISMATCH
            )
        
        # Step 5: Check volume confirmation
        if not self._validate_volume(df, timestamp):
            self.logger.debug("Volume validation failed")
            return self._create_invalid_signal(
                timestamp, current_price, ValidationResult.INVALID_INSUFFICIENT_VOLUME
            )
        
        # Step 6: Calculate confidence and risk/reward
        confidence_score = self._calculate_confidence_score(
            recent_break, active_clean_zone, df, timestamp
        )
        
        risk_reward_ratio = self._calculate_risk_reward_ratio(
            current_price, recent_break.direction, active_clean_zone
        )
        
        # Step 7: Final risk validation
        if risk_reward_ratio < 2.0:  # Minimum 2:1 risk/reward
            self.logger.debug(f"Risk/reward ratio too low: {risk_reward_ratio}")
            return self._create_invalid_signal(
                timestamp, current_price, ValidationResult.INVALID_RISK_TOO_HIGH
            )
        
        # Create valid entry signal
        return EntrySignal(
            timestamp=timestamp,
            price=current_price,
            direction=recent_break.direction,
            structure_break=recent_break,
            liquidity_points=self._get_relevant_liquidity_points(liquidity_points, recent_break),
            clean_zone=active_clean_zone,
            validation_result=ValidationResult.VALID,
            confidence_score=confidence_score,
            risk_reward_ratio=risk_reward_ratio
        )
    
    def check_liquidity_sweeps(self, df: pd.DataFrame, liquidity_points: List[LiquidityPoint],
                              timestamp: pd.Timestamp) -> List[LiquiditySweepEvent]:
        """
        Check for recent liquidity sweep events.
        
        Args:
            df: OHLCV data
            liquidity_points: Liquidity points to check
            timestamp: Current timestamp
            
        Returns:
            List of recent sweep events
        """
        new_sweeps = []
        current_data = df[df.index <= timestamp].tail(self.config.liquidity_sweep_confirmation_bars)
        
        if len(current_data) < self.config.liquidity_sweep_confirmation_bars:
            return new_sweeps
        
        for liq_point in liquidity_points:
            sweep_event = self._detect_liquidity_sweep(current_data, liq_point, timestamp)
            if sweep_event:
                new_sweeps.append(sweep_event)
                self.recent_sweeps.append(sweep_event)
        
        # Clean up old sweep events (keep only last 100)
        self.recent_sweeps = self.recent_sweeps[-100:]
        
        return new_sweeps
    
    def _find_recent_structure_break(self, structure_breaks: List[StructureBreak],
                                   timestamp: pd.Timestamp) -> Optional[StructureBreak]:
        """Find the most recent significant structure break."""
        # Look for breaks within the last 50 bars
        time_threshold = timestamp - pd.Timedelta(minutes=250)  # Assuming 5-min bars
        
        recent_breaks = [
            sb for sb in structure_breaks
            if sb.timestamp >= time_threshold and sb.break_type == StructureBreakType.BOSS
        ]
        
        if not recent_breaks:
            return None
        
        # Return the most recent and strongest break
        return max(recent_breaks, key=lambda x: (x.timestamp, x.strength))
    
    def _check_liquidity_sweep(self, df: pd.DataFrame, liquidity_points: List[LiquidityPoint],
                              structure_break: StructureBreak, timestamp: pd.Timestamp) -> bool:
        """Check if liquidity was swept before the structure break."""
        # Look for sweeps that occurred before the structure break
        sweep_window_start = structure_break.timestamp - pd.Timedelta(minutes=100)
        sweep_window_end = structure_break.timestamp
        
        relevant_sweeps = [
            sweep for sweep in self.recent_sweeps
            if sweep_window_start <= sweep.timestamp <= sweep_window_end
        ]
        
        if not relevant_sweeps:
            # Check for immediate sweeps in current data
            recent_data = df[df.index <= timestamp].tail(20)
            for liq_point in liquidity_points:
                if self._detect_liquidity_sweep(recent_data, liq_point, timestamp):
                    return True
            return False
        
        return len(relevant_sweeps) > 0
    
    def _find_active_clean_zone(self, clean_zones: List[CleanZone], current_price: float,
                               timestamp: pd.Timestamp) -> Optional[CleanZone]:
        """Find clean zone that contains the current price."""
        for zone in clean_zones:
            # Check if current price is within the clean zone
            if zone.lower_bound <= current_price <= zone.upper_bound:
                # Prefer more recent zones
                time_diff = timestamp - zone.timestamp
                if time_diff.total_seconds() / 60 <= 500:  # Within last 500 minutes
                    return zone
        
        return None
    
    def _validate_trend_continuation(self, df: pd.DataFrame, structure_break: StructureBreak,
                                   current_price: float) -> bool:
        """Validate that the entry aligns with trend continuation logic."""
        # Get recent price action after the structure break
        post_break_data = df[df.index > structure_break.timestamp].tail(20)
        
        if post_break_data.empty:
            return False
        
        # For bullish breaks, expect price to stay above the break level
        if structure_break.direction == TrendDirection.BULLISH:
            return current_price > structure_break.price
        
        # For bearish breaks, expect price to stay below the break level
        elif structure_break.direction == TrendDirection.BEARISH:
            return current_price < structure_break.price
        
        return False
    
    def _validate_volume(self, df: pd.DataFrame, timestamp: pd.Timestamp) -> bool:
        """Validate volume supports the entry."""
        recent_data = df[df.index <= timestamp].tail(self.config.volume_analysis_period)
        
        if len(recent_data) < 5:
            return False
        
        current_volume = recent_data.iloc[-1]['volume']
        avg_volume = recent_data['volume'].mean()
        
        # Require volume to be at least 80% of average
        return current_volume >= (avg_volume * 0.8)
    
    def _calculate_confidence_score(self, structure_break: StructureBreak, clean_zone: CleanZone,
                                   df: pd.DataFrame, timestamp: pd.Timestamp) -> float:
        """Calculate confidence score for the entry."""
        score = 0.0
        
        # Structure break strength (30% weight)
        score += structure_break.strength * 0.3
        
        # Clean zone quality (25% weight)
        score += clean_zone.quality_score * 0.25
        
        # Volume confirmation (20% weight)
        recent_data = df[df.index <= timestamp].tail(5)
        volume_ratio = recent_data.iloc[-1]['volume'] / recent_data['volume'].mean()
        volume_score = min(volume_ratio, 2.0) / 2.0
        score += volume_score * 0.2
        
        # Trend alignment (25% weight)
        trend_score = self._calculate_trend_alignment_score(df, timestamp, structure_break.direction)
        score += trend_score * 0.25
        
        return min(score, 1.0)
    
    def _calculate_risk_reward_ratio(self, entry_price: float, direction: TrendDirection,
                                   clean_zone: CleanZone) -> float:
        """Calculate risk/reward ratio for the entry."""
        # Define stop loss based on clean zone
        if direction == TrendDirection.BULLISH:
            stop_loss = clean_zone.lower_bound - (clean_zone.upper_bound - clean_zone.lower_bound) * 0.1
            take_profit = entry_price * (1 + self.config.tp1_percent / 100)
        else:
            stop_loss = clean_zone.upper_bound + (clean_zone.upper_bound - clean_zone.lower_bound) * 0.1
            take_profit = entry_price * (1 - self.config.tp1_percent / 100)
        
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return 0.0
        
        return reward / risk
    
    def _calculate_trend_alignment_score(self, df: pd.DataFrame, timestamp: pd.Timestamp,
                                       direction: TrendDirection) -> float:
        """Calculate how well the entry aligns with the trend."""
        recent_data = df[df.index <= timestamp].tail(20)
        
        if len(recent_data) < 10:
            return 0.5
        
        # Simple trend calculation using price direction
        price_changes = recent_data['close'].pct_change().dropna()
        
        if direction == TrendDirection.BULLISH:
            positive_changes = (price_changes > 0).sum()
            return positive_changes / len(price_changes)
        else:
            negative_changes = (price_changes < 0).sum()
            return negative_changes / len(price_changes)
    
    def _detect_liquidity_sweep(self, df: pd.DataFrame, liquidity_point: LiquidityPoint,
                               timestamp: pd.Timestamp) -> Optional[LiquiditySweepEvent]:
        """Detect if a liquidity point was swept."""
        tolerance = 0.001  # 0.1% tolerance
        
        for _, row in df.iterrows():
            if liquidity_point.point_type in ['high', 'equal_highs']:
                # Check if high was swept (price went above)
                if row['high'] > liquidity_point.price * (1 + tolerance):
                    sweep_strength = (row['high'] - liquidity_point.price) / liquidity_point.price
                    return LiquiditySweepEvent(
                        timestamp=row.name,
                        price=row['high'],
                        liquidity_point=liquidity_point,
                        sweep_strength=sweep_strength,
                        confirmed=True
                    )
            
            elif liquidity_point.point_type in ['low', 'equal_lows']:
                # Check if low was swept (price went below)
                if row['low'] < liquidity_point.price * (1 - tolerance):
                    sweep_strength = (liquidity_point.price - row['low']) / liquidity_point.price
                    return LiquiditySweepEvent(
                        timestamp=row.name,
                        price=row['low'],
                        liquidity_point=liquidity_point,
                        sweep_strength=sweep_strength,
                        confirmed=True
                    )
        
        return None
    
    def _get_relevant_liquidity_points(self, liquidity_points: List[LiquidityPoint],
                                     structure_break: StructureBreak) -> List[LiquidityPoint]:
        """Get liquidity points relevant to the structure break."""
        relevant_points = []
        
        for liq_point in liquidity_points:
            # Include points that align with the break direction
            if structure_break.direction == TrendDirection.BULLISH:
                if liq_point.point_type in ['high', 'equal_highs'] and liq_point.price < structure_break.price:
                    relevant_points.append(liq_point)
            else:
                if liq_point.point_type in ['low', 'equal_lows'] and liq_point.price > structure_break.price:
                    relevant_points.append(liq_point)
        
        return relevant_points
    
    def _create_invalid_signal(self, timestamp: pd.Timestamp, price: float,
                              validation_result: ValidationResult) -> EntrySignal:
        """Create an invalid entry signal."""
        return EntrySignal(
            timestamp=timestamp,
            price=price,
            direction=TrendDirection.SIDEWAYS,
            structure_break=None,
            liquidity_points=[],
            clean_zone=None,
            validation_result=validation_result,
            confidence_score=0.0,
            risk_reward_ratio=0.0
        )