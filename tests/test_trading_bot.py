"""
HEAD
Test suite for the BTCUSD trading bot components.
"""
import sys
import os

copilot/fix-63aa93a4-72a5-471a-a5ef-b3c5a75cd0ff
Test suite for Meta Trader Bot
"""

main
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
HEAD
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from trading_bot.config.settings import TradingConfig, validate_config
from trading_bot.analysis.market_structure import MarketStructureAnalyzer, TrendDirection
from trading_bot.risk_management.position_manager import RiskManager, PositionStatus
from trading_bot.validation.entry_validator import EntryValidator, ValidationResult


class TestTradingConfig(unittest.TestCase):
    """Test trading configuration."""
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = TradingConfig(
            exchange_api_key="test",
            exchange_secret="test",
            exchange_passphrase=None,
            exchange_sandbox=True,
            symbol="BTC/USDT",
            base_currency="USDT",
            quote_currency="BTC",
            position_size_percent=2.0,
            max_daily_loss_percent=5.0,
            trailing_stop_percent=1.5,
            tp1_percent=1.0,
            tp2_percent=2.5,
            tp3_percent=5.0,
            tp1_allocation=30,
            tp2_allocation=40,
            tp3_allocation=30,
            min_structure_break_strength=0.7,
            clean_zone_buffer_percent=0.2,
            liquidity_sweep_confirmation_bars=3,
            update_interval_seconds=5,
            volume_analysis_period=20,
            price_action_sensitivity=0.8
        )
        
        self.assertTrue(validate_config(config))
    
    def test_invalid_allocation(self):
        """Test invalid TP allocation validation."""
        config = TradingConfig(
            exchange_api_key="test",
            exchange_secret="test",
            exchange_passphrase=None,
            exchange_sandbox=True,
            symbol="BTC/USDT",
            base_currency="USDT",
            quote_currency="BTC",
            position_size_percent=2.0,
            max_daily_loss_percent=5.0,
            trailing_stop_percent=1.5,
            tp1_percent=1.0,
            tp2_percent=2.5,
            tp3_percent=5.0,
            tp1_allocation=40,  # Invalid: sums to 110
            tp2_allocation=40,
            tp3_allocation=30,
            min_structure_break_strength=0.7,
            clean_zone_buffer_percent=0.2,
            liquidity_sweep_confirmation_bars=3,
            update_interval_seconds=5,
            volume_analysis_period=20,
            price_action_sensitivity=0.8
        )
        
        with self.assertRaises(ValueError):
            validate_config(config)


class TestMarketStructureAnalyzer(unittest.TestCase):
    """Test market structure analysis."""
    
    def setUp(self):
        """Setup test data."""
        self.config = self._create_test_config()
        self.analyzer = MarketStructureAnalyzer(self.config)
        self.test_data = self._create_test_data()
    
    def test_structure_break_detection(self):
        """Test structure break detection."""
        structure_breaks = self.analyzer.analyze_structure_breaks(self.test_data)
        self.assertIsInstance(structure_breaks, list)
    
    def test_liquidity_point_identification(self):
        """Test liquidity point identification."""
        liquidity_points = self.analyzer.identify_liquidity_points(self.test_data)
        self.assertIsInstance(liquidity_points, list)
    
    def test_clean_zone_detection(self):
        """Test clean zone detection."""
        clean_zones = self.analyzer.find_clean_zones(self.test_data)
        self.assertIsInstance(clean_zones, list)
    
    def _create_test_config(self):
        """Create test configuration."""
        return TradingConfig(
            exchange_api_key="test",
            exchange_secret="test",
            exchange_passphrase=None,
            exchange_sandbox=True,
            symbol="BTC/USDT",
            base_currency="USDT",
            quote_currency="BTC",
            position_size_percent=2.0,
            max_daily_loss_percent=5.0,
            trailing_stop_percent=1.5,
            tp1_percent=1.0,
            tp2_percent=2.5,
            tp3_percent=5.0,
            tp1_allocation=30,
            tp2_allocation=40,
            tp3_allocation=30,
            min_structure_break_strength=0.7,
            clean_zone_buffer_percent=0.2,
            liquidity_sweep_confirmation_bars=3,
            update_interval_seconds=5,
            volume_analysis_period=20,
            price_action_sensitivity=0.8
        )
    
    def _create_test_data(self):
        """Create test market data."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='5T')
        
        # Generate realistic OHLCV data
        np.random.seed(42)
        base_price = 45000
        
        data = []
        current_price = base_price
        
        for i in range(100):
            # Random price movement
            change = np.random.normal(0, 200)
            current_price += change
            
            high = current_price + abs(np.random.normal(0, 100))
            low = current_price - abs(np.random.normal(0, 100))
            volume = abs(np.random.normal(1000, 200))
            
            data.append([current_price, high, low, current_price, volume])
        
        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'], index=dates)
        return df


