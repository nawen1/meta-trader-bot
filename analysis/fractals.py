"""
Fractal identification and analysis within market structure
Implements proper fractal detection avoiding misplacement and premature assumptions
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FractalAnalyzer:
    """
    Identifies and validates fractals within market structure
    Ensures proper fractal placement and prevents premature assumptions
    """
    
    def __init__(self, period: int = 5):
        """
        Initialize fractal analyzer
        
        Args:
            period: Number of candles on each side for fractal validation
        """
        self.period = period
        self.min_fractal_distance = period * 2  # Minimum distance between fractals
    
    def identify_fractals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Identify valid fractals in the price data
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            DataFrame with fractal signals
        """
        if len(data) < (self.period * 2 + 1):
            logger.warning("Insufficient data for fractal analysis")
            return data
        
        # Initialize fractal columns
        data = data.copy()
        data['fractal_high'] = False
        data['fractal_low'] = False
        data['fractal_high_price'] = np.nan
        data['fractal_low_price'] = np.nan
        
        # Identify potential fractals
        high_fractals = self._find_high_fractals(data)
        low_fractals = self._find_low_fractals(data)
        
        # Validate fractals within market structure
        validated_highs = self._validate_fractals(data, high_fractals, 'high')
        validated_lows = self._validate_fractals(data, low_fractals, 'low')
        
        # Apply validated fractals
        for idx in validated_highs:
            data.loc[idx, 'fractal_high'] = True
            data.loc[idx, 'fractal_high_price'] = data.loc[idx, 'high']
        
        for idx in validated_lows:
            data.loc[idx, 'fractal_low'] = True
            data.loc[idx, 'fractal_low_price'] = data.loc[idx, 'low']
        
        # Add fractal strength analysis
        data = self._calculate_fractal_strength(data)
        
        return data
    
    def _find_high_fractals(self, data: pd.DataFrame) -> List[int]:
        """Find potential high fractals"""
        fractals = []
        
        for i in range(self.period, len(data) - self.period):
            current_high = data.iloc[i]['high']
            
            # Check if current high is higher than surrounding candles
            is_fractal = True
            
            # Check left side
            for j in range(i - self.period, i):
                if data.iloc[j]['high'] >= current_high:
                    is_fractal = False
                    break
            
            # Check right side
            if is_fractal:
                for j in range(i + 1, i + self.period + 1):
                    if data.iloc[j]['high'] >= current_high:
                        is_fractal = False
                        break
            
            if is_fractal:
                fractals.append(i)
        
        return fractals
    
    def _find_low_fractals(self, data: pd.DataFrame) -> List[int]:
        """Find potential low fractals"""
        fractals = []
        
        for i in range(self.period, len(data) - self.period):
            current_low = data.iloc[i]['low']
            
            # Check if current low is lower than surrounding candles
            is_fractal = True
            
            # Check left side
            for j in range(i - self.period, i):
                if data.iloc[j]['low'] <= current_low:
                    is_fractal = False
                    break
            
            # Check right side
            if is_fractal:
                for j in range(i + 1, i + self.period + 1):
                    if data.iloc[j]['low'] <= current_low:
                        is_fractal = False
                        break
            
            if is_fractal:
                fractals.append(i)
        
        return fractals
    
    def _validate_fractals(self, data: pd.DataFrame, fractals: List[int], fractal_type: str) -> List[int]:
        """
        Validate fractals within broader market structure
        Prevents misplacement and premature assumptions
        """
        if not fractals:
            return []
        
        validated = []
        
        for fractal_idx in fractals:
            if self._is_valid_fractal(data, fractal_idx, fractal_type):
                # Check minimum distance from previous fractals
                if self._check_fractal_distance(validated, fractal_idx):
                    validated.append(fractal_idx)
        
        return validated
    
    def _is_valid_fractal(self, data: pd.DataFrame, idx: int, fractal_type: str) -> bool:
        """
        Validate individual fractal within market structure
        """
        # Get broader context (2x the fractal period)
        context_start = max(0, idx - (self.period * 2))
        context_end = min(len(data), idx + (self.period * 2))
        context_data = data.iloc[context_start:context_end]
        
        if fractal_type == 'high':
            fractal_price = data.iloc[idx]['high']
            
            # Check if fractal is significant within broader context
            # Should be in top 20% of highs in the context period
            context_highs = context_data['high'].values
            percentile_80 = np.percentile(context_highs, 80)
            
            # Also check for volume confirmation if available
            volume_confirmation = self._check_volume_confirmation(data, idx, fractal_type)
            
            return fractal_price >= percentile_80 and volume_confirmation
        
        else:  # low fractal
            fractal_price = data.iloc[idx]['low']
            
            # Check if fractal is significant within broader context
            # Should be in bottom 20% of lows in the context period
            context_lows = context_data['low'].values
            percentile_20 = np.percentile(context_lows, 20)
            
            # Also check for volume confirmation if available
            volume_confirmation = self._check_volume_confirmation(data, idx, fractal_type)
            
            return fractal_price <= percentile_20 and volume_confirmation
    
    def _check_volume_confirmation(self, data: pd.DataFrame, idx: int, fractal_type: str) -> bool:
        """Check for volume confirmation of fractal"""
        if 'volume' not in data.columns or data['volume'].sum() == 0:
            return True  # Skip volume check if not available
        
        # Check if volume is above average around fractal formation
        context_start = max(0, idx - self.period)
        context_end = min(len(data), idx + self.period + 1)
        context_volume = data.iloc[context_start:context_end]['volume']
        
        avg_volume = context_volume.mean()
        fractal_volume = data.iloc[idx]['volume']
        
        # Fractal should have above-average volume
        return fractal_volume >= avg_volume * 0.8
    
    def _check_fractal_distance(self, existing_fractals: List[int], new_fractal: int) -> bool:
        """Check minimum distance between fractals"""
        if not existing_fractals:
            return True
        
        for existing in existing_fractals:
            if abs(new_fractal - existing) < self.min_fractal_distance:
                return False
        
        return True
    
    def _calculate_fractal_strength(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate fractal strength based on various factors"""
        data['fractal_strength'] = 0.0
        
        # Calculate strength for high fractals
        high_fractals = data[data['fractal_high'].fillna(False)].index
        for idx in high_fractals:
            strength = self._calculate_strength_score(data, idx, 'high')
            data.loc[idx, 'fractal_strength'] = strength
        
        # Calculate strength for low fractals
        low_fractals = data[data['fractal_low'].fillna(False)].index
        for idx in low_fractals:
            strength = self._calculate_strength_score(data, idx, 'low')
            data.loc[idx, 'fractal_strength'] = strength
        
        return data
    
    def _calculate_strength_score(self, data: pd.DataFrame, idx: int, fractal_type: str) -> float:
        """
        Calculate fractal strength score (0-1)
        Based on price significance, volume, and market structure context
        """
        if fractal_type == 'high':
            price = data.iloc[idx]['high']
            context_prices = data['high'].iloc[max(0, idx-50):idx+50]
        else:
            price = data.iloc[idx]['low']
            context_prices = data['low'].iloc[max(0, idx-50):idx+50]
        
        # Price significance (0-0.5)
        if fractal_type == 'high':
            price_percentile = (price >= context_prices).mean()
        else:
            price_percentile = (price <= context_prices).mean()
        
        price_score = min(price_percentile * 0.5, 0.5)
        
        # Volume significance (0-0.3)
        volume_score = 0.0
        if 'volume' in data.columns and data['volume'].sum() > 0:
            fractal_volume = data.iloc[idx]['volume']
            avg_volume = data['volume'].iloc[max(0, idx-20):idx+20].mean()
            if avg_volume > 0:
                volume_ratio = min(fractal_volume / avg_volume, 3.0) / 3.0
                volume_score = volume_ratio * 0.3
        
        # Time significance (0-0.2) - fractals that hold longer are stronger
        time_score = min(self.period / 10.0, 0.2)
        
        total_score = price_score + volume_score + time_score
        return min(total_score, 1.0)
    
    def get_recent_fractals(self, data: pd.DataFrame, lookback: int = 50) -> Dict[str, List[Tuple[int, float]]]:
        """
        Get recent fractals with their prices
        
        Args:
            data: DataFrame with fractal data
            lookback: Number of candles to look back
            
        Returns:
            Dictionary with 'highs' and 'lows' keys containing (index, price) tuples
        """
        recent_data = data.tail(lookback)
        
        high_fractals = []
        low_fractals = []
        
        for idx in recent_data.index:
            if recent_data.loc[idx, 'fractal_high']:
                high_fractals.append((idx, recent_data.loc[idx, 'fractal_high_price']))
            
            if recent_data.loc[idx, 'fractal_low']:
                low_fractals.append((idx, recent_data.loc[idx, 'fractal_low_price']))
        
        return {
            'highs': high_fractals,
            'lows': low_fractals
        }