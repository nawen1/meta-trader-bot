#!/usr/bin/env python3
"""
Main entry point for the BTCUSD Trading Bot.
"""
import sys
import os
import argparse
import signal
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from trading_bot.bot import BTCUSDTradingBot
from trading_bot.config.settings import load_config


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutdown signal received. Stopping bot...")
    sys.exit(0)


def main():
    """Main function to run the trading bot."""
    parser = argparse.ArgumentParser(description='BTCUSD Trading Bot')
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode with mock data'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Display performance statistics and exit'
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize bot
        bot = BTCUSDTradingBot(config_path=args.config)
        
        if args.stats:
            # Display stats and exit
            stats = bot.get_performance_stats()
            print("\n=== Trading Bot Performance Statistics ===")
            print(f"Total Trades: {stats['total_trades']}")
            print(f"Winning Trades: {stats['winning_trades']}")
            print(f"Win Rate: {stats['win_rate']:.2f}%")
            print(f"Total Realized P&L: ${stats['total_realized_pnl']:.2f}")
            print(f"Total Unrealized P&L: ${stats['total_unrealized_pnl']:.2f}")
            print(f"Daily P&L: ${stats['daily_pnl']:.2f}")
            print(f"Total Exposure: ${stats['total_exposure']:.2f}")
            return
        
        # Start the bot
        print("Starting BTCUSD Trading Bot...")
        print("Press Ctrl+C to stop the bot gracefully")
        
        if args.demo:
            print("Running in DEMO mode with simulated data")
        
        bot.start()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()