class TestRiskManager(unittest.TestCase):
    """Test risk management."""
    
    def setUp(self):
        """Setup test data."""
        self.config = self._create_test_config()
        self.risk_manager = RiskManager(self.config)
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        account_balance = 10000.0
        entry_price = 45000.0
        
        position_size = self.risk_manager.calculate_position_size(account_balance, entry_price)
        
        # Should be 2% of account / entry_price
        expected_size = (account_balance * 0.02) / entry_price
        self.assertAlmostEqual(position_size, expected_size, places=6)
    
    def test_position_creation(self):
        """Test position creation."""
        entry_price = 45000.0
        size = 0.1
        direction = 'long'
        timestamp = pd.Timestamp.now()
        
        position_id = self.risk_manager.create_position(entry_price, size, direction, timestamp)
        
        self.assertIn(position_id, self.risk_manager.positions)
        position = self.risk_manager.positions[position_id]
        self.assertEqual(position.entry_price, entry_price)
        self.assertEqual(position.size, size)
        self.assertEqual(position.direction, direction)
        self.assertEqual(position.status, PositionStatus.OPEN)
    
    def test_trailing_stop_update(self):
        """Test trailing stop updates."""
        # Create a long position
        position_id = self.risk_manager.create_position(45000.0, 0.1, 'long', pd.Timestamp.now())
        
        # Update with higher price (should update trailing stop)
        updated = self.risk_manager.update_trailing_stop(position_id, 46000.0)
        self.assertTrue(updated)
        
        # Update with lower price (should not update trailing stop)
        updated = self.risk_manager.update_trailing_stop(position_id, 45500.0)
        self.assertFalse(updated)
    
    def _create_test_config(self):
        """Create test configuration."""
        return TradingConfig(
            exchange_api_key="test",
            exchange_secret="test",
            exchange_passphrase=None,
            exchange_sandbox=True,
            symbol="BTC/USDT",
            base_currency="USDT",
            quote_currency="BTC",
            position_size_percent=2.0,
            max_daily_loss_percent=5.0,
            trailing_stop_percent=1.5,
            tp1_percent=1.0,
            tp2_percent=2.5,
            tp3_percent=5.0,
            tp1_allocation=30,
            tp2_allocation=40,
            tp3_allocation=30,
            min_structure_break_strength=0.7,
            clean_zone_buffer_percent=0.2,
            liquidity_sweep_confirmation_bars=3,
            update_interval_seconds=5,
            volume_analysis_period=20,
            price_action_sensitivity=0.8
        )


