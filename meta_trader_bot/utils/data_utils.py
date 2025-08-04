"""
Data utilities for handling market data and analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..core.models import TimeFrame


def validate_ohlcv_data(data: pd.DataFrame) -> bool:
    """
    Validate OHLCV data format and completeness.
    
    Args:
        data: DataFrame with OHLCV data
        
    Returns:
        True if data is valid, False otherwise
    """
    required_columns = ['Open', 'High', 'Low', 'Close']
    
    # Check required columns exist
    if not all(col in data.columns for col in required_columns):
        return False
        
    # Check for empty data
    if len(data) == 0:
        return False
        
    # Check for valid price relationships
    valid_prices = (
        (data['High'] >= data['Open']) & 
        (data['High'] >= data['Close']) &
        (data['Low'] <= data['Open']) & 
        (data['Low'] <= data['Close']) &
        (data['High'] >= data['Low'])
    )
    
    return valid_prices.all()


def resample_timeframe(data: pd.DataFrame, target_timeframe: TimeFrame) -> pd.DataFrame:
    """
    Resample data to target timeframe.
    
    Args:
        data: Source OHLCV data
        target_timeframe: Target timeframe for resampling
        
    Returns:
        Resampled data
    """
    if not validate_ohlcv_data(data):
        raise ValueError("Invalid OHLCV data provided")
        
    # Map timeframes to pandas frequency strings
    freq_map = {
        TimeFrame.M1: '1min',
        TimeFrame.M5: '5min',
        TimeFrame.M15: '15min',
        TimeFrame.M30: '30min',
        TimeFrame.H1: '1h',
        TimeFrame.H4: '4h',
        TimeFrame.D1: '1D'
    }
    
    freq = freq_map.get(target_timeframe)
    if not freq:
        raise ValueError(f"Unsupported timeframe: {target_timeframe}")
        
    # Ensure index is datetime
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
        
    # Resample OHLCV data
    resampled = data.resample(freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum' if 'Volume' in data.columns else lambda x: 0
    })
    
    # Remove rows with NaN values
    resampled = resampled.dropna()
    
    return resampled


def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate common technical indicators.
    
    Args:
        data: OHLCV data
        
    Returns:
        Data with additional technical indicator columns
    """
    result = data.copy()
    
    # Simple Moving Averages
    result['SMA_10'] = result['Close'].rolling(10).mean()
    result['SMA_20'] = result['Close'].rolling(20).mean()
    result['SMA_50'] = result['Close'].rolling(50).mean()
    
    # Exponential Moving Averages
    result['EMA_10'] = result['Close'].ewm(span=10).mean()
    result['EMA_20'] = result['Close'].ewm(span=20).mean()
    
    # RSI
    result['RSI'] = calculate_rsi(result['Close'])
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(result['Close'])
    result['MACD'] = macd_line
    result['MACD_Signal'] = signal_line
    result['MACD_Histogram'] = histogram
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(result['Close'])
    result['BB_Upper'] = bb_upper
    result['BB_Middle'] = bb_middle
    result['BB_Lower'] = bb_lower
    
    # Average True Range
    result['ATR'] = calculate_atr(result)
    
    return result


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    
    return atr


def detect_market_regime(data: pd.DataFrame) -> str:
    """
    Detect current market regime (trending, ranging, volatile).
    
    Args:
        data: OHLCV data with technical indicators
        
    Returns:
        Market regime classification
    """
    if len(data) < 50:
        return 'insufficient_data'
        
    # Calculate regime indicators
    recent_data = data.tail(20)
    
    # Trend strength (using moving averages)
    if 'SMA_10' in data.columns and 'SMA_20' in data.columns:
        ma_trend = recent_data['SMA_10'].iloc[-1] > recent_data['SMA_20'].iloc[-1]
        ma_divergence = abs(recent_data['SMA_10'].iloc[-1] - recent_data['SMA_20'].iloc[-1]) / recent_data['Close'].iloc[-1]
    else:
        ma_trend = True
        ma_divergence = 0.01
        
    # Volatility (using ATR or price std)
    if 'ATR' in data.columns:
        volatility = recent_data['ATR'].mean() / recent_data['Close'].mean()
    else:
        volatility = recent_data['Close'].std() / recent_data['Close'].mean()
        
    # Range detection (price confined to narrow range)
    price_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Close'].mean()
    
    # Classify regime
    if volatility > 0.03:  # High volatility
        return 'volatile'
    elif ma_divergence > 0.02 and price_range > 0.05:  # Strong trend
        return 'trending'
    elif price_range < 0.02:  # Tight range
        return 'ranging'
    else:
        return 'mixed'


def generate_sample_data(
    start_date: datetime, 
    end_date: datetime, 
    timeframe: TimeFrame = TimeFrame.M15,
    initial_price: float = 1.1000
) -> pd.DataFrame:
    """
    Generate sample OHLCV data for testing.
    
    Args:
        start_date: Start date for data
        end_date: End date for data
        timeframe: Data timeframe
        initial_price: Starting price
        
    Returns:
        Sample OHLCV data
    """
    # Create date range
    freq_map = {
        TimeFrame.M1: '1min',
        TimeFrame.M5: '5min',
        TimeFrame.M15: '15min',
        TimeFrame.M30: '30min',
        TimeFrame.H1: '1h',
        TimeFrame.H4: '4h',
        TimeFrame.D1: '1D'
    }
    
    freq = freq_map.get(timeframe, '15min')
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # Generate random price movement
    np.random.seed(42)  # For reproducible results
    returns = np.random.normal(0, 0.001, len(date_range))  # 0.1% std dev
    
    # Create price series
    prices = [initial_price]
    for ret in returns[1:]:
        new_price = prices[-1] * (1 + ret)
        prices.append(new_price)
        
    # Create OHLCV data
    data = []
    for i, (timestamp, price) in enumerate(zip(date_range, prices)):
        # Generate realistic OHLC from close price
        volatility = abs(np.random.normal(0, 0.0005))  # Intrabar volatility
        
        high = price * (1 + volatility)
        low = price * (1 - volatility)
        open_price = prices[i-1] if i > 0 else price
        
        # Ensure OHLC relationships are valid
        high = max(high, open_price, price)
        low = min(low, open_price, price)
        
        volume = np.random.randint(1000, 10000)  # Random volume
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': price,
            'Volume': volume
        })
        
    df = pd.DataFrame(data, index=date_range)
    return df


def clean_market_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare market data for analysis.
    
    Args:
        data: Raw market data
        
    Returns:
        Cleaned market data
    """
    cleaned = data.copy()
    
    # Remove rows with invalid prices
    cleaned = cleaned[
        (cleaned['High'] >= cleaned['Low']) &
        (cleaned['High'] >= cleaned['Open']) &
        (cleaned['High'] >= cleaned['Close']) &
        (cleaned['Low'] <= cleaned['Open']) &
        (cleaned['Low'] <= cleaned['Close']) &
        (cleaned['Open'] > 0) &
        (cleaned['Close'] > 0)
    ]
    
    # Remove extreme outliers (price changes > 10%)
    price_changes = cleaned['Close'].pct_change().abs()
    cleaned = cleaned[price_changes < 0.1]
    
    # Forward fill small gaps (up to 3 consecutive NaN values)
    cleaned = cleaned.fillna(method='ffill', limit=3)
    
    # Remove remaining NaN rows
    cleaned = cleaned.dropna()
    
    return cleaned