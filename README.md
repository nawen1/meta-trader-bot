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

## Installation

```bash
# Clone the repository
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot

# Install dependencies
pip install -r requirements.txt

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
```

### Custom Configuration
```python
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
```

## Architecture

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

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This trading bot is for educational and research purposes. Trading financial instruments involves substantial risk of loss. Past performance is not indicative of future results. Use at your own risk.