class TestEntryValidator(unittest.TestCase):
    """Test entry validation."""
    
    def setUp(self):
        """Setup test data."""
        self.config = self._create_test_config()
        self.validator = EntryValidator(self.config)
    
    def test_entry_validation_no_structure_break(self):
        """Test entry validation without structure break."""
        df = self._create_test_data()
        
        # Test with empty structure breaks
        entry_signal = self.validator.validate_entry(
            df=df,
            structure_breaks=[],
            liquidity_points=[],
            clean_zones=[],
            current_price=45000.0,
            timestamp=pd.Timestamp.now()
        )
        
        self.assertEqual(entry_signal.validation_result, ValidationResult.INVALID_NO_STRUCTURE_BREAK)
    
    def _create_test_config(self):
        """Create test configuration."""
        return TradingConfig(
            exchange_api_key="test",
            exchange_secret="test",
            exchange_passphrase=None,
            exchange_sandbox=True,
            symbol="BTC/USDT",
            base_currency="USDT",
            quote_currency="BTC",
            position_size_percent=2.0,
            max_daily_loss_percent=5.0,
            trailing_stop_percent=1.5,
            tp1_percent=1.0,
            tp2_percent=2.5,
            tp3_percent=5.0,
            tp1_allocation=30,
            tp2_allocation=40,
            tp3_allocation=30,
            min_structure_break_strength=0.7,
            clean_zone_buffer_percent=0.2,
            liquidity_sweep_confirmation_bars=3,
            update_interval_seconds=5,
            volume_analysis_period=20,
            price_action_sensitivity=0.8
        )
    
    def _create_test_data(self):
        """Create test market data."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='5T')
        
        # Generate realistic OHLCV data
        np.random.seed(42)
        base_price = 45000
        
        data = []
        current_price = base_price
        
        for i in range(100):
            # Random price movement
            change = np.random.normal(0, 200)
            current_price += change
            
            high = current_price + abs(np.random.normal(0, 100))
            low = current_price - abs(np.random.normal(0, 100))
            volume = abs(np.random.normal(1000, 200))
            
            data.append([current_price, high, low, current_price, volume])
        
        df = pd.DataFrame(data, columns=['open', 'high', 'low', 'close', 'volume'], index=dates)
        return df


if __name__ == '__main__':
    unittest.main()


# Import modules to test
from meta_trader_bot.core.models import TradingConfig, TimeFrame, TradeDirection, RiskLevel
from meta_trader_bot.core.trading_bot import TradingBot
from meta_trader_bot.analyzers.trap_analyzer import TrapAnalyzer
from meta_trader_bot.analyzers.entry_validator import EntryValidator
from meta_trader_bot.analyzers.structural_analyzer import StructuralAnalyzer
from meta_trader_bot.managers.risk_manager import RiskManager
from meta_trader_bot.utils.data_utils import generate_sample_data, validate_ohlcv_data


class TestTradingModels(unittest.TestCase):
    """Test core trading models and data structures."""
    
    def test_trading_config_creation(self):
        """Test TradingConfig object creation."""
        config = TradingConfig()
        self.assertEqual(config.max_risk_per_trade, 0.02)
        self.assertEqual(config.tp1_ratio, 1.0)
        self.assertEqual(config.tp2_ratio, 2.0)
        self.assertEqual(config.tp3_ratio, 3.0)
        self.assertIsInstance(config.timeframes_to_analyze, list)
    
    def test_timeframe_enum(self):
        """Test TimeFrame enum values."""
        self.assertEqual(TimeFrame.M15.value, "15m")
        self.assertEqual(TimeFrame.H1.value, "1h")
        self.assertEqual(TimeFrame.D1.value, "1d")
    
    def test_trade_direction_enum(self):
        """Test TradeDirection enum values."""
        self.assertEqual(TradeDirection.LONG.value, "long")
        self.assertEqual(TradeDirection.SHORT.value, "short")


class TestDataUtils(unittest.TestCase):
    """Test data utility functions."""
    
    def test_validate_ohlcv_data(self):
        """Test OHLCV data validation."""
        # Create valid data
        valid_data = pd.DataFrame({
            'Open': [1.0, 1.1],
            'High': [1.2, 1.3],
            'Low': [0.9, 1.0],
            'Close': [1.1, 1.2],
            'Volume': [1000, 1500]
        })
        self.assertTrue(validate_ohlcv_data(valid_data))
        
        # Create invalid data (High < Low)
        invalid_data = pd.DataFrame({
            'Open': [1.0, 1.1],
            'High': [0.8, 1.0],  # High < Low
            'Low': [0.9, 1.1],
            'Close': [1.1, 1.2]
        })
        self.assertFalse(validate_ohlcv_data(invalid_data))
    
    def test_generate_sample_data(self):
        """Test sample data generation."""
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        data = generate_sample_data(start_date, end_date, TimeFrame.M15)
        
        self.assertIsInstance(data, pd.DataFrame)
        self.assertTrue(len(data) > 0)
        self.assertTrue(all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']))
        self.assertTrue(validate_ohlcv_data(data))


class TestRiskManager(unittest.TestCase):
    """Test risk management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = TradingConfig()
        self.risk_manager = RiskManager(self.config, account_balance=10000.0)
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        entry_price = 1.1000
        stop_loss = 1.0950
        risk_level = RiskLevel.MEDIUM
        
        position_size = self.risk_manager.calculate_position_size(entry_price, stop_loss, risk_level)
        
        self.assertGreater(position_size, 0)
        self.assertIsInstance(position_size, float)
    
    def test_create_position(self):
        """Test position creation."""
        position_id = self.risk_manager.create_position(
            entry_price=1.1000,
            direction=TradeDirection.LONG,
            stop_loss=1.0950
        )
        
        self.assertIsInstance(position_id, str)
        self.assertIn(position_id, self.risk_manager.active_positions)
        
        position = self.risk_manager.active_positions[position_id]
        self.assertEqual(position.entry_price, 1.1000)
        self.assertEqual(position.direction, TradeDirection.LONG)
    
    def test_trailing_stop_calculation(self):
        """Test trailing stop calculation."""
        position_id = self.risk_manager.create_position(
            entry_price=1.1000,
            direction=TradeDirection.LONG,
            stop_loss=1.0950
        )
        
        # Simulate price movement
        current_prices = {position_id: 1.1050}
        updates = self.risk_manager.update_trailing_stops(current_prices)
        
        self.assertIn(position_id, updates)
        position = updates[position_id]['position']
        self.assertIsNotNone(position.trailing_stop)


