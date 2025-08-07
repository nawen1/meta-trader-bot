#!/usr/bin/env python3
"""
CLI runner for the Meta Trading Bot
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import json

# Add the bot module to Python path
sys.path.insert(0, '/home/runner/work/meta-trader-bot/meta-trader-bot')

from bot.main import MetaTradingBot
from bot.config import BotConfig


def generate_sample_data(symbol: str = "EURUSD", days: int = 30) -> dict:
    """
    Generate sample OHLCV data for testing
    """
    # Create datetime index
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate different timeframes
    timeframes = {
        '1m': '1min',
        '5m': '5min', 
        '15m': '15min',
        '1h': '1H',
        '4h': '4H',
        '1d': '1D'
    }
    
    data = {}
    
    base_price = 1.1000  # Starting price for EURUSD
    
    for tf_name, tf_pandas in timeframes.items():
        # Calculate number of periods
        if tf_name == '1m':
            periods = days * 24 * 60
        elif tf_name == '5m':
            periods = days * 24 * 12
        elif tf_name == '15m':
            periods = days * 24 * 4
        elif tf_name == '1h':
            periods = days * 24
        elif tf_name == '4h':
            periods = days * 6
        else:  # 1d
            periods = days
        
        # Generate price data with some randomness
        np.random.seed(42)  # For reproducible results
        
        price_changes = np.random.normal(0, 0.001, periods)  # Small random changes
        
        # Add some trend
        trend = np.linspace(0, 0.02, periods)  # 2% uptrend over the period
        price_changes += trend / periods
        
        # Calculate prices
        closes = [base_price]
        for change in price_changes[:-1]:
            closes.append(closes[-1] * (1 + change))
        
        # Generate OHLC from closes
        data_rows = []
        for i, close in enumerate(closes):
            # Generate realistic OHLC
            volatility = np.random.uniform(0.0005, 0.002)  # Random volatility
            
            high = close * (1 + volatility * np.random.uniform(0.3, 1.0))
            low = close * (1 - volatility * np.random.uniform(0.3, 1.0))
            
            if i == 0:
                open_price = close
            else:
                open_price = closes[i-1] * (1 + np.random.normal(0, 0.0002))
            
            volume = np.random.uniform(1000, 10000)
            
            data_rows.append({
                'open': open_price,
                'high': max(open_price, close, high),
                'low': min(open_price, close, low),
                'close': close,
                'volume': volume
            })
        
        # Create DataFrame
        date_range = pd.date_range(start=start_date, periods=len(data_rows), freq=tf_pandas)
        df = pd.DataFrame(data_rows, index=date_range)
        data[tf_name] = df
    
    return data


def run_bot_demo():
    """Run a demo of the trading bot"""
    print("=== Meta Trading Bot Demo ===")
    print("Initializing bot...")
    
    # Create bot with default configuration
    bot = MetaTradingBot(account_balance=10000.0)
    
    # Generate sample market data
    print("Generating sample market data...")
    symbol = "EURUSD"
    market_data = generate_sample_data(symbol, days=30)
    
    # Current prices (last close prices)
    current_prices = {
        symbol: market_data['15m']['close'].iloc[-1]
    }
    
    print(f"Running trading cycle for {symbol}...")
    print(f"Current price: {current_prices[symbol]:.5f}")
    
    # Run trading cycle
    results = bot.run_trading_cycle(symbol, market_data, current_prices)
    
    # Display results
    print("\n=== Trading Cycle Results ===")
    print(f"Cycle duration: {results.get('cycle_duration_seconds', 0):.2f} seconds")
    print(f"Trap signals found: {results.get('market_analysis', {}).get('trap_signals_found', 0)}")
    print(f"Liquidity levels identified: {results.get('market_analysis', {}).get('liquidity_levels', 0)}")
    print(f"Signals generated: {results.get('signals_generated', 0)}")
    print(f"Positions executed: {results.get('positions_executed', 0)}")
    
    # Display market analysis
    market_analysis = results.get('market_analysis', {})
    print(f"\nMarket Analysis:")
    print(f"  Volatility: {market_analysis.get('market_volatility', 0):.3f}")
    print(f"  Trend strength: {market_analysis.get('trend_strength', 0):.3f}")
    
    htf_structures = market_analysis.get('higher_timeframe_structures', {})
    if htf_structures:
        print(f"  Higher timeframe structures:")
        for tf, structure in htf_structures.items():
            print(f"    {tf}: {structure.value if hasattr(structure, 'value') else structure}")
    
    # Display portfolio status
    portfolio = bot.get_portfolio_status()
    print(f"\n=== Portfolio Status ===")
    print(f"Account balance: ${portfolio.get('account_balance', 0):,.2f}")
    
    portfolio_risk = portfolio.get('portfolio_risk', {})
    print(f"Active positions: {portfolio_risk.get('total_positions', 0)}")
    print(f"Total portfolio risk: {portfolio_risk.get('total_risk', 0):.4f}")
    
    performance = portfolio.get('performance_metrics', {})
    print(f"Total trades: {performance.get('total_trades', 0)}")
    print(f"Win rate: {performance.get('win_rate', 0):.1f}%")
    print(f"Total P&L: ${performance.get('total_pnl', 0):.2f}")
    
    execution_stats = portfolio.get('execution_statistics', {})
    print(f"Trap trades: {execution_stats.get('trap_trades', 0)}")
    print(f"Regular trades: {execution_stats.get('regular_trades', 0)}")
    
    print(f"\n=== Demo completed successfully ===")
    
    return results


def run_analysis_only():
    """Run market analysis only without executing trades"""
    print("=== Market Analysis Only ===")
    
    bot = MetaTradingBot()
    symbol = "EURUSD"
    market_data = generate_sample_data(symbol, days=10)
    
    # Perform market analysis
    market_context = bot.analyze_market(symbol, market_data)
    
    print(f"\nAnalysis Results for {symbol}:")
    print(f"Timestamp: {market_context.get('timestamp', 'N/A')}")
    
    # Liquidity levels
    liquidity_levels = market_context.get('liquidity_levels', [])
    print(f"\nLiquidity Levels Found: {len(liquidity_levels)}")
    for i, level in enumerate(liquidity_levels[:5]):  # Show top 5
        print(f"  {i+1}. {level.level_type.upper()} at {level.price:.5f} (Volume: {level.volume:.0f})")
    
    # Trap signals
    trap_signals = market_context.get('trap_signals', [])
    print(f"\nTrap Signals Found: {len(trap_signals)}")
    for i, signal in enumerate(trap_signals):
        print(f"  {i+1}. {signal.trap_type.upper()}")
        print(f"      Entry: {signal.entry_price:.5f}")
        print(f"      Stop Loss: {signal.stop_loss:.5f}")
        print(f"      Confidence: {signal.confidence:.2f}")
        print(f"      Safe Entry: {'Yes' if signal.safe_entry_exists else 'No'}")
    
    # Higher timeframe analysis
    htf_analysis = market_context.get('higher_timeframe_structure', {})
    print(f"\nHigher Timeframe Analysis:")
    for tf, structure in htf_analysis.items():
        print(f"  {tf}: {structure.value if hasattr(structure, 'value') else structure}")
    
    return market_context


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='Meta Trading Bot CLI')
    parser.add_argument('--mode', choices=['demo', 'analysis'], default='demo',
                       help='Run mode: demo (full cycle) or analysis (analysis only)')
    parser.add_argument('--config', type=str, help='Path to configuration file (JSON)')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'demo':
            run_bot_demo()
        elif args.mode == 'analysis':
            run_analysis_only()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())