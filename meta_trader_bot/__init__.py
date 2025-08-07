"""
Meta Trader Bot - Advanced Trading Bot with Trap Analysis
"""

__version__ = "1.0.0"
__author__ = "KAIZEN Trading Systems"

from .core.trading_bot import TradingBot
from .core.models import *

__all__ = [
    'TradingBot',
    'TrapSignal', 
    'EntrySignal',
    'RiskLevel',
    'TradePosition',
    'MarketStructure'
]