HEAD
# BTCUSD Meta Trading Bot

An advanced trading bot for BTCUSD with refined logic based on the latest principles for analyzing and operating trades. The bot implements sophisticated entry strategies, dynamic risk management, and strict validation to ensure high-probability setups.

## Features

### 🎯 Entry Strategy Refinement
- **Structure Break Detection**: Identifies Boss (Break of Structure) patterns and other significant structure breaks
- **Liquidity Point Targeting**: Locates liquid points for potential barrages and sweep detection
- **Clean Zone Identification**: Finds clean zones for high-probability entry points
- **Trend Continuation Logic**: Ensures trades only execute when liquid points are swept and clean zones respect the trend

### 🛡️ Risk Management Enhancements
- **Dynamic Trailing Stops**: Automatically adjusts stop losses to secure profits as price moves favorably
- **Multiple Take Profit Levels**: Divides positions into TP1, TP2, and TP3 for optimized exit strategies
- **Position Sizing**: Intelligent position sizing based on account balance and risk parameters
- **Daily Loss Limits**: Prevents excessive losses by stopping trading when daily limits are reached

### ✅ Strict Validation
- **Entry Point Validation**: Avoids entries based solely on structure breaks without further context
- **Liquidity Sweep Analysis**: Ensures liquidity sweeps are confirmed before entry
- **Clean Zone Respect**: Validates that price action respects identified clean zones
- **Confidence Scoring**: Assigns confidence scores to potential setups

