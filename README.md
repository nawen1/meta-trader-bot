# KAIZEN Trading Bot

**Professional automated trading bot with advanced market analysis and risk management**

KAIZEN is a sophisticated trading bot that implements multi-timeframe analysis, autonomous pattern recognition, advanced trap detection, and strict risk management protocols. Built for professional traders who require institutional-grade trading logic with retail accessibility.

## 🎯 Core Features

### Advanced Market Analysis
- **Multi-Timeframe Analysis**: Strict higher timeframe prioritization (D1 > H4 > H1 > M15 > M5)
- **Autonomous Pattern Recognition**: Independent fractal and structure detection without presets
- **Change of Character (CHOCH) Detection**: Automated market structure shift identification
- **Liquidity Analysis**: Smart money flow tracking and liquidity sweep detection
- **Support/Resistance**: Multi-touch level validation with confluence analysis

### Intelligent Entry System
- **Trap Detection**: Bull traps, bear traps, and liquidity trap identification
- **Structure Break Analysis**: Boss (Break of Structure) pattern recognition
- **Clean Zone Identification**: High-probability entry zones with minimal overlap
- **Confluence Trading**: Multiple factor alignment for signal validation
- **Entry Point Validation**: Strict criteria to avoid low-probability setups

### Professional Risk Management
- **Dynamic Position Sizing**: Account balance and risk tolerance based calculations
- **Multi-Tier Take Profits**: TP1, TP2, TP3 with customizable ratios
- **Trailing Stops**: Automatic stop-loss adjustments to protect profits
- **Daily Loss Limits**: Configurable maximum daily loss protection
- **Portfolio Risk Control**: Overall exposure monitoring and limits

### Specialized Strategies
- **BTCUSD Optimized**: Crypto-specific entry strategies and volatility management
- **Market Adaptation**: Automatic adjustment to trending, ranging, and choppy conditions
- **Institutional Alignment**: Ensures all trades follow smart money flow direction

## 🚀 Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration Setup
```bash
cp .env.example .env
# Edit .env with your trading preferences and API credentials
```

### 4. Run the Bot
```bash
python src/kaizen_trading_bot.py
```

## 📁 Project Structure

```
meta-trader-bot/
├── src/
│   ├── kaizen_trading_bot.py      # Main entry point - start here
│   ├── meta_trader_bot.py         # MetaTrader 5 integration
│   ├── entry_signals.py          # Signal generation logic
│   ├── market_structure.py       # Market structure analysis
│   ├── liquidity_analyzer.py     # Liquidity detection
│   ├── config.py                 # Configuration settings
│   └── trading_bot/              # Core trading modules
│       ├── bot.py                # Trading bot orchestrator
│       ├── analysis/             # Market analysis components
│       ├── risk_management/      # Position and risk management
│       └── validation/           # Entry validation logic
├── utils/
│   ├── config.py                 # Unified configuration management
│   └── data_handler.py           # Data processing utilities
├── tests/
│   ├── test_trading_bot.py       # Comprehensive test suite
│   └── test_bot.py               # Basic functionality tests
├── examples/                     # Usage examples and demos
├── requirements.txt              # Clean, optimized dependencies
└── README.md                     # This file
```

## ⚙️ Configuration

The bot uses a flexible configuration system. Key settings include:

### Risk Management
```python
max_risk_per_trade = 0.02         # 2% maximum risk per trade
max_daily_loss = 0.05             # 5% maximum daily loss limit
trailing_stop_distance = 0.015    # 1.5% trailing stop distance
```

### Timeframe Settings
```python
higher_timeframes = ['1d', '4h', '1h']    # Context analysis
lower_timeframes = ['15m', '5m', '1m']    # Entry timing
strict_htf_priority = True                # Enforce HTF alignment
```

### Entry Criteria
```python
min_entry_confidence = 0.8        # 80% minimum confidence threshold
trap_detection_enabled = True     # Enable advanced trap detection
require_higher_tf_alignment = True # Require HTF confirmation
```

### Take Profit Levels
```python
tp1_ratio = 1.0                   # 1:1 risk-reward for TP1
tp2_ratio = 2.5                   # 2.5:1 risk-reward for TP2
tp3_ratio = 5.0                   # 5:1 risk-reward for TP3
```

## 📊 Usage Examples

### Basic Market Analysis
```python
from src.kaizen_trading_bot import KaizenTradingBot
from utils.config import get_config

# Initialize bot
bot = KaizenTradingBot(account_balance=10000.0)

# Prepare multi-timeframe data
timeframes_data = {
    '1d': daily_data,      # Higher timeframe context
    '4h': h4_data,         # Intermediate structure
    '1h': h1_data,         # Entry zone identification
    '15m': m15_data,       # Precise entry timing
    '5m': m5_data          # Fine-tuned execution
}

# Analyze market
results = bot.analyze_market('EURUSD', timeframes_data)

# Get trading recommendation
recommendation = results['trading_recommendation']
print(f"Action: {recommendation['action']}")
print(f"Direction: {recommendation['direction']}")
print(f"Confidence: {recommendation['confidence']:.2%}")
```

