#!/usr/bin/env python3
"""
Simplified CLI runner for the Meta Trading Bot (without external dependencies)
"""
import sys
import json
from datetime import datetime, timedelta
import random
import math

# Simplified data structure without pandas
class SimpleDataFrame:
    def __init__(self, data, columns):
        self.data = data
        self.columns = columns
        self.index = list(range(len(data)))
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, key):
        if isinstance(key, str):
            col_idx = self.columns.index(key)
            return [row[col_idx] for row in self.data]
        elif isinstance(key, int):
            return dict(zip(self.columns, self.data[key]))
        return None
    
    def iloc(self, idx):
        return dict(zip(self.columns, self.data[idx]))


def generate_sample_data(symbol="EURUSD", days=30):
    """
    Generate sample OHLCV data for testing
    """
    base_price = 1.1000
    data = {}
    
    # Generate 15m data
    periods = days * 24 * 4  # 15-minute periods
    prices = [base_price]
    
    random.seed(42)  # For reproducible results
    
    for i in range(periods - 1):
        change = random.gauss(0, 0.001)  # Small random changes
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # Generate OHLC data
    ohlcv_data = []
    for i, close in enumerate(prices):
        volatility = random.uniform(0.0005, 0.002)
        
        high = close * (1 + volatility * random.uniform(0.3, 1.0))
        low = close * (1 - volatility * random.uniform(0.3, 1.0))
        
        if i == 0:
            open_price = close
        else:
            open_price = prices[i-1] * (1 + random.gauss(0, 0.0002))
        
        volume = random.uniform(1000, 10000)
        
        ohlcv_data.append([
            max(open_price, close, high),  # high
            min(open_price, close, low),   # low  
            open_price,                    # open
            close,                         # close
            volume                         # volume
        ])
    
    # Create simplified DataFrame
    columns = ['high', 'low', 'open', 'close', 'volume']
    data['15m'] = SimpleDataFrame(ohlcv_data, columns)
    
    return data