### 🔄 Real-time Adaptation
- **Price Action Analysis**: Adapts to current market conditions and price movements
- **Volume Analysis**: Incorporates volume changes in decision-making
- **Principle Adherence**: Maintains strict adherence to trading principles while adapting to market conditions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your exchange API credentials and preferences
```

## Configuration

The bot uses environment variables for configuration. Key parameters include:

### Exchange Settings
- `EXCHANGE_API_KEY`: Your exchange API key
- `EXCHANGE_SECRET`: Your exchange secret
- `EXCHANGE_PASSPHRASE`: Your exchange passphrase (if required)
- `EXCHANGE_SANDBOX`: Set to `true` for demo trading

### Trading Parameters
- `SYMBOL`: Trading pair (default: BTC/USDT)
- `POSITION_SIZE_PERCENT`: Position size as percentage of account (default: 2.0%)
- `MAX_DAILY_LOSS_PERCENT`: Maximum daily loss limit (default: 5.0%)

### Take Profit Levels
- `TP1_PERCENT`: First take profit level (default: 1.0%)
- `TP2_PERCENT`: Second take profit level (default: 2.5%)
- `TP3_PERCENT`: Third take profit level (default: 5.0%)

### Position Allocation
- `TP1_ALLOCATION`: Percentage for TP1 (default: 30%)
- `TP2_ALLOCATION`: Percentage for TP2 (default: 40%)
- `TP3_ALLOCATION`: Percentage for TP3 (default: 30%)

## Usage

### Basic Usage
```bash
python main.py
```

### Demo Mode (Recommended for testing)
```bash
python main.py --demo
```

### View Performance Statistics
```bash
python main.py --stats
```

### Custom Configuration
```bash
python main.py --config /path/to/config.env
```

## Architecture

The bot is structured into several key components:

### Core Components
- **`bot.py`**: Main trading bot orchestrating all components
- **`config/settings.py`**: Configuration management and validation
- **`analysis/market_structure.py`**: Market structure analysis and pattern detection
- **`risk_management/position_manager.py`**: Position and risk management
- **`validation/entry_validator.py`**: Strict entry validation logic

### Key Classes
- **`BTCUSDTradingBot`**: Main bot class coordinating all operations
- **`MarketStructureAnalyzer`**: Analyzes market structure, structure breaks, and clean zones
- **`RiskManager`**: Handles position sizing, trailing stops, and P&L management
- **`EntryValidator`**: Validates entry opportunities using strict criteria

## Trading Logic

### Entry Process
1. **Structure Break Detection**: Identify significant breaks in market structure
2. **Liquidity Analysis**: Locate and monitor liquidity points for sweeps
3. **Clean Zone Validation**: Ensure entry occurs within identified clean zones
4. **Trend Confirmation**: Validate trend continuation logic
5. **Volume Validation**: Confirm adequate volume support
6. **Risk/Reward Calculation**: Ensure minimum 2:1 risk/reward ratio
7. **Confidence Scoring**: Calculate overall confidence in the setup

### Exit Process
1. **Dynamic Trailing Stops**: Continuously update trailing stops as price moves favorably
2. **Take Profit Execution**: Execute partial closes at TP1, TP2, and TP3 levels
3. **Position Management**: Adjust remaining position size and risk parameters
4. **P&L Tracking**: Monitor realized and unrealized profits/losses

## Testing

Run the test suite to validate bot components:

copilot/fix-a472e9a1-ed5c-4ecc-aa4f-d8d6469e04b4
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

copilot/fix-63aa93a4-72a5-471a-a5ef-b3c5a75cd0ff
# Meta Trader Bot

KAIZEN - Advanced Trading Bot with sophisticated trap analysis and risk management.

## Features

- **Advanced Trap Recognition**: Identifies traps from distance based on liquidity analysis
- **Strict Entry Validation**: Operates only on clear entry points aligned with trading models
- **Dynamic Risk Management**: Implements trailing stops and position management (TP1/TP2/TP3)
- **Structural Analysis**: Multi-timeframe analysis with clean zone identification

copilot/fix-ba9cb030-7087-4abc-ac1e-cd1a8563403f
# Meta Trading Bot - Advanced Trap Identification & Risk Management

An intelligent trading bot that specializes in identifying and safely operating market traps while maintaining strict risk management protocols.

## Key Features

### 🎯 Advanced Trap Identification
- **Liquidity-Based Detection**: Identifies traps based on liquidity above/below inductions
- **Strict Differentiation**: Uses precise criteria to differentiate between traps and legitimate inductions
- **Safe Entry Validation**: Ensures clear and safe entry points exist before trap execution

### 🛡️ Comprehensive Risk Management
- **Trailing Stops**: Dynamic stop-loss adjustments to protect profits
- **Multi-Level Take Profits**: TP1, TP2, TP3 with configurable ratios
- **Position Sizing**: Automatic position sizing based on risk parameters
- **Portfolio Risk Control**: Monitors overall portfolio exposure

### 📊 Market Analysis
- **Higher Timeframe Context**: Analyzes multiple timeframes for market structure
- **Trade Avoidance Logic**: Avoids forced trades when no valid setup exists
- **Market Structure Recognition**: Identifies bullish, bearish, and sideways markets
- **Volume and Volatility Analysis**: Incorporates volume and volatility metrics

### ⚙️ Configuration & Flexibility
- **Configurable Parameters**: Adjustable risk, confidence, and strategy settings
- **Trap Trading Toggle**: Can enable/disable trap trading operations
- **Force Trade Prevention**: Prevents entering trades without clear setups
main

## Installation

```bash
copilot/fix-63aa93a4-72a5-471a-a5ef-b3c5a75cd0ff
pip install -r requirements.txt
```

## Usage

```python
from meta_trader_bot import TradingBot

bot = TradingBot()
bot.start()

main
# Clone the repository
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot

# Install dependencies
pip install -r requirements.txt
copilot/fix-a472e9a1-ed5c-4ecc-aa4f-d8d6469e04b4
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
main

```bash
python -m pytest tests/ -v
```

HEAD
Or run the basic test suite:

```bash
python tests/test_trading_bot.py
```

## Safety Features

- **Sandbox Mode**: Default operation in sandbox/demo mode for safe testing
- **Daily Loss Limits**: Automatic trading halt when daily loss limits are reached
- **Position Size Limits**: Intelligent position sizing to prevent overexposure
- **Validation Layers**: Multiple validation layers before entry execution
- **Error Handling**: Comprehensive error handling and logging

## Logging

The bot generates detailed logs including:
- Entry/exit decisions and reasoning
- Market analysis results
- Position updates and P&L changes
- Error messages and warnings

Logs are written to both console and `trading_bot.log` file.

## Disclaimer

This trading bot is for educational and research purposes. Trading cryptocurrencies involves substantial risk and may not be suitable for all investors. Always test thoroughly in demo mode before using real funds. The authors are not responsible for any financial losses incurred through the use of this software.

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


