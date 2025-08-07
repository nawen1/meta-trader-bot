"""
Example usage of the Meta Trader Bot.
Demonstrates multi-timeframe analysis with sample data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.meta_trader_bot import MetaTraderBot


def generate_sample_data(timeframe: str, num_candles: int = 200) -> pd.DataFrame:
    """
    Generate sample OHLCV data for testing.
    """
    # Create datetime index based on timeframe
    if timeframe == 'D1':
        freq = 'D'
    elif timeframe == 'H4':
        freq = '4H'
    elif timeframe == 'H1':
        freq = 'H'
    elif timeframe == 'M15':
        freq = '15T'
    elif timeframe == 'M5':
        freq = '5T'
    else:
        freq = 'H'
    
    # Generate dates
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=num_candles, freq=freq)
    
    # Generate price data with realistic movements
    np.random.seed(42)  # For reproducible results
    
    # Start with a base price
    base_price = 1.2000 if 'EUR' in timeframe else 50000  # EURUSD or BTCUSD-like
    
    # Generate returns with some trend
    trend = 0.0001 if timeframe in ['D1', 'H4'] else 0.00005
    volatility = 0.01 if timeframe in ['D1', 'H4'] else 0.005
    
    returns = np.random.normal(trend, volatility, num_candles)
    
    # Create price series
    prices = []
    current_price = base_price
    
    for ret in returns:
        current_price *= (1 + ret)
        prices.append(current_price)
    
    # Generate OHLC from price series
    data = []
    for i, close in enumerate(prices):
        if i == 0:
            open_price = base_price
        else:
            open_price = prices[i-1]
        
        # Generate high and low with some randomness
        high_factor = 1 + abs(np.random.normal(0, 0.002))
        low_factor = 1 - abs(np.random.normal(0, 0.002))
        
        high = max(open_price, close) * high_factor
        low = min(open_price, close) * low_factor
        
        # Generate volume
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


def run_bot_demo():
    """
    Run a complete demonstration of the MetaTraderBot.
    """
    print("=" * 60)
    print("META TRADER BOT - MULTI-TIMEFRAME ANALYSIS DEMO")
    print("=" * 60)
    
    # Initialize the bot
    print("\n1. Initializing MetaTraderBot...")
    bot = MetaTraderBot()
    
    # Generate sample data for multiple timeframes
    print("\n2. Generating sample market data...")
    timeframes = ['D1', 'H4', 'H1', 'M15', 'M5']
    market_data = {}
    
    for tf in timeframes:
        candles = 100 if tf in ['D1', 'H4'] else 200
        market_data[tf] = generate_sample_data(tf, candles)
        print(f"   Generated {len(market_data[tf])} candles for {tf}")
    
    # Perform comprehensive market analysis
    print("\n3. Performing comprehensive market analysis...")
    analysis = bot.analyze_market(market_data)
    
    # Display analysis results
    print("\n4. Analysis Results:")
    print("-" * 40)
    
    # Market context
    market_context = analysis.get('market_context', {})
    print(f"Overall Bias: {market_context.get('overall_bias', 'Unknown')}")
    print(f"Trend Strength: {market_context.get('trend_strength', 0):.2f}")
    
    alignment = market_context.get('multi_tf_alignment', {})
    print(f"Multi-TF Alignment: {alignment.get('aligned', False)} ({alignment.get('alignment_score', 0):.1%})")
    
    # Timeframe hierarchy
    tf_hierarchy = analysis.get('timeframe_hierarchy', {})
    print(f"Higher TF Bias: {tf_hierarchy.get('higher_tf_bias', 'Unknown')}")
    print(f"Aligned Timeframes: {tf_hierarchy.get('entry_timeframes', [])}")
    print(f"Conflicting Signals: {len(tf_hierarchy.get('conflicting_signals', []))}")
    
    # Trading recommendation
    recommendation = analysis.get('trading_recommendation', {})
    print(f"\nTrading Recommendation: {recommendation.get('recommendation', 'Unknown')}")
    print(f"Reason: {recommendation.get('reason', 'No reason provided')}")
    print(f"Confidence: {recommendation.get('confidence', 0):.1%}")
    
    # Key zones
    key_zones = analysis.get('key_zones', {})
    print(f"\nKey Zones Identified:")
    print(f"  - Liquidity Zones: {len(key_zones.get('liquidity_zones', []))}")
    print(f"  - Structure Levels: {len(key_zones.get('structure_levels', []))}")
    print(f"  - Support/Resistance: {len(key_zones.get('support_resistance', []))}")
    print(f"  - Confluence Areas: {len(key_zones.get('confluence_areas', []))}")
    
    # Generate entry signals for different timeframes
    print("\n5. Generating Entry Signals...")
    print("-" * 40)
    
    entry_timeframes = ['H1', 'M15']
    
    for entry_tf in entry_timeframes:
        print(f"\nGenerating signals for {entry_tf}:")
        signals = bot.generate_entry_signals(market_data, entry_tf)
        
        if signals.get('entry_allowed', False):
            signal_list = signals.get('signals', [])
            print(f"  Entry Allowed: Yes")
            print(f"  Valid Signals: {len(signal_list)}")
            
            for i, signal in enumerate(signal_list[:3], 1):  # Show first 3 signals
                print(f"    Signal {i}:")
                print(f"      Type: {signal.get('type', 'Unknown')}")
                print(f"      Direction: {signal.get('direction', 'Unknown')}")
                print(f"      Entry Price: {signal.get('entry_price', 0):.5f}")
                print(f"      Stop Loss: {signal.get('stop_loss', 0):.5f}")
                print(f"      Take Profit: {signal.get('take_profit', 0):.5f}")
                print(f"      Risk/Reward: {signal.get('risk_reward_ratio', 0):.2f}")
                print(f"      TF Alignment: {signal.get('tf_alignment_score', 0):.1%}")
        else:
            print(f"  Entry Allowed: No")
            print(f"  Reason: {signals.get('reason', 'Unknown')}")
    
    # Display market summary
    print("\n6. Market Summary:")
    print("-" * 40)
    summary = bot.get_market_summary()
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Export analysis
    print("\n7. Exporting Analysis...")
    try:
        filename = bot.export_analysis()
        print(f"Analysis exported to: {filename}")
    except Exception as e:
        print(f"Export failed: {e}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
    return bot, analysis


def demonstrate_timeframe_hierarchy():
    """
    Demonstrate the timeframe hierarchy concept specifically.
    """
    print("\n" + "=" * 60)
    print("TIMEFRAME HIERARCHY DEMONSTRATION")
    print("=" * 60)
    
    bot = MetaTraderBot()
    
    # Show timeframe priorities
    print("\nTimeframe Priorities (Higher = More Important):")
    for tf in bot.tf_analyzer.timeframes:
        priority = bot.tf_analyzer.get_timeframe_priority(tf)
        print(f"  {tf}: Priority {priority}")
    
    # Demonstrate hierarchy relationships
    print("\nTimeframe Relationships:")
    test_tf = 'M15'
    higher_tfs = bot.tf_analyzer.get_higher_timeframes(test_tf)
    lower_tfs = bot.tf_analyzer.get_lower_timeframes(test_tf)
    
    print(f"For {test_tf}:")
    print(f"  Higher TFs: {higher_tfs}")
    print(f"  Lower TFs: {lower_tfs}")
    
    # Show how entries must align with higher TFs
    print(f"\nKey Principle: Entries on {test_tf} must align with context from {higher_tfs}")
    print("This ensures that trades follow the 'smart money' flow from institutional timeframes.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run the complete demo
    bot, analysis = run_bot_demo()
    
    # Demonstrate timeframe hierarchy
    demonstrate_timeframe_hierarchy()
    
    print("\nThe MetaTraderBot successfully implements multi-timeframe analysis")
    print("with strict hierarchy where higher timeframes always take precedence.")
    print("\nKey Features Demonstrated:")
    print("✓ Multi-timeframe market structure analysis")
    print("✓ Liquidity sweep detection")  
    print("✓ Change of Character (ChoCH) pattern recognition")
    print("✓ Support/resistance level identification")
    print("✓ Confluence zone detection")
    print("✓ Entry signal generation with TF alignment")
    print("✓ Risk management with stop/take profit calculation")
    print("✓ Strict adherence to higher timeframe context")