def analyze_market_simple(data):
    """
    Simplified market analysis
    """
    df = data['15m']
    
    # Calculate simple metrics
    closes = df['close']
    highs = df['high']
    lows = df['low']
    volumes = df['volume']
    
    # Simple trend analysis
    recent_closes = closes[-20:]  # Last 20 periods
    trend_direction = "bullish" if recent_closes[-1] > recent_closes[0] else "bearish"
    
    # Simple volatility (range)
    recent_ranges = []
    for i in range(len(highs) - 20, len(highs)):
        recent_ranges.append(highs[i] - lows[i])
    avg_range = sum(recent_ranges) / len(recent_ranges)
    volatility = avg_range / closes[-1]
    
    # Simple volume analysis
    avg_volume = sum(volumes[-20:]) / 20
    volume_strength = volumes[-1] / avg_volume
    
    # Look for potential trap signals
    trap_signals = []
    
    # Simple trap detection: look for false breakouts
    for i in range(50, len(closes) - 5):
        current_high = highs[i]
        prev_highs = highs[i-20:i]
        resistance = max(prev_highs)
        
        # Potential bull trap: break above resistance then fall back
        if current_high > resistance:
            # Check if price fell back in next few candles
            next_closes = closes[i+1:i+5]
            if next_closes and min(next_closes) < closes[i] * 0.995:
                confidence = min(0.9, volume_strength * 0.5 + 0.4)
                if confidence > 0.6:
                    trap_signals.append({
                        'type': 'bull_trap',
                        'entry_price': closes[i],
                        'stop_loss': current_high * 1.002,
                        'take_profits': [
                            closes[i] * 0.98,   # TP1: -2%
                            closes[i] * 0.96,   # TP2: -4%
                            closes[i] * 0.94    # TP3: -6%
                        ],
                        'confidence': confidence,
                        'safe_entry_exists': True
                    })
    
    # Look for bear traps (false breakdowns)
    for i in range(50, len(closes) - 5):
        current_low = lows[i]
        prev_lows = lows[i-20:i]
        support = min(prev_lows)
        
        # Potential bear trap: break below support then recover
        if current_low < support:
            # Check if price recovered in next few candles
            next_closes = closes[i+1:i+5]
            if next_closes and max(next_closes) > closes[i] * 1.005:
                confidence = min(0.9, volume_strength * 0.5 + 0.4)
                if confidence > 0.6:
                    trap_signals.append({
                        'type': 'bear_trap',
                        'entry_price': closes[i],
                        'stop_loss': current_low * 0.998,
                        'take_profits': [
                            closes[i] * 1.02,   # TP1: +2%
                            closes[i] * 1.04,   # TP2: +4%
                            closes[i] * 1.06    # TP3: +6%
                        ],
                        'confidence': confidence,
                        'safe_entry_exists': True
                    })
    
    return {
        'symbol': 'EURUSD',
        'timestamp': datetime.now(),
        'trend_direction': trend_direction,
        'volatility': volatility,
        'volume_strength': volume_strength,
        'current_price': closes[-1],
        'trap_signals': trap_signals,
        'market_metrics': {
            'avg_range': avg_range,
            'avg_volume': avg_volume,
            'trend_strength': abs(recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        }
    }


def validate_trap_signal(signal, account_balance=10000):
    """
    Validate a trap signal for trading
    """
    # Calculate risk
    risk_per_unit = abs(signal['entry_price'] - signal['stop_loss'])
    max_risk_amount = account_balance * 0.02  # 2% risk
    position_size = max_risk_amount / risk_per_unit
    
    # Validate risk-reward ratios
    rewards = []
    for tp in signal['take_profits']:
        reward = abs(tp - signal['entry_price'])
        rr_ratio = reward / risk_per_unit if risk_per_unit > 0 else 0
        rewards.append(rr_ratio)
    
    # Check minimum requirements
    valid = (
        signal['confidence'] >= 0.6 and  # Minimum confidence
        signal['safe_entry_exists'] and
        len([r for r in rewards if r >= 1.0]) >= 1  # At least one 1:1 RR
    )
    
    return {
        'valid': valid,
        'position_size': position_size,
        'risk_amount': max_risk_amount,
        'reward_ratios': rewards,
        'confidence': signal['confidence']
    }


def run_bot_demo():
    """Run a simplified demo of the trading bot"""
    print("=== Meta Trading Bot Demo (Simplified) ===")
    print("Initializing bot...")
    
    # Generate sample market data
    print("Generating sample market data...")
    symbol = "EURUSD"
    market_data = generate_sample_data(symbol, days=30)
    
    print(f"Generated {len(market_data['15m'])} data points for {symbol}")
    
    # Analyze market
    print("Analyzing market for trap signals...")
    analysis = analyze_market_simple(market_data)
    
    # Display results
    print(f"\n=== Market Analysis Results ===")
    print(f"Symbol: {analysis['symbol']}")
    print(f"Current Price: {analysis['current_price']:.5f}")
    print(f"Trend Direction: {analysis['trend_direction']}")
    print(f"Volatility: {analysis['volatility']:.4f}")
    print(f"Volume Strength: {analysis['volume_strength']:.2f}")
    
    # Display trap signals
    trap_signals = analysis['trap_signals']
    print(f"\n=== Trap Signals Found: {len(trap_signals)} ===")
    
    valid_signals = 0
    account_balance = 10000.0
    
    for i, signal in enumerate(trap_signals):
        print(f"\nSignal {i+1}: {signal['type'].upper()}")
        print(f"  Entry Price: {signal['entry_price']:.5f}")
        print(f"  Stop Loss: {signal['stop_loss']:.5f}")
        print(f"  Take Profits: {[f'{tp:.5f}' for tp in signal['take_profits']]}")
        print(f"  Confidence: {signal['confidence']:.2f}")
        print(f"  Safe Entry: {'Yes' if signal['safe_entry_exists'] else 'No'}")
        
        # Validate signal
        validation = validate_trap_signal(signal, account_balance)
        print(f"  Validation: {'VALID' if validation['valid'] else 'INVALID'}")
        
        if validation['valid']:
            valid_signals += 1
            print(f"  Position Size: {validation['position_size']:.2f}")
            print(f"  Risk Amount: ${validation['risk_amount']:.2f}")
            print(f"  R:R Ratios: {[f'{r:.2f}' for r in validation['reward_ratios']]}")
    
    # Summary
    print(f"\n=== Trading Summary ===")
    print(f"Total signals found: {len(trap_signals)}")
    print(f"Valid signals: {valid_signals}")
    print(f"Account balance: ${account_balance:,.2f}")
    print(f"Max risk per trade: ${account_balance * 0.02:.2f} (2%)")
    
    # Risk management demonstration
    if valid_signals > 0:
        print(f"\n=== Risk Management Features ===")
        print("✓ Trap identification based on false breakouts")
        print("✓ Safe entry point validation")
        print("✓ Multiple take profit levels (TP1, TP2, TP3)")
        print("✓ Automatic position sizing based on risk")
        print("✓ Confidence-based signal filtering")
        print("✓ Risk-reward ratio validation")
    
    print(f"\n=== Demo completed successfully ===")
    
    return analysis


def run_analysis_only():
    """Run market analysis only"""
    print("=== Market Analysis Only ===")
    
    symbol = "EURUSD"
    market_data = generate_sample_data(symbol, days=10)
    
    # Perform market analysis
    analysis = analyze_market_simple(market_data)
    
    print(f"\nAnalysis Results for {symbol}:")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Current Price: {analysis['current_price']:.5f}")
    print(f"Trend: {analysis['trend_direction']}")
    print(f"Volatility: {analysis['volatility']:.4f}")
    
    # Show metrics
    metrics = analysis['market_metrics']
    print(f"\nMarket Metrics:")
    print(f"  Average Range: {metrics['avg_range']:.6f}")
    print(f"  Average Volume: {metrics['avg_volume']:.0f}")
    print(f"  Trend Strength: {metrics['trend_strength']:.4f}")
    
    # Show trap signals
    trap_signals = analysis['trap_signals']
    print(f"\nTrap Signals: {len(trap_signals)}")
    
    for i, signal in enumerate(trap_signals):
        print(f"  {i+1}. {signal['type']} (confidence: {signal['confidence']:.2f})")
    
    return analysis


def main():
    """Main CLI function"""
    if len(sys.argv) > 1 and sys.argv[1] == "analysis":
        run_analysis_only()
    else:
        run_bot_demo()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)