# Install the package
pip install -e .
```

## Quick Start

### Run the Demo
```bash
python run_bot.py --mode demo
```

### Market Analysis Only
```bash
python run_bot.py --mode analysis
```

### Run Tests
```bash
python -m pytest tests/ -v
```

## Usage Examples

### Basic Bot Usage
```python
from bot.main import MetaTradingBot
from bot.config import BotConfig

# Initialize bot
bot = MetaTradingBot(account_balance=10000.0)

# Prepare market data (OHLCV DataFrames for different timeframes)
market_data = {
    '15m': df_15m,  # Primary timeframe
    '1h': df_1h,    # Higher timeframe
    '4h': df_4h,    # Higher timeframe
    '1d': df_1d     # Highest timeframe
}

# Current market prices
current_prices = {"EURUSD": 1.1000}

# Run complete trading cycle
results = bot.run_trading_cycle("EURUSD", market_data, current_prices)

 copilot/fix-7df13fe5-3188-47c1-8206-1d533e15e5fe
# Meta Trading Bot - KAIZEN

**Advanced Multi-Timeframe Trading Bot with Autonomous Decision Making**

A sophisticated trading bot that implements advanced technical analysis techniques including multi-timeframe analysis, autonomous pattern recognition, and adaptive trap detection.

## 🚀 Key Features

### ✅ Multi-Timeframe Analysis (Requirement 1)
- **Higher Timeframe Context**: Analyzes 1D, 4H, 1H timeframes for market direction
- **Lower Timeframe Entries**: Uses 15M, 5M, 1M for precise entry timing
- **Trend Alignment**: Ensures entries align with broader market trends
- **Context Validation**: Validates lower TF signals against higher TF structure

### ✅ Independent Technical Analysis (Requirement 2)
- **Autonomous Liquidity Zone Detection**: Identifies key support/resistance without presets
- **Smart Fractal Identification**: Self-determining swing points and market structure
- **CHOCH Detection**: Automatically recognizes Change of Character patterns
- **No Preset Dependencies**: All analysis is calculated dynamically from price action

### ✅ Advanced Fractal Analysis (Requirement 3)
- **Market Structure Validation**: Fractals are validated within broader context
- **Strength Scoring**: Each fractal receives a strength score (0-1)
- **Premature Prevention**: Logic prevents premature fractal assumptions
- **Volume Confirmation**: Uses volume data when available for validation

### ✅ False Break Detection (Requirement 4)
- **Liquidity Sweep Recognition**: Identifies when price sweeps stops for liquidity
- **Momentum Validation**: Distinguishes genuine breaks from false moves
- **Retest Analysis**: Analyzes how price behaves after level breaks
- **Multi-Factor Confirmation**: Uses volume, momentum, and price action together

### ✅ Adaptive Intelligence (Requirement 5)
- **Trap Detection**: Identifies bull traps, bear traps, and liquidity traps
- **Autonomous Reassessment**: Continuously evaluates and adapts strategy
- **Market Character Recognition**: Adapts to choppy, trending, or manipulative markets
- **Risk Adjustment**: Dynamically adjusts risk based on market conditions

## 🏗️ Architecture

```
meta-trader-bot/
├── analysis/
│   ├── timeframe_analyzer.py    # Multi-timeframe coordination
│   ├── fractals.py             # Fractal identification & validation
│   ├── choch_detector.py       # Change of Character detection
│   ├── liquidity_zones.py      # Liquidity zone analysis
│   └── market_structure.py     # False break & momentum analysis
├── utils/
│   ├── config.py               # Configuration management
│   └── data_handler.py         # Data fetching & processing
├── tests/
│   └── test_trading_bot.py     # Unit tests
├── trader_bot.py               # Main bot class
├── main.py                     # Entry point & demo
└── requirements.txt            # Dependencies
```

## 🛠️ Installation

# KAIZEN - Meta Trader Bot (Unified)

**Advanced MetaTrader 5 Trading Bot with Multi-Platform Integration**

This repository contains the unified implementation of 6 MetaTrader 5 related pull requests, merged into a single comprehensive trading system.

## 🚀 Unified Features

