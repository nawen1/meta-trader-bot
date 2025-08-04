"""
Test suite for Meta Trader Bot
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)