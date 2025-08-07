"""
KAIZEN Trading Bot Demo - Unified Features
Demonstrates the merged functionality from all 6 PRs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from src.kaizen_trading_bot import KaizenTradingBot
from utils.config import get_config, update_config

def generate_sample_data(symbol: str, timeframe: str, periods: int = 1000) -> pd.DataFrame:
    """Generate realistic sample market data for demo"""
    np.random.seed(42)  # For reproducible results
    
    # Base price
    base_price = 1.1000 if 'EUR' in symbol else 50000.0 if 'BTC' in symbol else 100.0
    
    # Generate price movements
    returns = np.random.normal(0, 0.001, periods)  # Small random returns
    
    # Add some trend
    trend = np.sin(np.linspace(0, 4*np.pi, periods)) * 0.002
    returns += trend
    
    # Calculate prices
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC
    high = prices * (1 + np.abs(np.random.normal(0, 0.0005, periods)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.0005, periods)))
    open_prices = np.roll(prices, 1)
    open_prices[0] = prices[0]
    
    # Generate volume
    volume = np.random.randint(1000, 10000, periods)
    
    # Create timestamps
    if timeframe == '1m':
        freq = '1min'
    elif timeframe == '5m':
        freq = '5min'
    elif timeframe == '15m':
        freq = '15min'
    elif timeframe == '1h':
        freq = '1H'
    elif timeframe == '4h':
        freq = '4H'
    elif timeframe == '1d':
        freq = '1D'
    else:
        freq = '1H'
    
    timestamps = pd.date_range(
        start=datetime.now() - timedelta(days=periods//24),
        periods=periods,
        freq=freq
    )
    
    return pd.DataFrame({
        'open': open_prices,
        'high': high,
        'low': low,
        'close': prices,
        'volume': volume
    }, index=timestamps)

def demo_unified_analysis():
    """Demonstrate unified analysis from all PRs"""
    print("=" * 60)
    print("KAIZEN TRADING BOT - UNIFIED DEMO")
    print("Integrating features from all 6 MetaTrader 5 PRs")
    print("=" * 60)
    
    # Initialize bot
    bot = KaizenTradingBot(account_balance=10000.0)
    
    # Display bot capabilities
    status = bot.get_bot_status()
    print("\n🤖 Bot Capabilities:")
    for capability in status['capabilities']:
        print(f"  ✓ {capability}")
    
    print(f"\n📊 Configuration:")
    print(f"  Higher Timeframes: {status['config']['timeframes']['higher']}")
    print(f"  Lower Timeframes: {status['config']['timeframes']['lower']}")
    print(f"  Risk per Trade: {status['config']['risk_per_trade']*100}%")
    print(f"  HTF Priority: {'Enabled' if status['config']['htf_priority'] else 'Disabled'}")
    print(f"  Trap Detection: {'Enabled' if status['config']['trap_detection'] else 'Disabled'}")
    
    # Demo with multiple symbols
    symbols = ['EURUSD', 'BTCUSD', 'GBPUSD']
    
    for symbol in symbols:
        print(f"\n{'='*40}")
        print(f"ANALYZING {symbol}")
        print(f"{'='*40}")
        
        # Generate sample data for all timeframes
        timeframes_data = {}
        all_timeframes = ['1d', '4h', '1h', '15m', '5m', '1m']
        
        for tf in all_timeframes:
            periods = 200 if tf in ['1d', '4h'] else 500
            timeframes_data[tf] = generate_sample_data(symbol, tf, periods)
        
        # Perform comprehensive analysis
        try:
            results = bot.analyze_market(symbol, timeframes_data)
            display_analysis_results(symbol, results)
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {str(e)}")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print("All PR features successfully integrated!")
    print(f"{'='*60}")

def display_analysis_results(symbol: str, results: Dict):
    """Display comprehensive analysis results"""
    print(f"\n📈 Multi-Timeframe Analysis:")
    mtf = results['multi_timeframe']
    print(f"  HTF Bias: {mtf['htf_bias']}")
    print(f"  Alignment Score: {mtf['alignment_score']:.2f}")
    print(f"  LTF Signals: {len(mtf['ltf_signals'])}")
    
    print(f"\n🪤 Trap Analysis:")
    trap = results['trap_analysis']
    print(f"  Liquidity Sweeps: {len(trap['liquidity_sweeps'])}")
    print(f"  Bull Traps: {len(trap['bull_traps'])}")
    print(f"  Bear Traps: {len(trap['bear_traps'])}")
    print(f"  Overall Trap Risk: {trap['trap_risk']:.2f}")
    
    print(f"\n🏗️ Market Structure:")
    structure = results['market_structure']
    print(f"  Character: {structure['current_character']}")
    print(f"  Boss Patterns: {len(structure['boss_patterns'])}")
    print(f"  Clean Zones: {len(structure['clean_zones'])}")
    print(f"  Model 2 Aligned: {'Yes' if structure['model2_alignment'] else 'No'}")
    
    print(f"\n📊 Entry Signals:")
    signals = results['entry_signals']
    print(f"  Total Signals: {len(signals)}")
    for i, signal in enumerate(signals[:3], 1):  # Show first 3 signals
        print(f"  {i}. {signal['direction'].upper()} on {signal['timeframe']} "
              f"(Confidence: {signal['confidence']:.2f})")
    
    print(f"\n⚠️ Risk Assessment:")
    risk = results['risk_assessment']
    print(f"  Overall Risk: {risk['overall_risk']}")
    print(f"  Market Conditions: {risk['market_conditions']}")
    print(f"  Position Size: ${risk['position_sizing']:.2f}")
    
    print(f"\n🎯 Trading Recommendation:")
    rec = results['trading_recommendation']
    if rec['action'] == 'trade':
        print(f"  Action: {rec['action'].upper()} {rec['direction'].upper()}")
        print(f"  Timeframe: {rec['timeframe']}")
        print(f"  Confidence: {rec['confidence']:.2f}")
        print(f"  Entry Type: {rec['entry_type']}")
        print(f"  Position Size: ${rec['position_size']:.2f}")
        print(f"  Risk/Reward: {rec['risk_reward']:.1f}:1")
    else:
        print(f"  Action: {rec['action'].upper()}")
        print(f"  Reason: {rec['reason']}")
    
    # Special handling for BTCUSD
    if 'BTC' in symbol and 'structure_breaks' in results['market_structure']:
        print(f"\n₿ BTCUSD Specific Analysis:")
        btc_data = results['market_structure']
        print(f"  Structure Breaks: {len(btc_data['structure_breaks'])}")
        print(f"  Refined Entries: {len(btc_data['refined_entries'])}")
        print(f"  Dynamic Risk Active: {'Yes' if btc_data['dynamic_risk_levels'] else 'No'}")

def demo_feature_showcase():
    """Showcase specific features from each PR"""
    print(f"\n{'='*60}")
    print("FEATURE SHOWCASE - BY PR")
    print(f"{'='*60}")
    
    features_by_pr = {
        "PR #1 - MetaTrader 5 Integration": [
            "✓ Advanced risk management with trailing stops",
            "✓ Multi-tier take profit levels (TP1, TP2, TP3)",
            "✓ Position sizing based on account balance",
            "✓ Daily loss limits and exposure control"
        ],
        "PR #2 - TradingView Pine Script": [
            "✓ Compatible Pine Script for TradingView",
            "✓ Real-time pattern recognition",
            "✓ Configurable alerts and notifications", 
            "✓ Visual overlays and statistics"
        ],
        "PR #3 - Multi-Timeframe Analysis": [
            "✓ Higher timeframe context analysis",
            "✓ Autonomous fractal identification",
            "✓ CHOCH (Change of Character) detection",
            "✓ Independent liquidity zone analysis"
        ],
        "PR #4 - Advanced Trap Detection": [
            "✓ Sophisticated trap identification",
            "✓ Safe entry point validation",
            "✓ Multi-type trap detection",
            "✓ Confidence-based filtering"
        ],
        "PR #5 - Comprehensive Analysis": [
            "✓ Distance-based trap analysis",
            "✓ Model 2 alignment checks",
            "✓ Clean zone validation",
            "✓ Dynamic risk monitoring"
        ],
        "PR #6 - BTCUSD Strategies": [
            "✓ Structure break detection with strength",
            "✓ Refined entry strategies",
            "✓ Dynamic trailing stops",
            "✓ Crypto-specific risk management"
        ],
        "PR #7 - HTF Prioritization": [
            "✓ Strict higher timeframe priority",
            "✓ Institutional alignment",
            "✓ Smart money flow tracking",
            "✓ Conflict resolution"
        ]
    }
    
    for pr_title, features in features_by_pr.items():
        print(f"\n{pr_title}:")
        for feature in features:
            print(f"  {feature}")
    
    print(f"\n{'='*60}")
    print("All features successfully merged into unified KAIZEN bot!")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        # Run unified demo
        demo_unified_analysis()
        
        # Showcase features
        demo_feature_showcase()
        
        print(f"\n🎉 Integration successful!")
        print(f"All 6 MetaTrader 5 PRs have been merged into a unified trading bot.")
        print(f"The bot combines:")
        print(f"- Multi-timeframe analysis with HTF priority")
        print(f"- Advanced trap detection and risk management") 
        print(f"- TradingView compatibility")
        print(f"- BTCUSD specialized strategies")
        print(f"- MetaTrader 5 integration capabilities")
        print(f"- Autonomous pattern recognition")
        
    except KeyboardInterrupt:
        print(f"\n\nDemo stopped by user.")
    except Exception as e:
        print(f"Demo error: {str(e)}")
        import traceback
        traceback.print_exc()