### 📊 Multi-Platform Integration
- **MetaTrader 5** - Advanced risk management and automated trading
- **TradingView** - Pine Script compatibility with real-time analysis
- **Python Framework** - Complete autonomous trading system

### 🧠 Advanced Analysis Engine
- **Multi-Timeframe Analysis** with strict higher timeframe prioritization
- **Autonomous Pattern Recognition** - Independent fractal and structure detection
- **Advanced Trap Detection** - Sophisticated liquidity sweep and trap analysis
- **BTCUSD Specialized Strategies** - Crypto-specific entry refinements
- **Change of Character (CHOCH)** detection with market structure analysis

### ⚡ Key Capabilities

#### From PR #1 - MetaTrader 5 Integration
- Advanced risk management with trailing stops
- Multi-tier take profit levels (TP1: 80%, TP2: 20%, TP3: 0%)
- Dynamic position sizing based on account balance
- Daily loss limits and exposure control

#### From PR #2 - TradingView Pine Script
- Complete Pine Script implementation (`kaizen_trading_strategy.pine`)
- Real-time pattern recognition and alerts
- Configurable visual overlays and statistics
- Mobile-compatible TradingView integration

#### From PR #3 - Multi-Timeframe Analysis
- Higher timeframe context analysis (1D, 4H, 1H)
- Lower timeframe precision entries (15M, 5M, 1M)  
- Autonomous liquidity zone detection
- Independent fractal identification without presets

#### From PR #4 & #5 - Advanced Trap Detection
- Distance-based trap identification using liquidity analysis
- Safe entry point validation preventing risky trades
- Multi-type trap detection (bull, bear, liquidity, induction traps)
- Model 2 alignment checks with pullback validation

#### From PR #6 - BTCUSD Refined Strategies
- Structure break detection with strength classification
- Clean zone analysis with minimal price overlap
- Dynamic trailing stops for crypto volatility
- Specialized entry strategies for BTCUSD

#### From PR #7 - Higher Timeframe Prioritization
- Strict institutional alignment (D1 > H4 > H1 > M15 > M5)
- Smart money flow tracking
- Conflict detection and resolution
- Ensures all trades align with higher timeframe bias

## 🛠️ Installation & Setup

### Quick Start
 main

1. **Clone the repository**:
```bash
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

 copilot/fix-7df13fe5-3188-47c1-8206-1d533e15e5fe
3. **Run the bot**:
```bash
python main.py
```

## 📊 Usage Examples

### Basic Analysis
```python
from trader_bot import MetaTradingBot

# Initialize bot with default settings
bot = MetaTradingBot()

# Analyze a symbol
results = bot.analyze_and_trade('EURUSD')

# Display results
print(f"Trading Decisions: {len(results['final_decisions'])}")
print(f"Market Bias: {results['market_analysis']['multi_timeframe']['context_analysis']['overall_bias']}")
main
```

### Custom Configuration
```python
copilot/fix-ba9cb030-7087-4abc-ac1e-cd1a8563403f
from bot.config import BotConfig, RiskManagementConfig

# Create custom configuration
config = BotConfig(
    risk_management=RiskManagementConfig(
        max_risk_per_trade=0.01,  # 1% risk per trade
        trailing_stop_distance=0.003,  # 0.3% trailing stop
        tp1_ratio=1.5,  # 1.5:1 risk-reward for TP1
        tp2_ratio=2.5,  # 2.5:1 risk-reward for TP2
        tp3_ratio=4.0   # 4:1 risk-reward for TP3
    ),
    min_entry_confidence=0.8,  # 80% minimum confidence
    enable_trap_trading=True,
    force_trades=False
)

