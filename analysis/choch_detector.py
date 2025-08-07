"""
Change of Character (CHOCH) Detection
Identifies market structure breaks and trend changes autonomously
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CHOCHDetector:
    """
    Detects Change of Character in market structure
    Identifies breaks in market trends and structural shifts
    """
    
    def __init__(self, confirmation_period: int = 3, min_swing_size: float = 0.001):
        """
        Initialize CHOCH detector
        
        Args:
            confirmation_period: Number of candles needed to confirm CHOCH
            min_swing_size: Minimum swing size as percentage for valid CHOCH
        """
        self.confirmation_period = confirmation_period
        self.min_swing_size = min_swing_size
        self.swing_points = []
    
    def detect_choch(self, data: pd.DataFrame, fractals_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Detect Change of Character patterns
        
        Args:
            data: OHLCV DataFrame
            fractals_data: DataFrame with fractal information
            
        Returns:
            DataFrame with CHOCH signals
        """
        if len(data) < self.confirmation_period * 3:
            logger.warning("Insufficient data for CHOCH detection")
            return data
        
        data = data.copy()
        
        # Initialize CHOCH columns
        data['choch_bullish'] = False
        data['choch_bearish'] = False
        data['choch_strength'] = 0.0
        data['market_structure'] = 'ranging'  # bullish, bearish, ranging
        
        # Identify swing points
        swing_highs, swing_lows = self._identify_swing_points(data, fractals_data)
        
        # Analyze market structure
        structure_analysis = self._analyze_market_structure(data, swing_highs, swing_lows)
        
        # Detect CHOCH patterns
        choch_signals = self._detect_choch_patterns(data, swing_highs, swing_lows, structure_analysis)
        
        # Apply CHOCH signals to data
        for signal in choch_signals:
            idx, signal_type, strength = signal
            if signal_type == 'bullish':
                data.loc[idx, 'choch_bullish'] = True
                data.loc[idx, 'market_structure'] = 'bullish'
            elif signal_type == 'bearish':
                data.loc[idx, 'choch_bearish'] = True
                data.loc[idx, 'market_structure'] = 'bearish'
            
            data.loc[idx, 'choch_strength'] = strength
        
        # Forward fill market structure
        data['market_structure'] = data['market_structure'].replace('ranging', np.nan).ffill().fillna('ranging')
        
        return data
    
    def _identify_swing_points(self, data: pd.DataFrame, fractals_data: pd.DataFrame = None) -> Tuple[List[Tuple], List[Tuple]]:
        """
        Identify swing highs and lows
        Uses fractals if available, otherwise calculates own swings
        """
        swing_highs = []
        swing_lows = []
        
        if fractals_data is not None:
            # Use fractal data if available
            for idx in fractals_data.index:
                if fractals_data.loc[idx, 'fractal_high']:
                    swing_highs.append((idx, fractals_data.loc[idx, 'fractal_high_price']))
                if fractals_data.loc[idx, 'fractal_low']:
                    swing_lows.append((idx, fractals_data.loc[idx, 'fractal_low_price']))
        else:
            # Calculate own swing points
            period = 5
            for i in range(period, len(data) - period):
                # Check for swing high
                if self._is_swing_high(data, i, period):
                    swing_highs.append((i, data.iloc[i]['high']))
                
                # Check for swing low
                if self._is_swing_low(data, i, period):
                    swing_lows.append((i, data.iloc[i]['low']))
        
        return swing_highs, swing_lows
    
    def _is_swing_high(self, data: pd.DataFrame, idx: int, period: int) -> bool:
        """Check if index is a swing high"""
        current_high = data.iloc[idx]['high']
        
        # Check left side
        for i in range(idx - period, idx):
            if data.iloc[i]['high'] >= current_high:
                return False
        
        # Check right side
        for i in range(idx + 1, idx + period + 1):
            if data.iloc[i]['high'] >= current_high:
                return False
        
        return True
    
    def _is_swing_low(self, data: pd.DataFrame, idx: int, period: int) -> bool:
        """Check if index is a swing low"""
        current_low = data.iloc[idx]['low']
        
        # Check left side
        for i in range(idx - period, idx):
            if data.iloc[i]['low'] <= current_low:
                return False
        
        # Check right side
        for i in range(idx + 1, idx + period + 1):
            if data.iloc[i]['low'] <= current_low:
                return False
        
        return True
    
    def _analyze_market_structure(self, data: pd.DataFrame, swing_highs: List[Tuple], swing_lows: List[Tuple]) -> Dict:
        """
        Analyze current market structure
        Determines if market is making higher highs/lows or lower highs/lows
        """
        analysis = {
            'trend': 'ranging',
            'last_structure_type': None,
            'structure_strength': 0.0,
            'key_levels': []
        }
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return analysis
        
        # Analyze recent swing highs
        recent_highs = sorted(swing_highs, key=lambda x: x[0])[-3:]  # Last 3 highs
        recent_lows = sorted(swing_lows, key=lambda x: x[0])[-3:]    # Last 3 lows
        
        # Check for higher highs and higher lows (bullish structure)
        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            hh_pattern = self._check_higher_highs(recent_highs)
            hl_pattern = self._check_higher_lows(recent_lows)
            
            # Check for lower highs and lower lows (bearish structure)
            lh_pattern = self._check_lower_highs(recent_highs)
            ll_pattern = self._check_lower_lows(recent_lows)
            
            if hh_pattern and hl_pattern:
                analysis['trend'] = 'bullish'
                analysis['last_structure_type'] = 'higher_highs_lows'
                analysis['structure_strength'] = (hh_pattern + hl_pattern) / 2
            elif lh_pattern and ll_pattern:
                analysis['trend'] = 'bearish'
                analysis['last_structure_type'] = 'lower_highs_lows'
                analysis['structure_strength'] = (lh_pattern + ll_pattern) / 2
            else:
                analysis['trend'] = 'ranging'
                analysis['last_structure_type'] = 'mixed'
        
        # Identify key levels
        analysis['key_levels'] = self._identify_key_levels(swing_highs, swing_lows)
        
        return analysis
    
    def _check_higher_highs(self, highs: List[Tuple]) -> float:
        """Check for higher highs pattern and return strength"""
        if len(highs) < 2:
            return 0.0
        
        strength = 0.0
        for i in range(1, len(highs)):
            if highs[i][1] > highs[i-1][1]:
                strength += 1.0
        
        return strength / (len(highs) - 1)
    
    def _check_higher_lows(self, lows: List[Tuple]) -> float:
        """Check for higher lows pattern and return strength"""
        if len(lows) < 2:
            return 0.0
        
        strength = 0.0
        for i in range(1, len(lows)):
            if lows[i][1] > lows[i-1][1]:
                strength += 1.0
        
        return strength / (len(lows) - 1)
    
    def _check_lower_highs(self, highs: List[Tuple]) -> float:
        """Check for lower highs pattern and return strength"""
        if len(highs) < 2:
            return 0.0
        
        strength = 0.0
        for i in range(1, len(highs)):
            if highs[i][1] < highs[i-1][1]:
                strength += 1.0
        
        return strength / (len(highs) - 1)
    
    def _check_lower_lows(self, lows: List[Tuple]) -> float:
        """Check for lower lows pattern and return strength"""
        if len(lows) < 2:
            return 0.0
        
        strength = 0.0
        for i in range(1, len(lows)):
            if lows[i][1] < lows[i-1][1]:
                strength += 1.0
        
        return strength / (len(lows) - 1)
    
    def _identify_key_levels(self, swing_highs: List[Tuple], swing_lows: List[Tuple]) -> List[float]:
        """Identify key support and resistance levels"""
        key_levels = []
        
        # Get recent significant levels
        if swing_highs:
            recent_highs = [price for _, price in swing_highs[-5:]]
            key_levels.extend(recent_highs)
        
        if swing_lows:
            recent_lows = [price for _, price in swing_lows[-5:]]
            key_levels.extend(recent_lows)
        
        return sorted(set(key_levels))
    
    def _detect_choch_patterns(self, data: pd.DataFrame, swing_highs: List[Tuple], 
                              swing_lows: List[Tuple], structure_analysis: Dict) -> List[Tuple]:
        """
        Detect CHOCH patterns based on structure breaks
        
        Returns:
            List of (index, signal_type, strength) tuples
        """
        choch_signals = []
        
        if structure_analysis['trend'] == 'ranging' or len(swing_highs) < 2 or len(swing_lows) < 2:
            return choch_signals
        
        # Sort swings by time
        all_swings = [(idx, price, 'high') for idx, price in swing_highs] + \
                     [(idx, price, 'low') for idx, price in swing_lows]
        all_swings.sort(key=lambda x: x[0])
        
        current_trend = structure_analysis['trend']
        
        for i in range(self.confirmation_period, len(data)):
            # Check for bullish CHOCH (break of bearish structure)
            if current_trend == 'bearish':
                bullish_choch = self._check_bullish_choch(data, i, swing_highs, swing_lows)
                if bullish_choch:
                    strength = self._calculate_choch_strength(data, i, 'bullish', swing_highs, swing_lows)
                    choch_signals.append((i, 'bullish', strength))
                    current_trend = 'bullish'
            
            # Check for bearish CHOCH (break of bullish structure)
            elif current_trend == 'bullish':
                bearish_choch = self._check_bearish_choch(data, i, swing_highs, swing_lows)
                if bearish_choch:
                    strength = self._calculate_choch_strength(data, i, 'bearish', swing_highs, swing_lows)
                    choch_signals.append((i, 'bearish', strength))
                    current_trend = 'bearish'
        
        return choch_signals
    
    def _check_bullish_choch(self, data: pd.DataFrame, idx: int, 
                            swing_highs: List[Tuple], swing_lows: List[Tuple]) -> bool:
        """Check for bullish CHOCH pattern"""
        current_price = data.iloc[idx]['close']
        
        # Find the most recent swing high that could be broken
        recent_highs = [high for high_idx, high in swing_highs if high_idx < idx]
        if not recent_highs:
            return False
        
        # Check if current price breaks above recent swing high
        last_swing_high = recent_highs[-1]
        
        # Confirm break with additional criteria
        if current_price > last_swing_high:
            # Check for confirmation over multiple candles
            confirmation_count = 0
            for j in range(max(0, idx - self.confirmation_period), idx + 1):
                if data.iloc[j]['close'] > last_swing_high:
                    confirmation_count += 1
            
            return confirmation_count >= self.confirmation_period
        
        return False
    
    def _check_bearish_choch(self, data: pd.DataFrame, idx: int,
                            swing_highs: List[Tuple], swing_lows: List[Tuple]) -> bool:
        """Check for bearish CHOCH pattern"""
        current_price = data.iloc[idx]['close']
        
        # Find the most recent swing low that could be broken
        recent_lows = [low for low_idx, low in swing_lows if low_idx < idx]
        if not recent_lows:
            return False
        
        # Check if current price breaks below recent swing low
        last_swing_low = recent_lows[-1]
        
        # Confirm break with additional criteria
        if current_price < last_swing_low:
            # Check for confirmation over multiple candles
            confirmation_count = 0
            for j in range(max(0, idx - self.confirmation_period), idx + 1):
                if data.iloc[j]['close'] < last_swing_low:
                    confirmation_count += 1
            
            return confirmation_count >= self.confirmation_period
        
        return False
    
    def _calculate_choch_strength(self, data: pd.DataFrame, idx: int, choch_type: str,
                                 swing_highs: List[Tuple], swing_lows: List[Tuple]) -> float:
        """Calculate the strength of CHOCH signal (0-1)"""
        base_strength = 0.5
        
        # Volume confirmation
        volume_strength = 0.0
        if 'volume' in data.columns and data['volume'].sum() > 0:
            recent_avg_volume = data['volume'].iloc[max(0, idx-10):idx].mean()
            current_volume = data.iloc[idx]['volume']
            if recent_avg_volume > 0:
                volume_ratio = min(current_volume / recent_avg_volume, 2.0)
                volume_strength = (volume_ratio - 1.0) * 0.2  # Up to 0.2 bonus
        
        # Price momentum strength
        momentum_strength = 0.0
        if idx >= 5:
            price_change = abs(data.iloc[idx]['close'] - data.iloc[idx-5]['close'])
            atr = data.iloc[idx-14:idx]['high'].subtract(data.iloc[idx-14:idx]['low']).mean()
            if atr > 0:
                momentum_ratio = min(price_change / atr, 2.0)
                momentum_strength = momentum_ratio * 0.15  # Up to 0.15 bonus
        
        # Time since last structure break
        time_strength = min(idx / 100.0, 0.15)  # Up to 0.15 bonus for later signals
        
        total_strength = base_strength + volume_strength + momentum_strength + time_strength
        return min(total_strength, 1.0)
    
    def get_current_market_structure(self, data: pd.DataFrame) -> Dict:
        """Get current market structure analysis"""
        if 'market_structure' not in data.columns:
            return {'trend': 'ranging', 'last_choch': None, 'strength': 0.0}
        
        latest_structure = data['market_structure'].iloc[-1]
        
        # Find most recent CHOCH
        recent_bullish = data[data['choch_bullish']].tail(1)
        recent_bearish = data[data['choch_bearish']].tail(1)
        
        last_choch = None
        if not recent_bullish.empty and not recent_bearish.empty:
            if recent_bullish.index[0] > recent_bearish.index[0]:
                last_choch = ('bullish', recent_bullish.index[0], recent_bullish['choch_strength'].iloc[0])
            else:
                last_choch = ('bearish', recent_bearish.index[0], recent_bearish['choch_strength'].iloc[0])
        elif not recent_bullish.empty:
            last_choch = ('bullish', recent_bullish.index[0], recent_bullish['choch_strength'].iloc[0])
        elif not recent_bearish.empty:
            last_choch = ('bearish', recent_bearish.index[0], recent_bearish['choch_strength'].iloc[0])
        
        return {
            'trend': latest_structure,
            'last_choch': last_choch,
            'strength': data['choch_strength'].iloc[-1] if 'choch_strength' in data.columns else 0.0
        }