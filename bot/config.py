"""
Configuration settings for the Meta Trading Bot
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskManagementConfig(BaseModel):
    """Risk management configuration"""
    max_risk_per_trade: float = Field(default=0.02, description="Maximum risk per trade (2%)")
    trailing_stop_enabled: bool = Field(default=True, description="Enable trailing stops")
    trailing_stop_distance: float = Field(default=0.005, description="Trailing stop distance (0.5%)")
    
    # Take Profit levels
    tp1_ratio: float = Field(default=1.0, description="TP1 risk-reward ratio")
    tp2_ratio: float = Field(default=2.0, description="TP2 risk-reward ratio")
    tp3_ratio: float = Field(default=3.0, description="TP3 risk-reward ratio")
    
    # Partial position closing
    tp1_close_percentage: float = Field(default=0.3, description="Close 30% at TP1")
    tp2_close_percentage: float = Field(default=0.5, description="Close 50% at TP2")
    tp3_close_percentage: float = Field(default=1.0, description="Close 100% at TP3")


class TrapIdentificationConfig(BaseModel):
    """Configuration for trap identification"""
    liquidity_threshold: float = Field(default=0.01, description="Minimum liquidity threshold (1%)")
    induction_confirmation_bars: int = Field(default=3, description="Bars needed to confirm induction")
    trap_validation_distance: float = Field(default=0.002, description="Distance to validate trap (0.2%)")
    min_trap_size: float = Field(default=0.005, description="Minimum trap size (0.5%)")


class AnalysisConfig(BaseModel):
    """Market analysis configuration"""
    higher_timeframes: List[str] = Field(default=["4h", "1d"], description="Higher timeframes for context")
    confirmation_timeframes: List[str] = Field(default=["15m", "1h"], description="Confirmation timeframes")
    lookback_periods: int = Field(default=100, description="Periods to look back for analysis")


class BotConfig(BaseModel):
    """Main bot configuration"""
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig)
    trap_identification: TrapIdentificationConfig = Field(default_factory=TrapIdentificationConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    
    # General settings
    min_entry_confidence: float = Field(default=0.75, description="Minimum confidence for entry (75%)")
    force_trades: bool = Field(default=False, description="Force trades even without clear setup")
    enable_trap_trading: bool = Field(default=True, description="Enable trading in traps")
    
    # Logging and monitoring
    log_level: str = Field(default="INFO", description="Logging level")
    enable_detailed_logging: bool = Field(default=True, description="Enable detailed logging")


# Default configuration instance
default_config = BotConfig()