class TestTrapAnalyzer(unittest.TestCase):
    """Test trap analysis functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = TradingConfig()
        self.trap_analyzer = TrapAnalyzer(self.config)
    
    def test_trap_analyzer_initialization(self):
        """Test TrapAnalyzer initialization."""
        self.assertIsInstance(self.trap_analyzer, TrapAnalyzer)
        self.assertEqual(self.trap_analyzer.config, self.config)
    
    def test_analyze_traps_with_sample_data(self):
        """Test trap analysis with sample data."""
        # Generate sample data
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        price_data = generate_sample_data(start_date, end_date, TimeFrame.M15)
        volume_data = price_data['Volume']
        
        # Analyze traps
        trap_signals = self.trap_analyzer.analyze_traps(price_data, volume_data)
        
        self.assertIsInstance(trap_signals, list)
        # Trap signals may or may not be found in random data


class TestEntryValidator(unittest.TestCase):
    """Test entry validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = TradingConfig()
        self.entry_validator = EntryValidator(self.config)
    
    def test_entry_validator_initialization(self):
        """Test EntryValidator initialization."""
        self.assertIsInstance(self.entry_validator, EntryValidator)
        self.assertEqual(self.entry_validator.config, self.config)
    
    def test_validate_entry_with_sample_data(self):
        """Test entry validation with sample data."""
        # Generate sample data
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        price_data = generate_sample_data(start_date, end_date, TimeFrame.M15)
        current_price = price_data['Close'].iloc[-1]
        
        # Validate entry
        entry_signal = self.entry_validator.validate_entry(price_data, current_price)
        
        # Entry signal may or may not be generated depending on conditions
        if entry_signal:
            self.assertEqual(entry_signal.price, current_price)
            self.assertIn(entry_signal.direction, [TradeDirection.LONG, TradeDirection.SHORT])


