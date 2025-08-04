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

```bash
python -m pytest tests/ -v
```

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