# Initialize bot with custom config
bot = MetaTradingBot(config=config, account_balance=10000.0)
main
```

## Architecture

copilot/fix-63aa93a4-72a5-471a-a5ef-b3c5a75cd0ff
- `core/`: Main trading bot orchestrator
- `analyzers/`: Market analysis modules (trap detection, structural analysis)
- `managers/`: Risk and trade management modules  
- `utils/`: Utility functions and helpers
- `config/`: Configuration files and settings

The bot is structured into several key modules:

- **`bot/main.py`**: Main trading bot orchestrator
- **`bot/market_analysis.py`**: Market analysis and trap identification
- **`bot/risk_management.py`**: Risk management and position handling
- **`bot/trade_executor.py`**: Trade validation and execution
- **`bot/config.py`**: Configuration management

## Risk Management Features

### Position Sizing
- Automatic calculation based on account balance and risk percentage
- Considers stop-loss distance for precise sizing
- Adjustable maximum risk per trade

### Trailing Stops
- Dynamic stop-loss adjustments as price moves favorably
- Configurable trailing distance
- Protects profits while allowing for continued upside

### Take Profit Management
- Three-level take profit system (TP1, TP2, TP3)
- Partial position closing at each level
- Configurable risk-reward ratios

### Portfolio Protection
- Maximum number of concurrent positions
- Total portfolio risk monitoring
- Market condition-based trade avoidance

## Trap Trading Logic

### Identification Criteria
1. **Liquidity Analysis**: Identifies areas of high liquidity above/below key levels
2. **Induction Detection**: Recognizes false breakouts that lead to reversals
3. **Entry Point Validation**: Ensures safe entry exists before trap formation
4. **Confidence Scoring**: Assigns confidence levels to trap signals

### Safety Measures
- Requires minimum confidence threshold for trap trades
- Validates safe entry points before execution
- Considers higher timeframe context
- Implements strict risk parameters for trap trades

## Testing

The bot includes comprehensive test coverage:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/test_bot.py::TestMarketAnalysis -v
```

## Configuration Reference

### Risk Management
- `max_risk_per_trade`: Maximum risk percentage per trade (default: 2%)
- `trailing_stop_enabled`: Enable/disable trailing stops (default: True)
- `trailing_stop_distance`: Trailing stop distance (default: 0.5%)
- `tp1_ratio`, `tp2_ratio`, `tp3_ratio`: Take profit ratios (default: 1:1, 2:1, 3:1)

### Trap Identification
- `liquidity_threshold`: Minimum liquidity threshold (default: 1%)
- `induction_confirmation_bars`: Bars needed to confirm induction (default: 3)
- `trap_validation_distance`: Distance to validate trap (default: 0.2%)
- `min_trap_size`: Minimum trap size (default: 0.5%)

### Analysis
- `higher_timeframes`: Timeframes for context analysis (default: ["4h", "1d"])
- `confirmation_timeframes`: Timeframes for confirmation (default: ["15m", "1h"])
- `lookback_periods`: Periods to analyze (default: 100)
main

## Contributing

1. Fork the repository
HEAD
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
main

## License

This project is licensed under the MIT License - see the LICENSE file for details.
HEAD


## Disclaimer

This trading bot is for educational and research purposes. Trading financial instruments involves substantial risk of loss. Past performance is not indicative of future results. Use at your own risk.

from utils.config import update_config

# Customize settings
config = update_config(
    max_risk_per_trade=0.01,  # 1% risk per trade
    fractal_period=7,         # 7-period fractals
    trap_detection_enabled=True
)

bot = MetaTradingBot(config)
```

### Advanced Usage
```python
# Get detailed market structure analysis
results = bot.analyze_and_trade('BTCUSD')
structure = results['market_analysis']['market_structure']

print(f"Market Character: {structure['current_character']}")
print(f"Trap Risk: {results['market_analysis']['market_assessment']['trap_risk']}")
print(f"Trading Conditions: {results['market_analysis']['market_assessment']['trading_conditions']}")
```

## 🔬 Technical Analysis Components

### Fractal Analyzer
- Identifies swing highs and lows with configurable period
- Validates fractals within broader market context
- Calculates fractal strength based on multiple factors
- Prevents premature fractal identification

### CHOCH Detector
- Detects Change of Character in market structure
- Confirms breaks with multiple candle validation
- Analyzes swing point relationships
- Provides strength scoring for reliability

### Liquidity Zone Detector
- Identifies multiple types of liquidity zones:
  - Fractal-based zones
  - Equal highs/lows
  - Volume-based zones
  - Session highs/lows
- Detects liquidity sweeps and retests
- Manages zone lifecycle and relevance

### Market Structure Analyzer
- Differentiates false breaks from legitimate moves
- Detects trap patterns (bull/bear/liquidity traps)
- Analyzes momentum confirmation
- Provides market character assessment

## ⚙️ Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `max_risk_per_trade` | 0.02 | Maximum risk per trade (2%) |
| `max_daily_loss` | 0.05 | Maximum daily loss limit (5%) |
| `fractal_period` | 5 | Period for fractal identification |
| `false_break_threshold` | 0.002 | Threshold for false break detection (0.2%) |
| `momentum_confirmation_period` | 5 | Candles for momentum confirmation |
| `trap_detection_enabled` | True | Enable/disable trap detection |
| `auto_reassessment_interval` | 10 | Candles between auto reassessments |

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/test_trading_bot.py -v
```

