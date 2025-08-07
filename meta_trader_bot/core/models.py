"""
Core data models for the trading bot
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime


class TrapType(Enum):
    """Types of traps that can be identified"""
    LIQUIDITY_ABOVE = "liquidity_above"
    LIQUIDITY_BELOW = "liquidity_below"
    DOUBLE_TRAP = "double_trap"
    INDUCTION_TRAP = "induction_trap"


class RiskLevel(Enum):
    """Risk levels for trade entries"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class TradeDirection(Enum):
    """Trade direction"""
    LONG = "long"
    SHORT = "short"


class EntryModel(Enum):
    """Entry validation models"""
    MODEL_1 = "model_1"
    MODEL_2 = "model_2"
    MODEL_3 = "model_3"


class TimeFrame(Enum):
    """Trading timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


@dataclass
class LiquidityZone:
    """Represents a liquidity zone in the market"""
    price: float
    volume: float
    strength: float
    timestamp: datetime
    zone_type: str  # 'support', 'resistance', 'neutral'


@dataclass
class TrapSignal:
    """Signal indicating a potential trap"""
    trap_type: TrapType
    entry_price: Optional[float]
    confidence: float
    risk_level: RiskLevel
    liquidity_zones: List[LiquidityZone]
    safe_entry_exists: bool
    distance_to_liquidity: float
    timestamp: datetime


@dataclass
class BossStructure:
    """Represents a Boss structure in the market"""
    high_point: float
    low_point: float
    strength: float
    timeframe: TimeFrame
    formation_time: datetime
    is_valid: bool


@dataclass
class EntrySignal:
    """Signal for trade entry validation"""
    price: float
    direction: TradeDirection
    model_alignment: EntryModel
    boss_structure: Optional[BossStructure]
    liquid_points: List[float]
    confidence: float
    clean_zone: bool
    timestamp: datetime


@dataclass
class TradePosition:
    """Represents an active trading position"""
    entry_price: float
    direction: TradeDirection
    size: float
    tp1_price: float
    tp2_price: float
    tp3_price: float
    stop_loss: float
    trailing_stop: Optional[float]
    entry_time: datetime
    is_trap_trade: bool


@dataclass
class MarketStructure:
    """Represents overall market structure analysis"""
    higher_timeframe_trend: TradeDirection
    clean_zones: List[tuple]  # [(price_low, price_high), ...]
    key_levels: List[float]
    structure_strength: float
    last_updated: datetime


@dataclass
class TradingConfig:
    """Configuration for trading parameters"""
    max_risk_per_trade: float = 0.02  # 2%
    tp1_ratio: float = 1.0  # 1:1 risk/reward
    tp2_ratio: float = 2.0  # 1:2 risk/reward  
    tp3_ratio: float = 3.0  # 1:3 risk/reward
    tp1_size_percent: float = 0.5  # 50% of position at TP1
    tp2_size_percent: float = 0.3  # 30% of position at TP2
    tp3_size_percent: float = 0.2  # 20% of position at TP3
    trailing_stop_distance: float = 0.5  # % for trailing stop
    min_trap_confidence: float = 0.7  # Minimum confidence for trap trades
    min_entry_confidence: float = 0.8  # Minimum confidence for entries
    max_distance_to_liquidity: float = 0.002  # Max distance to liquidity (0.2%)
    timeframes_to_analyze: List[TimeFrame] = None
    
    def __post_init__(self):
        if self.timeframes_to_analyze is None:
            self.timeframes_to_analyze = [TimeFrame.M15, TimeFrame.H1, TimeFrame.H4]