"""
Data handler for market data management and processing
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataHandler:
    """Handles market data fetching, processing, and management"""
    
    def __init__(self):
        self.data_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.last_update: Dict[str, datetime] = {}
    
    def fetch_data(self, symbol: str, timeframe: str, periods: int = 1000) -> pd.DataFrame:
        """
        Fetch market data for given symbol and timeframe
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'BTCUSD')
            timeframe: Timeframe (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            periods: Number of periods to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Create cache key
            cache_key = f"{symbol}_{timeframe}"
            
            # Check if we need to update cache
            if self._should_update_cache(cache_key):
                logger.info(f"Fetching data for {symbol} on {timeframe}")
                
                # Convert timeframe to yfinance format
                yf_interval = self._convert_timeframe(timeframe)
                
                # Calculate period for yfinance
                end_date = datetime.now()
                start_date = self._calculate_start_date(timeframe, periods)
                
                # Fetch data using yfinance (for demo purposes)
                ticker = yf.Ticker(symbol)
                data = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=yf_interval
                )
                
                if data.empty:
                    logger.warning(f"No data found for {symbol}")
                    return pd.DataFrame()
                
                # Standardize column names
                data = self._standardize_columns(data)
                
                # Cache the data
                if symbol not in self.data_cache:
                    self.data_cache[symbol] = {}
                self.data_cache[symbol][timeframe] = data
                self.last_update[cache_key] = datetime.now()
                
                return data
            else:
                # Return cached data
                return self.data_cache[symbol][timeframe]
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_multiple_timeframes(self, symbol: str, timeframes: List[str], periods: int = 1000) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple timeframes
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes
            periods: Number of periods per timeframe
            
        Returns:
            Dictionary with timeframe as key and DataFrame as value
        """
        result = {}
        for tf in timeframes:
            result[tf] = self.fetch_data(symbol, tf, periods)
        return result
    
    def _should_update_cache(self, cache_key: str) -> bool:
        """Check if cache should be updated"""
        if cache_key not in self.last_update:
            return True
        
        # Update if last update was more than 1 minute ago
        return (datetime.now() - self.last_update[cache_key]).seconds > 60
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to yfinance format"""
        mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1wk',
            '1M': '1mo'
        }
        return mapping.get(timeframe, '1h')
    
    def _calculate_start_date(self, timeframe: str, periods: int) -> datetime:
        """Calculate start date based on timeframe and periods"""
        now = datetime.now()
        
        if timeframe == '1m':
            return now - timedelta(minutes=periods)
        elif timeframe == '5m':
            return now - timedelta(minutes=periods * 5)
        elif timeframe == '15m':
            return now - timedelta(minutes=periods * 15)
        elif timeframe == '30m':
            return now - timedelta(minutes=periods * 30)
        elif timeframe == '1h':
            return now - timedelta(hours=periods)
        elif timeframe == '4h':
            return now - timedelta(hours=periods * 4)
        elif timeframe == '1d':
            return now - timedelta(days=periods)
        else:
            return now - timedelta(days=periods)
    
    def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to OHLCV format"""
        column_mapping = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        
        # Rename columns
        data = data.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                if col == 'volume':
                    data[col] = 0  # Set volume to 0 if not available
                else:
                    logger.warning(f"Missing required column: {col}")
        
        return data[required_cols]
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate common technical indicators"""
        if data.empty:
            return data
        
        # Simple moving averages
        data['sma_20'] = data['close'].rolling(window=20).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean()
        data['sma_200'] = data['close'].rolling(window=200).mean()
        
        # Exponential moving averages
        data['ema_20'] = data['close'].ewm(span=20).mean()
        data['ema_50'] = data['close'].ewm(span=50).mean()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Average True Range)
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        data['atr'] = tr.rolling(window=14).mean()
        
        return data