Or run individual tests:
```bash
cd tests
python test_trading_bot.py
```

## 📈 Performance Metrics

The bot tracks several performance indicators:
- **Reliability Score**: Ratio of legitimate breaks to total breaks
- **Trap Risk Assessment**: Dynamic risk evaluation (0-1 scale)
- **Momentum Clarity**: Multi-timeframe momentum alignment
- **Trading Conditions**: Overall market assessment (excellent/good/fair/average/poor)

## 🔒 Risk Management

### Built-in Risk Controls
- Maximum risk per trade limit
- Daily loss limits
- Position sizing based on confidence levels
- Risk-reward ratio validation (minimum 1.5:1)
- Adaptive confidence thresholds

### Safety Features
- Comprehensive input validation
- Error handling and graceful degradation
- Market condition assessment before trading
- Automatic reassessment triggers

## 🚦 Trading Signals

The bot generates various signal types:
- **Pullback Signals**: Retracements to key levels in trending markets
- **Breakout Signals**: Confirmed breaks of market structure
- **Momentum Continuation**: Follow-through after momentum shifts
- **Sweep Reversals**: Opportunities after liquidity sweeps

Each signal includes:
- Entry price and direction
- Confidence score (0-1)
- Risk level assessment
- Stop loss and take profit levels
- Risk-reward ratio

## 📋 Roadmap

### Planned Features
- [ ] Backtesting engine with historical performance analysis
- [ ] Live trading integration with major brokers
- [ ] Machine learning enhancement for pattern recognition
- [ ] Portfolio management and correlation analysis
- [ ] Advanced risk metrics and reporting
- [ ] Web-based dashboard and monitoring
- [ ] Alert system for high-confidence setups

## ⚠️ Disclaimer

This trading bot is for educational and research purposes. Always:
- Test thoroughly with paper trading before using real money
- Understand the risks involved in trading
- Use proper risk management
- Consider your financial situation and risk tolerance
- Seek professional advice if needed

Trading involves substantial risk of loss and is not suitable for all investors.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions, bug reports, or feature requests:
- Open an issue on GitHub
- Contact: [Your Contact Information]

---

**KAIZEN** - Continuous improvement in trading through advanced technology and rigorous analysis.

3. **Run the unified demo**:
```bash
python demo_unified.py
```

### TradingView Pine Script Setup

1. Copy the content of `kaizen_trading_strategy.pine`
2. Open TradingView Pine Editor (Alt+E)
3. Paste the code and save
4. Add to chart and configure alerts

See `INSTALACION_RAPIDA.md` for detailed TradingView setup instructions.

## 📊 Usage Examples

### Basic Analysis
```python
from src.kaizen_trading_bot import KaizenTradingBot
from utils.config import get_config

# Initialize unified bot
bot = KaizenTradingBot(account_balance=10000.0)

# Analyze with multi-timeframe data
timeframes_data = {
    '1d': daily_data,     # Higher timeframe context
    '4h': h4_data,        # Confirmation
    '1h': h1_data,        # Entry zone identification  
    '15m': m15_data,      # Precise entry timing
    '5m': m5_data         # Scalping opportunities
}

# Comprehensive analysis
results = bot.analyze_market('EURUSD', timeframes_data)

# Get trading recommendation
recommendation = results['trading_recommendation']
print(f"Action: {recommendation['action']}")
print(f"Direction: {recommendation['direction']}")
print(f"Confidence: {recommendation['confidence']:.2f}")
```

