"""
Simple test to verify the bot works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
import numpy as np
from timeframe_analyzer import TimeframeAnalyzer
from meta_trader_bot import MetaTraderBot

def test_basic_functionality():
    """Test basic bot functionality."""
    print("Testing basic functionality...")
    
    # Test timeframe analyzer
    tf_analyzer = TimeframeAnalyzer()
    assert tf_analyzer.get_timeframe_priority('D1') == 5
    assert tf_analyzer.get_timeframe_priority('M5') == 1
    assert tf_analyzer.is_higher_timeframe('D1', 'H1')
    print("✓ Timeframe analyzer works correctly")
    
    # Test bot initialization
    bot = MetaTraderBot()
    print("✓ Bot initializes correctly")
    
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='h')
    np.random.seed(42)
    
    test_data = []
    base_price = 1.2000
    for i in range(100):
        price_change = np.random.normal(0, 0.001)
        base_price *= (1 + price_change)
        
        test_data.append({
            'open': base_price,
            'high': base_price * 1.001,
            'low': base_price * 0.999,
            'close': base_price,
            'volume': np.random.randint(1000, 5000)
        })
    
    df = pd.DataFrame(test_data, index=dates)
    market_data = {'H1': df, 'D1': df.resample('D').agg({
        'open': 'first', 
        'high': 'max', 
        'low': 'min', 
        'close': 'last', 
        'volume': 'sum'
    })}
    
    # Test market analysis
    analysis = bot.analyze_market(market_data)
    assert 'timeframe_hierarchy' in analysis
    assert 'market_context' in analysis
    print("✓ Market analysis works correctly")
    
    # Test signal generation
    signals = bot.generate_entry_signals(market_data, 'H1')
    assert 'entry_allowed' in signals
    assert 'signals' in signals
    print("✓ Signal generation works correctly")
    
    print("\n🎉 All tests passed!")

if __name__ == '__main__':
    test_basic_functionality()