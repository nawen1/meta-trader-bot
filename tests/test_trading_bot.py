"""
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

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)