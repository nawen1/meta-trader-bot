#!/usr/bin/env python3
"""
Example script demonstrating the Meta Trader Bot functionality
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from meta_trader_bot import TradingBot
from meta_trader_bot.core.models import TimeFrame, TradingConfig
from meta_trader_bot.utils.data_utils import generate_sample_data, calculate_technical_indicators
from meta_trader_bot.config.config_manager import load_config_from_file, get_default_config


def main():
    """Main example function."""
    print("🤖 Meta Trader Bot - KAIZEN Advanced Trading System")
    print("=" * 60)
    
    # Initialize configuration
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'meta_trader_bot', 'config', 'default_config.json')
        config = load_config_from_file(config_path)
        print("✅ Configuration loaded from file")
    except FileNotFoundError:
        config = get_default_config()
        print("⚠️  Using default configuration")
    
    # Initialize the bot
    bot = TradingBot(config=config, account_balance=10000.0)
    print(f"✅ Trading Bot initialized with ${bot.account_balance:,.2f}")
    
    # Generate sample market data for demonstration
    print("\n📊 Generating sample market data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # 1 week of data
    
    market_data = {}
    for timeframe in config.timeframes_to_analyze:
        print(f"   - Generating {timeframe.value} data...")
        data = generate_sample_data(start_date, end_date, timeframe, initial_price=1.1000)
        data = calculate_technical_indicators(data)
        market_data[timeframe] = data
    
    print(f"✅ Generated data for {len(market_data)} timeframes")
    
    # Start the bot
    bot.start()
    print("\n🚀 Trading Bot started")
    
    # Demonstrate market analysis
    print("\n🔍 Performing market analysis...")
    analysis = bot.analyze_market(market_data)
    
    if 'error' in analysis:
        print(f"❌ Analysis error: {analysis['error']}")
        return
    
    print(f"✅ Analysis completed at {analysis['timestamp']}")
    print(f"   - Trap signals found: {len(analysis['trap_signals'])}")
    print(f"   - Entry signals found: {len(analysis['entry_signals'])}")
    print(f"   - Market structures analyzed: {len(analysis['market_structures'])}")
    
    # Display trap signals
    if analysis['trap_signals']:
        print("\n🎯 Trap Signals:")
        for i, signal in enumerate(analysis['trap_signals'][:3]):  # Show first 3
            print(f"   {i+1}. Type: {signal.trap_type.value}")
            print(f"      Confidence: {signal.confidence:.2%}")
            print(f"      Risk Level: {signal.risk_level.value}")
            print(f"      Safe Entry: {'Yes' if signal.safe_entry_exists else 'No'}")
            if signal.entry_price:
                print(f"      Entry Price: {signal.entry_price:.5f}")
            print(f"      Distance to Liquidity: {signal.distance_to_liquidity:.4%}")
    
    # Display entry signals
    if analysis['entry_signals']:
        print("\n📈 Entry Signals:")
        for i, signal in enumerate(analysis['entry_signals'][:3]):  # Show first 3
            print(f"   {i+1}. Price: {signal.price:.5f}")
            print(f"      Direction: {signal.direction.value}")
            print(f"      Model: {signal.model_alignment.value}")
            print(f"      Confidence: {signal.confidence:.2%}")
            print(f"      Clean Zone: {'Yes' if signal.clean_zone else 'No'}")
            if signal.boss_structure:
                print(f"      Boss Structure: {signal.boss_structure.strength:.2f} strength")
    
    # Evaluate trading opportunity
    print("\n💡 Evaluating trading opportunities...")
    opportunity = bot.evaluate_trading_opportunity(market_data, force_analysis=True)
    
    if opportunity:
        print("✅ Trading opportunity found!")
        print(f"   Type: {opportunity['type']}")
        print(f"   Entry Price: {opportunity['entry_price']:.5f}")
        print(f"   Direction: {opportunity['direction'].value}")
        print(f"   Stop Loss: {opportunity['stop_loss']:.5f}")
        print(f"   Position Size: {opportunity['position_size']:.2f}")
        print(f"   Estimated Risk: ${opportunity['estimated_risk']:.2f}")
        print(f"   Total Score: {opportunity['total_score']:.2%}")
        
        # Simulate trade execution
        print("\n📋 Simulating trade execution...")
        position_id = bot.execute_trade(opportunity)
        if position_id:
            print(f"✅ Trade executed! Position ID: {position_id}")
            
            # Show position details
            position_status = bot.risk_manager.get_position_status(position_id)
            if position_status:
                print(f"   Entry Price: {position_status['entry_price']:.5f}")
                print(f"   Direction: {position_status['direction']}")
                print(f"   Size: {position_status['size']:.2f}")
                print(f"   TP1: {position_status['tp1_price']:.5f}")
                print(f"   TP2: {position_status['tp2_price']:.5f}")
                print(f"   TP3: {position_status['tp3_price']:.5f}")
                print(f"   Stop Loss: {position_status['stop_loss']:.5f}")
        else:
            print("❌ Trade execution failed")
    else:
        print("⚠️  No trading opportunities found at this time")
    
    # Display risk metrics
    print("\n📊 Risk Metrics:")
    risk_metrics = bot.risk_manager.get_risk_metrics()
    print(f"   Total Positions: {risk_metrics['total_positions']}")
    print(f"   Total Risk: ${risk_metrics['total_risk']:.2f} ({risk_metrics['risk_percentage']:.2f}%)")
    print(f"   Total Exposure: ${risk_metrics['total_exposure']:.2f} ({risk_metrics['exposure_percentage']:.2f}%)")
    print(f"   Account Balance: ${risk_metrics['account_balance']:,.2f}")
    print(f"   Trap Trades: {risk_metrics['trap_trades']}")
    print(f"   Regular Trades: {risk_metrics['regular_trades']}")
    
    # Simulate price updates
    if bot.risk_manager.active_positions:
        print("\n🔄 Simulating position updates...")
        
        # Create sample price updates (simulate market movement)
        current_prices = {}
        for position_id in bot.risk_manager.active_positions.keys():
            position = bot.risk_manager.active_positions[position_id]
            # Simulate 0.1% favorable price movement
            if position.direction.value == 'long':
                new_price = position.entry_price * 1.001
            else:
                new_price = position.entry_price * 0.999
            current_prices[position_id] = new_price
        
        # Update positions
        update_results = bot.update_positions(current_prices)
        if 'error' not in update_results:
            print(f"✅ Position updates completed")
            if update_results['actions_taken']:
                print("   Actions taken:")
                for action in update_results['actions_taken']:
                    print(f"   - {action}")
            else:
                print("   - No actions required")
        else:
            print(f"❌ Update error: {update_results['error']}")
    
    # Show final bot status
    print("\n📋 Final Bot Status:")
    status = bot.get_status()
    print(f"   Running: {status['is_running']}")
    print(f"   Active Positions: {len(status['active_positions'])}")
    print(f"   Account Balance: ${status['account_balance']:,.2f}")
    
    # Shutdown bot
    bot.shutdown()
    print("\n🛑 Trading Bot shutdown completed")
    print("\n" + "=" * 60)
    print("Demo completed successfully! 🎉")
    print("\nKey Features Demonstrated:")
    print("✓ Advanced trap recognition and analysis")
    print("✓ Strict entry validation with Model 2 alignment")
    print("✓ Dynamic risk management with TP1/TP2/TP3")
    print("✓ Multi-timeframe structural analysis")
    print("✓ Real-time position management")
    print("✓ Comprehensive risk monitoring")


if __name__ == "__main__":
    main()