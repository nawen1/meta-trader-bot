"""
Configuration module for the multi-timeframe trading bot.
"""

# Timeframe priorities (higher values = higher priority)
TIMEFRAME_PRIORITY = {
    'D1': 5,    # Daily - highest priority
    'H4': 4,    # 4-hour
    'H1': 3,    # 1-hour  
    'M15': 2,   # 15-minute
    'M5': 1,    # 5-minute - lowest priority
}

# Timeframes ordered by priority (highest to lowest)
TIMEFRAMES_ORDERED = ['D1', 'H4', 'H1', 'M15', 'M5']

# Analysis configuration
LIQUIDITY_CONFIG = {
    'lookback_periods': 20,
    'min_volume_threshold': 1.5,  # Minimum volume multiplier for liquidity detection
}

MARKET_STRUCTURE_CONFIG = {
    'swing_detection_periods': 10,
    'choch_confirmation_periods': 3,
}

SUPPORT_RESISTANCE_CONFIG = {
    'touch_tolerance': 0.001,  # 0.1% tolerance for level touches
    'min_touches': 2,  # Minimum touches to confirm S/R level
    'lookback_periods': 50,
}

# Entry criteria
ENTRY_CONFIG = {
    'require_higher_tf_alignment': True,
    'min_confirmation_timeframes': 2,  # Minimum number of TFs that must align
    'risk_reward_ratio': 2.0,
}