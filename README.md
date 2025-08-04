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

1. **Clone the repository**:
```bash
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

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
```

### Custom Configuration
```python
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
