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

1. **Clone the repository**:
```bash
git clone https://github.com/nawen1/meta-trader-bot.git
cd meta-trader-bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

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
