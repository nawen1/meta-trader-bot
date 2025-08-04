"""
Configuration management for the BTCUSD trading bot.
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class TradingConfig:
    """Configuration class for trading parameters."""
    
    # API Configuration
    exchange_api_key: str
    exchange_secret: str
    exchange_passphrase: Optional[str]
    exchange_sandbox: bool
    
    # Trading Parameters
    symbol: str
    base_currency: str
    quote_currency: str
    
    # Risk Management
    position_size_percent: float
    max_daily_loss_percent: float
    trailing_stop_percent: float
    
    # Take Profit Levels
    tp1_percent: float
    tp2_percent: float
    tp3_percent: float
    
    # Position Allocation
    tp1_allocation: int
    tp2_allocation: int
    tp3_allocation: int
    
    # Entry Strategy
    min_structure_break_strength: float
    clean_zone_buffer_percent: float
    liquidity_sweep_confirmation_bars: int
    
    # Real-time Parameters
    update_interval_seconds: int
    volume_analysis_period: int
    price_action_sensitivity: float


def load_config() -> TradingConfig:
    """Load configuration from environment variables."""
    load_dotenv()
    
    return TradingConfig(
        # API Configuration
        exchange_api_key=os.getenv('EXCHANGE_API_KEY', ''),
        exchange_secret=os.getenv('EXCHANGE_SECRET', ''),
        exchange_passphrase=os.getenv('EXCHANGE_PASSPHRASE'),
        exchange_sandbox=os.getenv('EXCHANGE_SANDBOX', 'true').lower() == 'true',
        
        # Trading Parameters
        symbol=os.getenv('SYMBOL', 'BTC/USDT'),
        base_currency=os.getenv('BASE_CURRENCY', 'USDT'),
        quote_currency=os.getenv('QUOTE_CURRENCY', 'BTC'),
        
        # Risk Management
        position_size_percent=float(os.getenv('POSITION_SIZE_PERCENT', '2.0')),
        max_daily_loss_percent=float(os.getenv('MAX_DAILY_LOSS_PERCENT', '5.0')),
        trailing_stop_percent=float(os.getenv('TRAILING_STOP_PERCENT', '1.5')),
        
        # Take Profit Levels
        tp1_percent=float(os.getenv('TP1_PERCENT', '1.0')),
        tp2_percent=float(os.getenv('TP2_PERCENT', '2.5')),
        tp3_percent=float(os.getenv('TP3_PERCENT', '5.0')),
        
        # Position Allocation
        tp1_allocation=int(os.getenv('TP1_ALLOCATION', '30')),
        tp2_allocation=int(os.getenv('TP2_ALLOCATION', '40')),
        tp3_allocation=int(os.getenv('TP3_ALLOCATION', '30')),
        
        # Entry Strategy
        min_structure_break_strength=float(os.getenv('MIN_STRUCTURE_BREAK_STRENGTH', '0.7')),
        clean_zone_buffer_percent=float(os.getenv('CLEAN_ZONE_BUFFER_PERCENT', '0.2')),
        liquidity_sweep_confirmation_bars=int(os.getenv('LIQUIDITY_SWEEP_CONFIRMATION_BARS', '3')),
        
        # Real-time Parameters
        update_interval_seconds=int(os.getenv('UPDATE_INTERVAL_SECONDS', '5')),
        volume_analysis_period=int(os.getenv('VOLUME_ANALYSIS_PERIOD', '20')),
        price_action_sensitivity=float(os.getenv('PRICE_ACTION_SENSITIVITY', '0.8'))
    )


def validate_config(config: TradingConfig) -> bool:
    """Validate configuration parameters."""
    # Check allocation sums to 100
    total_allocation = config.tp1_allocation + config.tp2_allocation + config.tp3_allocation
    if total_allocation != 100:
        raise ValueError(f"TP allocations must sum to 100, got {total_allocation}")
    
    # Check positive percentages
    if config.position_size_percent <= 0:
        raise ValueError("Position size percent must be positive")
    
    if config.max_daily_loss_percent <= 0:
        raise ValueError("Max daily loss percent must be positive")
    
    # Check TP levels are in ascending order
    if not (config.tp1_percent < config.tp2_percent < config.tp3_percent):
        raise ValueError("Take profit levels must be in ascending order")
    
    return True