class TestStructuralAnalyzer(unittest.TestCase):
    """Test structural analysis functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = TradingConfig()
        self.structural_analyzer = StructuralAnalyzer(self.config)
    
    def test_structural_analyzer_initialization(self):
        """Test StructuralAnalyzer initialization."""
        self.assertIsInstance(self.structural_analyzer, StructuralAnalyzer)
        self.assertEqual(self.structural_analyzer.config, self.config)
    
    def test_analyze_market_structure(self):
        """Test market structure analysis."""
        # Generate sample data for multiple timeframes
        start_date = datetime.now() - timedelta(days=2)
        end_date = datetime.now()
        
        price_data_dict = {}
        for timeframe in self.config.timeframes_to_analyze:
            price_data_dict[timeframe] = generate_sample_data(start_date, end_date, timeframe)
        
        # Analyze market structure
        structures = self.structural_analyzer.analyze_market_structure(price_data_dict)
        
        self.assertIsInstance(structures, dict)
        for timeframe in self.config.timeframes_to_analyze:
            if timeframe in structures:
                structure = structures[timeframe]
                self.assertIn(structure.higher_timeframe_trend, [TradeDirection.LONG, TradeDirection.SHORT])
                self.assertIsInstance(structure.clean_zones, list)
                self.assertIsInstance(structure.key_levels, list)


class TestTradingBot(unittest.TestCase):
    """Test main trading bot functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = TradingConfig()
        self.bot = TradingBot(config=self.config, account_balance=10000.0)
    
    def test_bot_initialization(self):
        """Test TradingBot initialization."""
        self.assertIsInstance(self.bot, TradingBot)
        self.assertEqual(self.bot.account_balance, 10000.0)
        self.assertFalse(self.bot.is_running)
    
    def test_bot_start_stop(self):
        """Test bot start and stop functionality."""
        self.bot.start()
        self.assertTrue(self.bot.is_running)
        
        self.bot.stop()
        self.assertFalse(self.bot.is_running)
    
    def test_analyze_market(self):
        """Test market analysis functionality."""
        # Generate sample data
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        market_data = {}
        for timeframe in self.config.timeframes_to_analyze:
            market_data[timeframe] = generate_sample_data(start_date, end_date, timeframe)
        
        # Start bot and analyze
        self.bot.start()
        analysis = self.bot.analyze_market(market_data)
        
        self.assertIsInstance(analysis, dict)
        self.assertIn('timestamp', analysis)
        self.assertIn('trap_signals', analysis)
        self.assertIn('entry_signals', analysis)
        self.assertIn('market_structures', analysis)
        self.assertIn('risk_metrics', analysis)
    
    def test_get_status(self):
        """Test bot status functionality."""
        status = self.bot.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('is_running', status)
        self.assertIn('account_balance', status)
        self.assertIn('active_positions', status)
        self.assertIn('risk_metrics', status)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete trading system."""
    
    def test_full_trading_workflow(self):
        """Test complete trading workflow from analysis to execution."""
        # Initialize bot
        config = TradingConfig()
        bot = TradingBot(config=config, account_balance=10000.0)
        
        # Generate market data
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        market_data = {}
        for timeframe in config.timeframes_to_analyze:
            market_data[timeframe] = generate_sample_data(start_date, end_date, timeframe)
        
        # Start bot
        bot.start()
        
        # Analyze market
        analysis = bot.analyze_market(market_data)
        self.assertNotIn('error', analysis)
        
        # Evaluate opportunities (may or may not find any)
        opportunity = bot.evaluate_trading_opportunity(market_data, force_analysis=True)
        
        # If opportunity found, test execution
        if opportunity:
            position_id = bot.execute_trade(opportunity)
            self.assertIsNotNone(position_id)
            
            # Test position management
            current_prices = {position_id: opportunity['entry_price'] * 1.001}
            updates = bot.update_positions(current_prices)
            self.assertNotIn('error', updates)
        
        # Test shutdown
        bot.shutdown()
        self.assertFalse(bot.is_running)


Basic tests for the Meta Trading Bot
"""
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from utils.config import get_config
from utils.data_handler import DataHandler
from analysis.fractals import FractalAnalyzer
from analysis.choch_detector import CHOCHDetector
from analysis.liquidity_zones import LiquidityZoneDetector
from trader_bot import MetaTradingBot

