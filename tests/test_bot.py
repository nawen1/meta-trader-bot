"""
copilot/fix-a472e9a1-ed5c-4ecc-aa4f-d8d6469e04b4
Basic tests for the MetaTraderBot components.
"""


Test suite for the Meta Trading Bot
"""
main
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

copilot/fix-a472e9a1-ed5c-4ecc-aa4f-d8d6469e04b4
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

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bot.config import BotConfig, RiskManagementConfig, TrapIdentificationConfig
from bot.market_analysis import MarketAnalyzer, LiquidityLevel, TrapSignal
from bot.risk_management import RiskManager, Position, PositionStatus
from bot.trade_executor import TradeExecutor, TradeValidationResult
from bot.main import MetaTradingBot


class TestBotConfiguration(unittest.TestCase):
    """Test bot configuration"""
    
    def test_default_config_creation(self):
        """Test that default configuration is created correctly"""
        config = BotConfig()
        
        # Check default values
        self.assertEqual(config.risk_management.max_risk_per_trade, 0.02)
        self.assertTrue(config.risk_management.trailing_stop_enabled)
        self.assertEqual(config.risk_management.tp1_ratio, 1.0)
        self.assertEqual(config.risk_management.tp2_ratio, 2.0)
        self.assertEqual(config.risk_management.tp3_ratio, 3.0)
        
        self.assertEqual(config.min_entry_confidence, 0.75)
        self.assertFalse(config.force_trades)
        self.assertTrue(config.enable_trap_trading)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid configuration
        config = BotConfig(
            risk_management=RiskManagementConfig(max_risk_per_trade=0.01),
            min_entry_confidence=0.8
        )
        
        self.assertEqual(config.risk_management.max_risk_per_trade, 0.01)
        self.assertEqual(config.min_entry_confidence, 0.8)


class TestMarketAnalysis(unittest.TestCase):
    """Test market analysis functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.config = BotConfig()
        self.analyzer = MarketAnalyzer(self.config)
        
        # Create sample OHLCV data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)
        
        # Generate realistic price data
        price_base = 1.1000
        price_changes = np.random.normal(0, 0.001, 100)
        prices = [price_base]
        
        for change in price_changes[:-1]:
            prices.append(prices[-1] * (1 + change))
        
        self.df = pd.DataFrame({
            'open': [p * (1 + np.random.normal(0, 0.0001)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        # Ensure high >= close >= low and high >= open >= low
        for i in range(len(self.df)):
            row = self.df.iloc[i]
            max_price = max(row['open'], row['close'])
            min_price = min(row['open'], row['close'])
            
            self.df.iloc[i, self.df.columns.get_loc('high')] = max(row['high'], max_price)
            self.df.iloc[i, self.df.columns.get_loc('low')] = min(row['low'], min_price)
    
    def test_liquidity_level_identification(self):
        """Test liquidity level identification"""
        liquidity_levels = self.analyzer.identify_liquidity_levels(self.df)
        
        # Should find some liquidity levels
        self.assertIsInstance(liquidity_levels, list)
        
        # Check structure of liquidity levels
        if liquidity_levels:
            level = liquidity_levels[0]
            self.assertIsInstance(level, LiquidityLevel)
            self.assertIn(level.level_type, ['support', 'resistance'])
            self.assertGreater(level.volume, 0)
    
    def test_induction_identification(self):
        """Test induction identification"""
        inductions = self.analyzer.identify_inductions(self.df)
        
        self.assertIsInstance(inductions, list)
        
        # Check structure if inductions found
        for induction in inductions:
            self.assertIn('type', induction)
            self.assertIn(induction['type'], ['bullish_induction', 'bearish_induction'])
            self.assertIn('entry_bar', induction)
            self.assertIn('strength', induction)
            self.assertGreaterEqual(induction['strength'], 0)
            self.assertLessEqual(induction['strength'], 1)
    
    def test_trap_identification(self):
        """Test trap identification"""
        liquidity_levels = self.analyzer.identify_liquidity_levels(self.df)
        trap_signals = self.analyzer.identify_traps(self.df, liquidity_levels)
        
        self.assertIsInstance(trap_signals, list)
        
        # Check structure of trap signals
        for trap in trap_signals:
            self.assertIsInstance(trap, TrapSignal)
            self.assertIn(trap.trap_type, ['bull_trap', 'bear_trap'])
            self.assertGreater(trap.entry_price, 0)
            self.assertGreater(trap.stop_loss, 0)
            self.assertIsInstance(trap.take_profits, list)
            self.assertGreaterEqual(trap.confidence, 0)
            self.assertLessEqual(trap.confidence, 1)


class TestRiskManagement(unittest.TestCase):
    """Test risk management functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.config = BotConfig()
        self.risk_manager = RiskManager(self.config)
    
    def test_position_size_calculation(self):
        """Test position size calculation"""
        account_balance = 10000.0
        entry_price = 1.1000
        stop_loss = 1.0900  # 100 pip stop
        
        position_size = self.risk_manager.calculate_position_size(
            account_balance, entry_price, stop_loss
        )
        
        # Position size should be positive
        self.assertGreater(position_size, 0)
        
        # Risk should not exceed configured maximum
        risk_amount = abs(entry_price - stop_loss) * position_size
        max_risk = account_balance * self.config.risk_management.max_risk_per_trade
        self.assertLessEqual(risk_amount, max_risk * 1.01)  # Allow small rounding error
    
    def test_position_opening(self):
        """Test position opening"""
        position_id = self.risk_manager.open_position(
            symbol="EURUSD",
            entry_price=1.1000,
            size=10000,
            direction="long",
            stop_loss=1.0900,
            take_profits=[1.1100, 1.1200, 1.1300]
        )
        
        self.assertIsInstance(position_id, str)
        self.assertIn(position_id, self.risk_manager.positions)
        
        position = self.risk_manager.positions[position_id]
        self.assertEqual(position.entry_price, 1.1000)
        self.assertEqual(position.size, 10000)
        self.assertEqual(position.direction, "long")
        self.assertEqual(position.status, PositionStatus.OPEN)
    
    def test_trailing_stop_updates(self):
        """Test trailing stop updates"""
        position_id = self.risk_manager.open_position(
            symbol="EURUSD",
            entry_price=1.1000,
            size=10000,
            direction="long",
            stop_loss=1.0900,
            take_profits=[1.1100, 1.1200, 1.1300]
        )
        
        # Price moves favorably
        updated = self.risk_manager.update_trailing_stop(position_id, 1.1050)
        position = self.risk_manager.positions[position_id]
        
        # Should update max favorable price
        self.assertEqual(position.max_favorable_price, 1.1050)
        
        # Price moves more favorably
        self.risk_manager.update_trailing_stop(position_id, 1.1100)
        
        # Stop should trail higher
        self.assertGreater(position.current_stop_loss, 1.0900)
    
    def test_exit_conditions(self):
        """Test exit condition checking"""
        position_id = self.risk_manager.open_position(
            symbol="EURUSD",
            entry_price=1.1000,
            size=10000,
            direction="long",
            stop_loss=1.0900,
            take_profits=[1.1100, 1.1200, 1.1300]
        )
        
        # Test stop loss hit
        result = self.risk_manager.check_exit_conditions(position_id, 1.0890)
        self.assertIsNotNone(result)
        
        # Position should be closed
        self.assertNotIn(position_id, self.risk_manager.positions)


class TestTradeExecution(unittest.TestCase):
    """Test trade execution functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.config = BotConfig()
        self.risk_manager = RiskManager(self.config)
        self.trade_executor = TradeExecutor(self.config, self.risk_manager)
    
    def test_trap_trade_validation(self):
        """Test trap trade validation"""
        trap_signal = TrapSignal(
            entry_price=1.1000,
            stop_loss=1.0950,
            take_profits=[1.1050, 1.1100, 1.1150],
            confidence=0.8,
            trap_type='bull_trap',
            liquidity_above=1000,
            liquidity_below=2000,
            safe_entry_exists=True
        )
        
        market_context = {
            'volatility': 1.0,
            'spread': 0.001,
            'higher_timeframe_structure': {}
        }
        
        trade_setup = self.trade_executor.validate_trap_trade(
            trap_signal, market_context, 10000.0
        )
        
        self.assertEqual(trade_setup.validation_result, TradeValidationResult.VALID)
        self.assertGreater(trade_setup.position_size, 0)
        self.assertTrue(trade_setup.is_trap_trade)


class TestMainBot(unittest.TestCase):
    """Test main bot functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.bot = MetaTradingBot(account_balance=10000.0)
        
        # Generate sample market data
        self.market_data = self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample market data for testing"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='15min')
        np.random.seed(42)
        
        price_base = 1.1000
        price_changes = np.random.normal(0, 0.001, 100)
        prices = [price_base]
        
        for change in price_changes[:-1]:
            prices.append(prices[-1] * (1 + change))
        
        df = pd.DataFrame({
            'open': [p * (1 + np.random.normal(0, 0.0001)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'close': prices,
            'volume': np.random.uniform(1000, 10000, 100)
        }, index=dates)
        
        # Ensure OHLC consistency
        for i in range(len(df)):
            row = df.iloc[i]
            max_price = max(row['open'], row['close'])
            min_price = min(row['open'], row['close'])
            
            df.iloc[i, df.columns.get_loc('high')] = max(row['high'], max_price)
            df.iloc[i, df.columns.get_loc('low')] = min(row['low'], min_price)
        
        return {'15m': df, '1h': df.resample('1H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })}
    
    def test_market_analysis(self):
        """Test market analysis"""
        market_context = self.bot.analyze_market("EURUSD", self.market_data)
        
        self.assertIsInstance(market_context, dict)
        self.assertIn('symbol', market_context)
        self.assertIn('timestamp', market_context)
        self.assertIn('liquidity_levels', market_context)
        self.assertIn('trap_signals', market_context)
        self.assertIn('market_metrics', market_context)
    
    def test_signal_generation(self):
        """Test signal generation"""
        market_context = self.bot.analyze_market("EURUSD", self.market_data)
        signals = self.bot.generate_trading_signals(market_context)
        
        self.assertIsInstance(signals, list)
        
        # Check signal structure
        for signal in signals:
            self.assertIn('signal_type', signal)
            self.assertIn('validation_result', signal)
    
    def test_trading_cycle(self):
        """Test complete trading cycle"""
        current_prices = {"EURUSD": 1.1000}
        
        results = self.bot.run_trading_cycle("EURUSD", self.market_data, current_prices)
        
        self.assertIsInstance(results, dict)
        self.assertIn('cycle_duration_seconds', results)
        self.assertIn('market_analysis', results)
        self.assertIn('signals_generated', results)
        self.assertIn('portfolio_status', results)
main


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)