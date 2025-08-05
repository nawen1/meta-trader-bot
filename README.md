# Meta Trader Bot - Multi-Timeframe Analysis

**KAIZEN - BEST TRADING BOT**

A sophisticated trading bot that implements multi-timeframe analysis with strict timeframe hierarchy. The bot prioritizes higher timeframes over lower ones, ensuring that all trading decisions align with institutional market structure and smart money flow.

## 🎯 Key Features

### Multi-Timeframe Hierarchy
- **Strict Priority System**: D1 > H4 > H1 > M15 > M5
- **Higher TF Dominance**: All entries must align with higher timeframe context
- **Conflict Detection**: Identifies and handles timeframe conflicts intelligently

### Advanced Market Analysis
- **Change of Character (ChoCH)**: Detects market structure shifts and trend changes
- **Liquidity Analysis**: Identifies liquidity sweeps, pools, and stop hunts
- **Support/Resistance**: Multi-timeframe S/R levels with confluence detection
- **Market Structure**: Break of structure (BOS) and swing point analysis

### Smart Entry System
- **Context-Aware Signals**: Entries only when aligned with higher TF bias
- **Risk Management**: Automatic stop-loss and take-profit calculation
- **Signal Filtering**: Multiple validation layers for high-quality entries
- **Confluence Trading**: Prioritizes areas where multiple factors align

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from src.meta_trader_bot import MetaTraderBot
import pandas as pd

# Initialize the bot
bot = MetaTraderBot()

# Prepare multi-timeframe data (OHLCV format)
market_data = {
    'D1': daily_data,      # Daily timeframe data
    'H4': h4_data,         # 4-hour timeframe data  
    'H1': h1_data,         # 1-hour timeframe data
    'M15': m15_data,       # 15-minute timeframe data
    'M5': m5_data          # 5-minute timeframe data
}

# Analyze market conditions
analysis = bot.analyze_market(market_data)

# Generate entry signals for a specific timeframe
signals = bot.generate_entry_signals(market_data, 'M15')

# Get trading recommendation
recommendation = bot.get_trading_recommendation()
print(f"Recommendation: {recommendation['recommendation']}")
print(f"Confidence: {recommendation['confidence']:.1%}")
```

### Running the Demo

```bash
python example_usage.py
```

This will run a complete demonstration with sample data showing all bot capabilities.

## 📊 Analysis Components

### 1. Timeframe Analyzer
- Manages timeframe priority hierarchy
- Ensures higher timeframe dominance
- Detects inter-timeframe conflicts

### 2. Market Structure Analyzer
- Identifies swing highs and lows
- Detects ChoCH (Change of Character) patterns
- Recognizes BOS (Break of Structure) signals
- Determines trend direction and strength

### 3. Liquidity Analyzer
- Detects liquidity pools and accumulation zones
- Identifies liquidity sweeps and stop hunts
- Calculates liquidity imbalances
- Predicts next liquidity targets

### 4. Support/Resistance Analyzer
- Multi-touch level validation
- Strength assessment based on multiple factors
- Confluence zone identification
- Broken level tracking

### 5. Entry Signal Generator
- Context-aware signal generation
- Multi-timeframe alignment verification
- Risk/reward calculation
- Signal quality scoring

## 🎛️ Configuration

The bot behavior can be customized through the configuration in `src/config.py`:

```python
# Timeframe priorities (higher values = higher priority)
TIMEFRAME_PRIORITY = {
    'D1': 5,    # Daily - highest priority
    'H4': 4,    # 4-hour
    'H1': 3,    # 1-hour  
    'M15': 2,   # 15-minute
    'M5': 1,    # 5-minute - lowest priority
}

# Entry criteria
ENTRY_CONFIG = {
    'require_higher_tf_alignment': True,
    'min_confirmation_timeframes': 2,
    'risk_reward_ratio': 2.0,
}
```

## 📈 Trading Logic

### Higher Timeframe First Approach

1. **Daily Analysis**: Establishes overall market bias and major levels
2. **4-Hour Context**: Confirms daily bias and identifies intermediate structure
3. **1-Hour Structure**: Refines entry zones and validates signals
4. **Lower TF Entries**: Execute entries with higher timeframe confirmation

### Signal Validation Process

1. **Higher TF Alignment**: Signal direction must match higher TF bias
2. **Structure Confirmation**: Entry must align with market structure
3. **Liquidity Context**: Consider liquidity levels and potential sweeps
4. **Risk Management**: Ensure proper risk/reward ratio
5. **Confluence Check**: Multiple factors supporting the entry

## 🧪 Testing

Run the test suite to verify all components:

```bash
python -m pytest tests/ -v
```

Or run specific tests:

```bash
cd tests
python test_bot.py
```

## 📋 Requirements

- Python 3.7+
- pandas >= 1.3.0
- numpy >= 1.21.0
- ta >= 0.10.0 (for technical analysis)
- python-dateutil >= 2.8.0

## 🔧 Advanced Usage

### Custom Indicators
```python
# Add custom analysis to entry timeframe
def custom_analysis(data):
    # Your custom logic here
    return analysis_result

# Integrate with bot
bot.add_custom_analysis(custom_analysis)
```

### Export Analysis
```python
# Export detailed analysis to JSON
filename = bot.export_analysis()
print(f"Analysis saved to {filename}")
```

### Real-time Monitoring
```python
# Continuous market monitoring
while True:
    analysis = bot.analyze_market(get_live_data())
    
    if analysis['trading_recommendation']['recommendation'] != 'NO_ACTION':
        signals = bot.generate_entry_signals(get_live_data(), 'M15')
        process_signals(signals)
    
    time.sleep(300)  # Check every 5 minutes
```

## 🎯 Key Principles

1. **Higher Timeframes Rule**: Never trade against higher timeframe bias
2. **Context is King**: Always consider full market context before entries
3. **Quality over Quantity**: Focus on high-probability setups only
4. **Risk Management**: Every trade must have proper risk/reward ratio
5. **Institutional Alignment**: Follow smart money flow and market structure

## 📚 Understanding Market Structure

### Change of Character (ChoCH)
- Indicates potential trend reversal
- Break of previous market structure
- Higher timeframe ChoCH overrides lower timeframe signals

### Liquidity Sweeps
- Institutional moves to collect liquidity
- Often create optimal entry opportunities
- Look for reversal after sweep completion

### Break of Structure (BOS)
- Confirms trend continuation
- Entry signal in direction of break
- Must align with higher timeframe bias

## 🔄 Workflow Example

1. **Market Opening**: Analyze D1 and H4 for overall bias
2. **Session Planning**: Identify key levels and liquidity zones
3. **Entry Setup**: Monitor M15/M5 for aligned entry signals
4. **Trade Execution**: Enter only with higher TF confirmation
5. **Management**: Adjust based on structure development

## 🚨 Risk Disclaimer

This trading bot is for educational and research purposes. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Always use proper risk management and never risk more than you can afford to lose.

## 📞 Support

For questions, suggestions, or contributions:
- Create an issue on GitHub
- Review the documentation in the `docs/` folder
- Check the example usage in `example_usage.py`

## 🏆 License

MIT License - See LICENSE file for details

---

**Remember**: In multi-timeframe analysis, the higher timeframe always wins. This bot ensures you're always trading with the institutional flow, not against it.
