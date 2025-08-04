# Meta Trader Bot

KAIZEN - Advanced Trading Bot with sophisticated trap analysis and risk management.

## Features

- **Advanced Trap Recognition**: Identifies traps from distance based on liquidity analysis
- **Strict Entry Validation**: Operates only on clear entry points aligned with trading models
- **Dynamic Risk Management**: Implements trailing stops and position management (TP1/TP2/TP3)
- **Structural Analysis**: Multi-timeframe analysis with clean zone identification

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from meta_trader_bot import TradingBot

bot = TradingBot()
bot.start()
```

## Architecture

- `core/`: Main trading bot orchestrator
- `analyzers/`: Market analysis modules (trap detection, structural analysis)
- `managers/`: Risk and trade management modules  
- `utils/`: Utility functions and helpers
- `config/`: Configuration files and settings