### Custom Configuration
```python
from utils.config import update_config

# Create custom settings
config = update_config(
    max_risk_per_trade=0.03,        # 3% risk per trade
    min_trap_confidence=0.8,        # Higher trap detection threshold
    strict_htf_priority=True,       # Enforce HTF alignment
    trap_detection_enabled=True     # Enable trap detection
)

bot = KaizenTradingBot(config=config, account_balance=10000.0)
```

### BTCUSD Specialized Trading
```python
# Bot automatically applies BTCUSD-specific strategies when symbol contains 'BTC'
btc_results = bot.analyze_market('BTCUSD', timeframes_data)

# Access BTCUSD-specific analysis
btc_structure = btc_results['market_structure']
print(f"Structure Breaks: {len(btc_structure['structure_breaks'])}")
print(f"Clean Zones: {len(btc_structure['clean_zones'])}")
```

## 🧪 Testing

### Run Complete Test Suite
```bash
python -m pytest tests/ -v
```

### Run Basic Tests
```bash
python tests/test_trading_bot.py
```

### Demo Mode
```bash
python examples/demo_unified.py
```

## 🛠️ Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in the project root directory
cd meta-trader-bot
python -c "import src.kaizen_trading_bot; print('Success')"
```

**Missing Dependencies**
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

**Configuration Issues**
```bash
# Check configuration
python -c "from utils.config import get_config; print(get_config())"
```

**Data Format Issues**
- Ensure OHLCV data is in pandas DataFrame format
- Required columns: 'open', 'high', 'low', 'close', 'volume'
- Index should be datetime-based

### Performance Optimization

**For High-Frequency Analysis**
```python
# Optimize for speed
config = update_config(
    fractal_period=3,              # Faster fractal detection
    auto_reassessment_interval=5,  # More frequent updates
    lookback_periods=50            # Reduced history analysis
)
```

**For Conservative Trading**
```python
# Optimize for safety
config = update_config(
    min_entry_confidence=0.9,      # Higher confidence threshold
    max_risk_per_trade=0.01,       # Lower risk per trade
    strict_htf_priority=True       # Strict timeframe alignment
)
```

## 📈 Best Practices

### 1. Always Start with Higher Timeframes
- Analyze D1 and H4 for overall market bias
- Use H1 for intermediate structure confirmation
- Execute entries on M15 or M5 only when aligned

### 2. Respect Risk Management Rules
- Never risk more than 2% per trade
- Set daily loss limits and stick to them
- Use proper position sizing based on stop-loss distance

### 3. Quality Over Quantity
- Wait for high-confluence setups (80%+ confidence)
- Avoid trading during high trap risk conditions
- Focus on clean entry zones with minimal overlap

### 4. Monitor Market Conditions
- Avoid trading in choppy/manipulative conditions
- Adapt position sizing based on volatility
- Consider session times and major news events

### 5. Continuous Learning
- Review trade results and analyze performance
- Adjust configuration based on market conditions
- Stay updated with market structure changes

## 🔧 Advanced Features

### MetaTrader 5 Integration
```python
# Enable MT5 integration (when available)
config = update_config(
    mt5_enabled=True,
    mt5_login="your_login",
    mt5_password="your_password",
    mt5_server="your_server"
)
```

### Custom Indicators
```python
# Add custom analysis
def custom_analysis(data):
    # Your custom logic here
    return analysis_result

bot.add_custom_analysis(custom_analysis)
```

### Export Analysis
```python
# Export detailed analysis to JSON
filename = bot.export_analysis()
print(f"Analysis saved to {filename}")
```

## ⚠️ Risk Disclaimer

**Important:** This trading bot is for educational and research purposes. Trading financial instruments involves substantial risk of loss and may not be suitable for all investors. 

- **Test thoroughly** in demo mode before using real capital
- **Understand all risks** before trading with real money
- **Use proper risk management** at all times
- **Past performance** does not guarantee future results
- **Market conditions** can change rapidly

The authors are not responsible for any financial losses incurred through the use of this software.

## 📞 Support & Contributing

### Getting Help
- Check the [troubleshooting section](#troubleshooting) first
- Review example usage in the `examples/` folder
- Create an issue on GitHub for bugs or feature requests

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**KAIZEN** - Continuous improvement through advanced technology and disciplined trading principles.

*"In trading, as in Kaizen, small continuous improvements lead to extraordinary results."*