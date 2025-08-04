"""
Configuration management utilities
"""

import json
import os
from typing import Dict, Any
from ..core.models import TradingConfig, TimeFrame


def load_config_from_file(config_path: str) -> TradingConfig:
    """
    Load trading configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        TradingConfig object
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        
    # Extract trading configuration
    trading_config = config_data.get('trading', {})
    
    # Convert timeframe strings to TimeFrame enums
    timeframes_str = trading_config.get('timeframes_to_analyze', ['M15', 'H1', 'H4'])
    timeframes = [TimeFrame(tf) for tf in timeframes_str]
    
    # Create TradingConfig object
    config = TradingConfig(
        max_risk_per_trade=trading_config.get('max_risk_per_trade', 0.02),
        tp1_ratio=trading_config.get('tp1_ratio', 1.0),
        tp2_ratio=trading_config.get('tp2_ratio', 2.0),
        tp3_ratio=trading_config.get('tp3_ratio', 3.0),
        tp1_size_percent=trading_config.get('tp1_size_percent', 0.5),
        tp2_size_percent=trading_config.get('tp2_size_percent', 0.3),
        tp3_size_percent=trading_config.get('tp3_size_percent', 0.2),
        trailing_stop_distance=trading_config.get('trailing_stop_distance', 0.5),
        min_trap_confidence=trading_config.get('min_trap_confidence', 0.7),
        min_entry_confidence=trading_config.get('min_entry_confidence', 0.8),
        max_distance_to_liquidity=trading_config.get('max_distance_to_liquidity', 0.002),
        timeframes_to_analyze=timeframes
    )
    
    return config


def save_config_to_file(config: TradingConfig, config_path: str):
    """
    Save trading configuration to JSON file.
    
    Args:
        config: TradingConfig object
        config_path: Path to save configuration
    """
    config_data = {
        'trading': {
            'max_risk_per_trade': config.max_risk_per_trade,
            'tp1_ratio': config.tp1_ratio,
            'tp2_ratio': config.tp2_ratio,
            'tp3_ratio': config.tp3_ratio,
            'tp1_size_percent': config.tp1_size_percent,
            'tp2_size_percent': config.tp2_size_percent,
            'tp3_size_percent': config.tp3_size_percent,
            'trailing_stop_distance': config.trailing_stop_distance,
            'min_trap_confidence': config.min_trap_confidence,
            'min_entry_confidence': config.min_entry_confidence,
            'max_distance_to_liquidity': config.max_distance_to_liquidity,
            'timeframes_to_analyze': [tf.value for tf in config.timeframes_to_analyze]
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)


def get_default_config() -> TradingConfig:
    """Get default trading configuration."""
    return TradingConfig()


def merge_configs(base_config: TradingConfig, override_config: Dict[str, Any]) -> TradingConfig:
    """
    Merge configuration overrides with base configuration.
    
    Args:
        base_config: Base TradingConfig
        override_config: Dict of configuration overrides
        
    Returns:
        Merged TradingConfig
    """
    # Convert base config to dict
    config_dict = base_config.__dict__.copy()
    
    # Apply overrides
    for key, value in override_config.items():
        if hasattr(base_config, key):
            if key == 'timeframes_to_analyze' and isinstance(value, list):
                # Convert string timeframes to enums
                config_dict[key] = [TimeFrame(tf) if isinstance(tf, str) else tf for tf in value]
            else:
                config_dict[key] = value
                
    # Create new config object
    return TradingConfig(**config_dict)