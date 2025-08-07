"""
copilot/fix-7df13fe5-3188-47c1-8206-1d533e15e5fe
Configuration settings for the Meta Trading Bot

Configuration settings for the Meta Trading Bot - KAIZEN
Integrates settings from all merged PRs
main
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
copilot/fix-7df13fe5-3188-47c1-8206-1d533e15e5fe
    """Main trading configuration"""
    # Timeframe settings
    timeframes: TimeframeConfig
    
    # Risk management

    """Main trading configuration combining all PR features"""
    # Timeframe settings
    timeframes: TimeframeConfig
    
    # Risk management (from all PRs)
main
    max_risk_per_trade: float = 0.02  # 2% max risk per trade
    max_daily_loss: float = 0.05     # 5% max daily loss
    
    # Technical analysis settings
    fractal_period: int = 5           # Period for fractal identification
    liquidity_zone_buffer: float = 0.001  # 0.1% buffer for liquidity zones
    choch_confirmation_period: int = 3     # Candles for CHOCH confirmation
    
    # False break detection
    false_break_threshold: float = 0.002   # 0.2% threshold for false breaks
    momentum_confirmation_period: int = 5   # Candles for momentum confirmation
    
copilot/fix-7df13fe5-3188-47c1-8206-1d533e15e5fe
    # Adaptive settings
    trap_detection_enabled: bool = True
    auto_reassessment_interval: int = 10   # Candles between reassessments

# Default configuration

    # Trap detection (PR #4, #5)
    trap_detection_enabled: bool = True
    min_trap_confidence: float = 0.7
    min_entry_confidence: float = 0.8
    
    # BTCUSD specific settings (PR #6)
    structure_break_threshold: float = 0.7
    clean_zone_buffer: float = 0.002
    
    # Multi-timeframe prioritization (PR #7)
    strict_htf_priority: bool = True
    
    # Position management
    trailing_stop_distance: float = 0.015  # 1.5%
    tp1_ratio: float = 1.0
    tp2_ratio: float = 2.5
    tp3_ratio: float = 5.0
    
    # Adaptive settings
    auto_reassessment_interval: int = 10   # Candles between reassessments
    
    # MetaTrader 5 integration (PR #1)
    mt5_enabled: bool = False
    mt5_login: Optional[str] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None

# Default configuration integrating all PR features
main
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