### Advanced Configuration
```python
from utils.config import update_config

# Customize for aggressive trading
config = update_config(
    max_risk_per_trade=0.03,        # 3% risk per trade
    min_trap_confidence=0.8,        # Higher trap detection threshold
    strict_htf_priority=True,       # Enforce HTF alignment
    trap_detection_enabled=True     # Enable advanced trap detection
)

bot = KaizenTradingBot(config=config)
```

## 🎯 Merged Pull Request Features

| PR | Title | Key Features Integrated |
|----|-------|------------------------|
| #1 | KAIZEN Professional MetaTrader 5 Bot | Risk management, trailing stops, MT5 integration |
| #2 | Comprehensive Pine Script Strategy | TradingView compatibility, alerts, visual analysis |
| #3 | Multi-Timeframe Trading Bot | HTF context, autonomous analysis, fractal detection |
| #4 | Advanced Trap Identification | Sophisticated trap detection, safe entry validation |
| #5 | Comprehensive Trap Analysis | Distance-based analysis, Model 2 alignment, clean zones |
| #6 | BTCUSD Refined Entry Strategies | Crypto-specific strategies, dynamic risk management |
| #7 | Strict HTF Prioritization | Institutional alignment, smart money flow tracking |

## 🔬 Testing & Validation

Run the comprehensive test suite:
```bash
python -m pytest tests/ -v
```

Or run individual demos:
```bash
python demo_unified.py          # Full feature demonstration
python examples/mt5_demo.py     # MetaTrader 5 specific features
python examples/btc_demo.py     # BTCUSD specialized strategies
```

## 📈 Performance Features

### Risk Management
- **Position Sizing**: Dynamic calculation based on account balance and risk tolerance
- **Trailing Stops**: Automatic stop-loss adjustments to protect profits
- **Multi-Tier Profits**: TP1 (1%), TP2 (2.5%), TP3 (5%) with customizable allocation
- **Daily Limits**: Prevent excessive losses with configurable daily limits

### Signal Quality
- **Confluence Analysis**: Multiple factors must align before signal generation
- **Trap Avoidance**: Advanced detection prevents trading in manipulative conditions
- **HTF Alignment**: All trades must align with higher timeframe bias
- **Confidence Scoring**: Each signal includes confidence score (0-1)

## 🔧 Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `max_risk_per_trade` | 2% | Maximum risk per individual trade |
| `max_daily_loss` | 5% | Maximum daily loss limit |
| `fractal_period` | 5 | Period for fractal identification |
| `min_trap_confidence` | 0.7 | Minimum confidence for trap detection |
| `strict_htf_priority` | True | Enforce higher timeframe priority |
| `trap_detection_enabled` | True | Enable advanced trap detection |

## 🚦 Trading Workflow

1. **Higher Timeframe Analysis**: Establish market bias on D1/4H/1H
2. **Structure Assessment**: Identify key levels, fractals, and market character
3. **Trap Detection**: Screen for potential manipulation and unsafe conditions
4. **Entry Refinement**: Find precise entries on lower timeframes (15M/5M)
5. **Risk Calculation**: Size positions and set stops/targets
6. **Execution**: Only trade when all conditions align

## 📋 Conflict Resolution

During the merge process, conflicts between overlapping implementations were resolved by:

- **Prioritizing higher-quality code** with better error handling
- **Combining complementary features** rather than duplicating functionality
- **Maintaining backward compatibility** with existing configurations
- **Preserving the strengths** of each individual PR
- **Creating unified interfaces** for consistent usage

## ⚠️ Important Notes

- **Test thoroughly** before using with real capital
- **Start with demo accounts** to validate performance
- **Understand risk management** - trading involves substantial risk
- **Monitor performance** and adjust parameters as needed
- **Keep higher timeframe bias** - never trade against institutional flow

## 🤝 Contributing

This unified implementation represents the merger of 6 separate pull requests. For future contributions:

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with the existing unified framework
4. Submit a pull request with clear documentation

## 📄 License

This project combines work from multiple pull requests under MIT License.

## 📞 Support

For questions about the unified implementation:
- Review the comprehensive documentation in each component
- Check the demo scripts for usage examples
- Refer to individual PR documentation for specific features

---

**KAIZEN** - Continuous improvement through advanced technology and unified development.
main

git fetch origin pull/3/head:pr-3
git checkout main
git merge pr-3
main
main
main
main