class TestTradingBot(unittest.TestCase):
    """Test cases for the trading bot components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = get_config()
        self.data_handler = DataHandler()
        
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='H')
        np.random.seed(42)  # For reproducible tests
        
        # Generate realistic OHLCV data
        close_prices = np.cumsum(np.random.randn(100) * 0.01) + 100
        high_prices = close_prices + np.abs(np.random.randn(100) * 0.005)
        low_prices = close_prices - np.abs(np.random.randn(100) * 0.005)
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = close_prices[0]
        volumes = np.random.randint(1000, 10000, 100)
        
        self.sample_data = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }, index=dates)
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = get_config()
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.timeframes)
        self.assertGreater(len(config.timeframes.higher_timeframes), 0)
        self.assertGreater(len(config.timeframes.lower_timeframes), 0)
    
    def test_data_handler(self):
        """Test data handler functionality"""
        # Test column standardization
        standardized = self.data_handler._standardize_columns(self.sample_data)
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            self.assertIn(col, standardized.columns)
        
        # Test indicator calculation
        with_indicators = self.data_handler.calculate_indicators(self.sample_data)
        self.assertIn('sma_20', with_indicators.columns)
        self.assertIn('rsi', with_indicators.columns)
    
    def test_fractal_analyzer(self):
        """Test fractal identification"""
        fractal_analyzer = FractalAnalyzer(period=5)
        result = fractal_analyzer.identify_fractals(self.sample_data)
        
        # Check that fractal columns are added
        self.assertIn('fractal_high', result.columns)
        self.assertIn('fractal_low', result.columns)
        self.assertIn('fractal_strength', result.columns)
        
        # Check that some fractals are identified
        fractals_found = result['fractal_high'].sum() + result['fractal_low'].sum()
        self.assertGreater(fractals_found, 0)
    
    def test_choch_detector(self):
        """Test CHOCH detection"""
        choch_detector = CHOCHDetector(confirmation_period=3)
        result = choch_detector.detect_choch(self.sample_data)
        
        # Check that CHOCH columns are added
        self.assertIn('choch_bullish', result.columns)
        self.assertIn('choch_bearish', result.columns)
        self.assertIn('market_structure', result.columns)
    
    def test_liquidity_zones(self):
        """Test liquidity zone detection"""
        liquidity_detector = LiquidityZoneDetector()
        result = liquidity_detector.detect_liquidity_zones(self.sample_data)
        
        # Check that liquidity zone columns are added
        self.assertIn('liquidity_zone', result.columns)
        self.assertIn('zone_type', result.columns)
        self.assertIn('zone_strength', result.columns)
    
    def test_trading_bot_initialization(self):
        """Test trading bot initialization"""
        bot = MetaTradingBot()
        
        # Check that bot is properly initialized
        self.assertIsNotNone(bot.config)
        self.assertIsNotNone(bot.timeframe_analyzer)
        self.assertIsNotNone(bot.market_structure_analyzer)
        
        # Check bot status
        status = bot.get_bot_status()
        self.assertIn('capabilities', status)
        self.assertIn('config', status)
    
    def test_integration_workflow(self):
        """Test integrated workflow"""
        # This test would require mock data or external API access
        # For now, we'll test the bot's error handling
        bot = MetaTradingBot()
        
        # Test with invalid symbol (should handle gracefully)
        try:
            result = bot.analyze_and_trade('INVALID_SYMBOL')
            # Should not raise exception, but return error response
            self.assertIn('status', result)
        except Exception as e:
            self.fail(f"Bot should handle invalid symbols gracefully, but raised: {e}")

class TestAnalysisComponents(unittest.TestCase):
    """Test individual analysis components"""
    
    def test_fractal_validation(self):
        """Test fractal validation logic"""
        # Create data with known fractal pattern
        data = pd.DataFrame({
            'open': [1, 2, 3, 4, 3, 2, 1],
            'high': [1.1, 2.1, 3.1, 4.1, 3.1, 2.1, 1.1],
            'low': [0.9, 1.9, 2.9, 3.9, 2.9, 1.9, 0.9],
            'close': [1, 2, 3, 4, 3, 2, 1],
            'volume': [100, 200, 300, 400, 300, 200, 100]
        })
        
        fractal_analyzer = FractalAnalyzer(period=2)
        result = fractal_analyzer.identify_fractals(data)
        
        # The middle point (index 3) should be identified as a fractal high
        # This is a very basic test - in practice, validation would be more complex
        self.assertTrue(result['fractal_high'].sum() > 0)
main

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
main
