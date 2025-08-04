"""
Configuration settings for the Meta Trading Bot
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TimeframeConfig:
    """Configuration for timeframe analysis"""
    higher_timeframes: List[str]
    lower_timeframes: List[str]
    context_period: int = 200  # Number of candles for context analysis

@dataclass
class TradingConfig:
    """Main trading configuration"""
    # Timeframe settings
    timeframes: TimeframeConfig
    
    # Risk management
    max_risk_per_trade: float = 0.02  # 2% max risk per trade
    max_daily_loss: float = 0.05     # 5% max daily loss
    
    # Technical analysis settings
    fractal_period: int = 5           # Period for fractal identification
    liquidity_zone_buffer: float = 0.001  # 0.1% buffer for liquidity zones
    choch_confirmation_period: int = 3     # Candles for CHOCH confirmation
    
    # False break detection
    false_break_threshold: float = 0.002   # 0.2% threshold for false breaks
    momentum_confirmation_period: int = 5   # Candles for momentum confirmation
    
    # Adaptive settings
    trap_detection_enabled: bool = True
    auto_reassessment_interval: int = 10   # Candles between reassessments

# Default configuration
DEFAULT_CONFIG = TradingConfig(
    timeframes=TimeframeConfig(
        higher_timeframes=['1d', '4h', '1h'],
        lower_timeframes=['15m', '5m', '1m'],
        context_period=200
    )
)

def get_config() -> TradingConfig:
    """Get trading configuration"""
    return DEFAULT_CONFIG

def update_config(**kwargs) -> TradingConfig:
    """Update configuration with new values"""
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config