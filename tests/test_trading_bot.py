"""
Test suite for the BTCUSD trading bot components.
"""
import sys
import os
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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