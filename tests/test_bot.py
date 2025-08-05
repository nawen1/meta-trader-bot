"""
Basic tests for the MetaTraderBot components.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.timeframe_analyzer import TimeframeAnalyzer
from src.market_structure import MarketStructureAnalyzer
from src.liquidity_analyzer import LiquidityAnalyzer
from src.support_resistance import SupportResistanceAnalyzer
from src.meta_trader_bot import MetaTraderBot


class TestTimeframeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TimeframeAnalyzer()
    
    def test_timeframe_priorities(self):
        """Test timeframe priority system."""
        self.assertEqual(self.analyzer.get_timeframe_priority('D1'), 5)
        self.assertEqual(self.analyzer.get_timeframe_priority('M5'), 1)
        self.assertTrue(self.analyzer.is_higher_timeframe('D1', 'H1'))
        self.assertFalse(self.analyzer.is_higher_timeframe('M5', 'H1'))
    
    def test_higher_lower_timeframes(self):
        """Test getting higher and lower timeframes."""
        higher_tfs = self.analyzer.get_higher_timeframes('H1')
        self.assertIn('D1', higher_tfs)
        self.assertIn('H4', higher_tfs)
        
        lower_tfs = self.analyzer.get_lower_timeframes('H1')
        self.assertIn('M15', lower_tfs)
        self.assertIn('M5', lower_tfs)


class TestMarketStructureAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketStructureAnalyzer()
        self.sample_data = self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        
        prices = []
        base_price = 1.2000
        for i in range(100):
            price_change = np.random.normal(0, 0.001)
            base_price *= (1 + price_change)
            prices.append(base_price)
        
        data = []
        for i, close in enumerate(prices):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.001)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.001)))
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': np.random.randint(1000, 5000)
            })
        
        return pd.DataFrame(data, index=dates)
    
    def test_market_structure_analysis(self):
        """Test basic market structure analysis."""
        analysis = self.analyzer.analyze_market_structure(self.sample_data)
        
        self.assertIn('swing_highs', analysis)
        self.assertIn('swing_lows', analysis)
        self.assertIn('current_trend', analysis)
        self.assertIn('choch_signals', analysis)
        self.assertIn('bos_signals', analysis)


class TestLiquidityAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = LiquidityAnalyzer()
        self.sample_data = self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data with volume."""
        dates = pd.date_range(start='2023-01-01', periods=50, freq='H')
        np.random.seed(42)
        
        data = []
        base_price = 1.2000
        for i in range(50):
            price_change = np.random.normal(0, 0.002)
            base_price *= (1 + price_change)
            
            open_price = base_price
            close = base_price * (1 + np.random.normal(0, 0.001))
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.002)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.002)))
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data, index=dates)
    
    def test_liquidity_analysis(self):
        """Test liquidity analysis."""
        analysis = self.analyzer.analyze_liquidity(self.sample_data)
        
        self.assertIn('liquidity_pools', analysis)
        self.assertIn('liquidity_sweeps', analysis)
        self.assertIn('liquidity_zones', analysis)
        self.assertIn('liquidity_imbalance', analysis)


class TestSupportResistanceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SupportResistanceAnalyzer()
        self.sample_data = self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data with clear S/R levels."""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        
        # Create data with obvious support/resistance at 1.2000
        data = []
        base_price = 1.2000
        support_level = 1.1950
        resistance_level = 1.2050
        
        for i in range(100):
            # Create price that bounces off support/resistance
            if i % 20 < 5:  # Touch support/resistance occasionally
                if i % 40 < 20:
                    close = support_level + np.random.normal(0, 0.0005)
                else:
                    close = resistance_level + np.random.normal(0, 0.0005)
            else:
                close = base_price + np.random.normal(0, 0.001)
            
            open_price = close + np.random.normal(0, 0.0005)
            high = max(open_price, close) + abs(np.random.normal(0, 0.001))
            low = min(open_price, close) - abs(np.random.normal(0, 0.001))
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': np.random.randint(1000, 5000)
            })
        
        return pd.DataFrame(data, index=dates)
    
    def test_support_resistance_analysis(self):
        """Test support/resistance analysis."""
        analysis = self.analyzer.analyze_support_resistance(self.sample_data)
        
        self.assertIn('support_levels', analysis)
        self.assertIn('resistance_levels', analysis)
        self.assertIn('key_levels', analysis)
        self.assertIn('nearest_support', analysis)
        self.assertIn('nearest_resistance', analysis)


class TestMetaTraderBot(unittest.TestCase):
    def setUp(self):
        self.bot = MetaTraderBot()
        self.sample_data = self._create_multi_tf_data()
    
    def _create_multi_tf_data(self):
        """Create multi-timeframe sample data."""
        data = {}
        timeframes = ['D1', 'H4', 'H1', 'M15']
        
        for tf in timeframes:
            periods = 50 if tf == 'D1' else 100
            freq = {'D1': 'D', 'H4': '4H', 'H1': 'H', 'M15': '15T'}[tf]
            
            dates = pd.date_range(start='2023-01-01', periods=periods, freq=freq)
            np.random.seed(42)
            
            sample_data = []
            base_price = 1.2000
            for i in range(periods):
                price_change = np.random.normal(0, 0.001)
                base_price *= (1 + price_change)
                
                open_price = base_price
                close = base_price * (1 + np.random.normal(0, 0.0005))
                high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.001)))
                low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.001)))
                
                sample_data.append({
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': np.random.randint(1000, 10000)
                })
            
            data[tf] = pd.DataFrame(sample_data, index=dates)
        
        return data
    
    def test_market_analysis(self):
        """Test comprehensive market analysis."""
        analysis = self.bot.analyze_market(self.sample_data)
        
        self.assertIn('timeframe_hierarchy', analysis)
        self.assertIn('market_context', analysis)
        self.assertIn('timeframe_analyses', analysis)
        self.assertIn('key_zones', analysis)
        self.assertIn('trading_recommendation', analysis)
    
    def test_entry_signal_generation(self):
        """Test entry signal generation."""
        # First analyze the market
        self.bot.analyze_market(self.sample_data)
        
        # Then generate signals
        signals = self.bot.generate_entry_signals(self.sample_data, 'H1')
        
        self.assertIn('entry_allowed', signals)
        self.assertIn('signals', signals)
        self.assertIn('timeframe_analysis', signals)
    
    def test_market_summary(self):
        """Test market summary generation."""
        # Analyze market first
        self.bot.analyze_market(self.sample_data)
        
        summary = self.bot.get_market_summary()
        
        self.assertIn('overall_bias', summary)
        self.assertIn('trend_strength', summary)
        self.assertIn('higher_tf_bias', summary)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)