"""
Main BTCUSD trading bot with refined logic for high-probability setups.
"""
import pandas as pd
import numpy as np
import ccxt
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from .config.settings import TradingConfig, load_config, validate_config
from .analysis.market_structure import MarketStructureAnalyzer, TrendDirection
from .risk_management.position_manager import RiskManager, PositionStatus
from .validation.entry_validator import EntryValidator, ValidationResult


class BTCUSDTradingBot:
    """
    Advanced BTCUSD trading bot with refined entry strategies and risk management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the trading bot."""
        # Load configuration
        self.config = load_config()
        validate_config(self.config)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.market_analyzer = MarketStructureAnalyzer(self.config)
        self.risk_manager = RiskManager(self.config)
        self.entry_validator = EntryValidator(self.config)
        
        # Initialize exchange connection
        self.exchange = self._setup_exchange()
        
        # Data storage
        self.market_data = pd.DataFrame()
        self.last_update = None
        
        # Trading state
        self.is_running = False
        self.account_balance = 0.0
        
        self.logger.info("BTCUSD Trading Bot initialized successfully")
    
    def start(self):
        """Start the trading bot."""
        try:
            self.is_running = True
            self.logger.info("Starting BTCUSD Trading Bot...")
            
            # Initial setup
            self._update_account_info()
            self._load_initial_data()
            
            # Main trading loop
            while self.is_running:
                self._run_trading_cycle()
                time.sleep(self.config.update_interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot encountered an error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the trading bot."""
        self.is_running = False
        self._close_all_positions()
        self.logger.info("BTCUSD Trading Bot stopped")
    
    def _run_trading_cycle(self):
        """Execute one complete trading cycle."""
        try:
            # 1. Update market data
            self._update_market_data()
            
            # 2. Check for daily reset
            self._check_daily_reset()
            
            # 3. Skip trading if daily loss limit reached
            if self.risk_manager.check_daily_loss_limit():
                self.logger.warning("Daily loss limit reached, skipping trading")
                return
            
            # 4. Update existing positions
            self._update_positions()
            
            # 5. Analyze market structure
            self._analyze_market_structure()
            
            # 6. Check for new entry opportunities
            self._check_entry_opportunities()
            
            # 7. Log status
            self._log_status()
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
    
    def _update_market_data(self):
        """Update market data from exchange."""
        try:
            # Fetch latest OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=self.config.symbol,
                timeframe='5m',
                limit=200
            )
            
            # Convert to DataFrame
            new_data = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            new_data['timestamp'] = pd.to_datetime(new_data['timestamp'], unit='ms')
            new_data.set_index('timestamp', inplace=True)
            
            # Update market data
            if self.market_data.empty:
                self.market_data = new_data
            else:
                # Merge with existing data, avoiding duplicates
                self.market_data = pd.concat([self.market_data, new_data]).drop_duplicates()
                # Keep last 500 bars
                self.market_data = self.market_data.tail(500)
            
            self.last_update = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Failed to update market data: {e}")
    
    def _check_daily_reset(self):
        """Check if we need to reset daily P&L tracking."""
        if self.last_update:
            current_date = datetime.now().date()
            last_date = self.last_update.date()
            
            if current_date > last_date:
                self.risk_manager.reset_daily_pnl()
                self.logger.info("Daily P&L reset for new trading day")
    
    def _update_positions(self):
        """Update existing positions with current market data."""
        if self.market_data.empty:
            return
        
        current_price = self.market_data.iloc[-1]['close']
        current_timestamp = self.market_data.index[-1]
        
        # Update all open positions
        open_positions = [
            (pos_id, pos) for pos_id, pos in self.risk_manager.positions.items()
            if pos.status == PositionStatus.OPEN
        ]
        
        for position_id, position in open_positions:
            # Update trailing stops
            self.risk_manager.update_trailing_stop(position_id, current_price)
            
            # Check exit conditions
            exit_orders = self.risk_manager.check_exit_conditions(
                position_id, current_price, current_timestamp
            )
            
            # Execute exit orders
            for order in exit_orders:
                self.risk_manager.execute_order(order)
                self.logger.info(f"Executed exit order: {order.order_type} at {order.price}")
            
            # Update unrealized P&L
            unrealized_pnl = self.risk_manager.calculate_unrealized_pnl(position_id, current_price)
            self.logger.debug(f"Position {position_id} unrealized P&L: {unrealized_pnl}")
    
    def _analyze_market_structure(self):
        """Analyze current market structure."""
        if len(self.market_data) < 50:
            return
        
        # Analyze structure breaks
        structure_breaks = self.market_analyzer.analyze_structure_breaks(self.market_data)
        
        # Identify liquidity points
        liquidity_points = self.market_analyzer.identify_liquidity_points(self.market_data)
        
        # Find clean zones
        clean_zones = self.market_analyzer.find_clean_zones(self.market_data)
        
        # Check for liquidity sweeps
        current_timestamp = self.market_data.index[-1]
        new_sweeps = self.entry_validator.check_liquidity_sweeps(
            self.market_data, liquidity_points, current_timestamp
        )
        
        if new_sweeps:
            self.logger.info(f"Detected {len(new_sweeps)} new liquidity sweeps")
    
    def _check_entry_opportunities(self):
        """Check for valid entry opportunities."""
        if len(self.market_data) < 50:
            return
        
        current_price = self.market_data.iloc[-1]['close']
        current_timestamp = self.market_data.index[-1]
        
        # Get recent analysis results
        structure_breaks = self.market_analyzer.structure_breaks
        liquidity_points = self.market_analyzer.liquidity_points
        clean_zones = self.market_analyzer.clean_zones
        
        # Validate entry
        entry_signal = self.entry_validator.validate_entry(
            df=self.market_data,
            structure_breaks=structure_breaks,
            liquidity_points=liquidity_points,
            clean_zones=clean_zones,
            current_price=current_price,
            timestamp=current_timestamp
        )
        
        if entry_signal and entry_signal.validation_result == ValidationResult.VALID:
            self._execute_entry(entry_signal)
    
    def _execute_entry(self, entry_signal):
        """Execute a validated entry signal."""
        try:
            # Check if we already have positions in the same direction
            same_direction_positions = [
                pos for pos in self.risk_manager.positions.values()
                if pos.status == PositionStatus.OPEN and pos.direction == entry_signal.direction.value
            ]
            
            if same_direction_positions:
                self.logger.info("Skipping entry - already have position in same direction")
                return
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                self.account_balance, entry_signal.price
            )
            
            if position_size <= 0:
                self.logger.warning("Invalid position size calculated")
                return
            
            # Create position
            position_id = self.risk_manager.create_position(
                entry_price=entry_signal.price,
                size=position_size,
                direction=entry_signal.direction.value,
                timestamp=entry_signal.timestamp
            )
            
            # Log entry
            self.logger.info(
                f"Entered {entry_signal.direction.value} position {position_id} at {entry_signal.price}, "
                f"confidence: {entry_signal.confidence_score:.3f}, "
                f"R/R: {entry_signal.risk_reward_ratio:.2f}"
            )
            
            # In a real implementation, you would place the actual order on the exchange here
            # self._place_market_order(entry_signal.direction.value, position_size)
            
        except Exception as e:
            self.logger.error(f"Failed to execute entry: {e}")
    
    def _update_account_info(self):
        """Update account balance and other info."""
        try:
            # In sandbox mode, use a simulated balance
            if self.config.exchange_sandbox:
                self.account_balance = 10000.0  # $10k demo account
            else:
                balance = self.exchange.fetch_balance()
                self.account_balance = balance[self.config.base_currency]['free']
            
            self.logger.info(f"Account balance: {self.account_balance} {self.config.base_currency}")
            
        except Exception as e:
            self.logger.error(f"Failed to update account info: {e}")
            # Use default demo balance as fallback
            self.account_balance = 10000.0
    
    def _load_initial_data(self):
        """Load initial market data."""
        self.logger.info("Loading initial market data...")
        self._update_market_data()
        
        if not self.market_data.empty:
            self.logger.info(f"Loaded {len(self.market_data)} bars of market data")
        else:
            self.logger.warning("No market data loaded")
    
    def _close_all_positions(self):
        """Close all open positions."""
        open_positions = [
            pos_id for pos_id, pos in self.risk_manager.positions.items()
            if pos.status == PositionStatus.OPEN
        ]
        
        if open_positions:
            self.logger.info(f"Closing {len(open_positions)} open positions")
            # In a real implementation, you would close positions on the exchange here
    
    def _log_status(self):
        """Log current bot status."""
        if len(self.market_data) > 0:
            current_price = self.market_data.iloc[-1]['close']
            open_positions = len([
                pos for pos in self.risk_manager.positions.values()
                if pos.status == PositionStatus.OPEN
            ])
            
            total_pnl = sum(pos.realized_pnl + pos.unrealized_pnl 
                          for pos in self.risk_manager.positions.values())
            
            self.logger.debug(
                f"Price: {current_price:.2f}, Open positions: {open_positions}, "
                f"Total P&L: {total_pnl:.2f}, Daily P&L: {self.risk_manager.daily_pnl:.2f}"
            )
    
    def _setup_exchange(self):
        """Setup exchange connection."""
        try:
            # For demo purposes, we'll use a sandbox exchange
            exchange_class = getattr(ccxt, 'binance')  # You can change this to your preferred exchange
            
            exchange = exchange_class({
                'apiKey': self.config.exchange_api_key,
                'secret': self.config.exchange_secret,
                'sandbox': self.config.exchange_sandbox,
                'enableRateLimit': True,
            })
            
            # Add passphrase for exchanges that require it
            if self.config.exchange_passphrase:
                exchange.passphrase = self.config.exchange_passphrase
            
            self.logger.info(f"Connected to {exchange.name} exchange")
            return exchange
            
        except Exception as e:
            self.logger.error(f"Failed to setup exchange: {e}")
            # Return a mock exchange for testing
            return self._create_mock_exchange()
    
    def _create_mock_exchange(self):
        """Create a mock exchange for testing."""
        class MockExchange:
            def __init__(self):
                self.name = "Mock Exchange"
            
            def fetch_ohlcv(self, symbol, timeframe, limit):
                # Generate mock OHLCV data
                now = int(time.time() * 1000)
                data = []
                base_price = 45000  # Base BTC price
                
                for i in range(limit):
                    timestamp = now - (limit - i) * 5 * 60 * 1000  # 5-minute intervals
                    price = base_price + np.random.normal(0, 500)  # Add some volatility
                    high = price + abs(np.random.normal(0, 100))
                    low = price - abs(np.random.normal(0, 100))
                    volume = abs(np.random.normal(100, 20))
                    
                    data.append([timestamp, price, high, low, price, volume])
                
                return data
            
            def fetch_balance(self):
                return {'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}}
        
        return MockExchange()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_performance_stats(self) -> Dict:
        """Get bot performance statistics."""
        total_trades = len(self.risk_manager.positions)
        winning_trades = len([
            pos for pos in self.risk_manager.positions.values()
            if pos.realized_pnl > 0
        ])
        
        total_realized_pnl = sum(pos.realized_pnl for pos in self.risk_manager.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.risk_manager.positions.values())
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_realized_pnl': total_realized_pnl,
            'total_unrealized_pnl': total_unrealized_pnl,
            'daily_pnl': self.risk_manager.daily_pnl,
            'total_exposure': self.risk_manager.get_total_exposure()
        }