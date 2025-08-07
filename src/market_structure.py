"""
Market structure analyzer for detecting Change of Character (ChoCH) patterns
and market structure shifts.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from config import MARKET_STRUCTURE_CONFIG


class MarketStructureAnalyzer:
    """
    Analyzes market structure to detect ChoCH (Change of Character) patterns,
    break of structure (BOS), and swing points.
    """
    
    def __init__(self):
        self.config = MARKET_STRUCTURE_CONFIG
        self.swing_periods = self.config['swing_detection_periods']
        self.choch_confirmation = self.config['choch_confirmation_periods']
    
    def analyze_market_structure(self, data: pd.DataFrame) -> Dict:
        """
        Comprehensive market structure analysis.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary containing market structure analysis
        """
        if data.empty or len(data) < self.swing_periods * 2:
            return self._empty_analysis()
        
        # Detect swing highs and lows
        swing_highs = self._detect_swing_highs(data)
        swing_lows = self._detect_swing_lows(data)
        
        # Determine current trend
        current_trend = self._determine_trend(data, swing_highs, swing_lows)
        
        # Detect ChoCH patterns
        choch_signals = self._detect_choch(data, swing_highs, swing_lows, current_trend)
        
        # Detect Break of Structure (BOS)
        bos_signals = self._detect_bos(data, swing_highs, swing_lows, current_trend)
        
        # Identify market structure levels
        structure_levels = self._identify_structure_levels(swing_highs, swing_lows)
        
        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'current_trend': current_trend,
            'choch_signals': choch_signals,
            'bos_signals': bos_signals,
            'structure_levels': structure_levels,
            'last_structure_break': self._get_last_structure_break(choch_signals, bos_signals),
            'trend_strength': self._calculate_trend_strength(data, current_trend)
        }
    
    def _detect_swing_highs(self, data: pd.DataFrame) -> List[Dict]:
        """Detect swing high points in price data."""
        swing_highs = []
        highs = data['high'].values
        
        for i in range(self.swing_periods, len(highs) - self.swing_periods):
            # Check if current point is higher than surrounding points
            left_side = highs[i-self.swing_periods:i]
            right_side = highs[i+1:i+self.swing_periods+1]
            current_high = highs[i]
            
            if (current_high > max(left_side) and 
                current_high > max(right_side)):
                swing_highs.append({
                    'index': i,
                    'price': current_high,
                    'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                    'type': 'swing_high'
                })
        
        return swing_highs
    
    def _detect_swing_lows(self, data: pd.DataFrame) -> List[Dict]:
        """Detect swing low points in price data."""
        swing_lows = []
        lows = data['low'].values
        
        for i in range(self.swing_periods, len(lows) - self.swing_periods):
            # Check if current point is lower than surrounding points
            left_side = lows[i-self.swing_periods:i]
            right_side = lows[i+1:i+self.swing_periods+1]
            current_low = lows[i]
            
            if (current_low < min(left_side) and 
                current_low < min(right_side)):
                swing_lows.append({
                    'index': i,
                    'price': current_low,
                    'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                    'type': 'swing_low'
                })
        
        return swing_lows
    
    def _determine_trend(self, data: pd.DataFrame, swing_highs: List[Dict], 
                        swing_lows: List[Dict]) -> str:
        """Determine the current market trend based on swing points."""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'sideways'
        
        # Get recent swing points
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]
        
        # Check for higher highs and higher lows (uptrend)
        if (recent_highs[-1]['price'] > recent_highs[-2]['price'] and
            recent_lows[-1]['price'] > recent_lows[-2]['price']):
            return 'bullish'
        
        # Check for lower highs and lower lows (downtrend)
        elif (recent_highs[-1]['price'] < recent_highs[-2]['price'] and
              recent_lows[-1]['price'] < recent_lows[-2]['price']):
            return 'bearish'
        
        return 'sideways'
    
    def _detect_choch(self, data: pd.DataFrame, swing_highs: List[Dict], 
                     swing_lows: List[Dict], current_trend: str) -> List[Dict]:
        """
        Detect Change of Character (ChoCH) patterns.
        ChoCH occurs when the market structure changes from bullish to bearish or vice versa.
        """
        choch_signals = []
        
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return choch_signals
        
        # Combine and sort swing points by index
        all_swings = swing_highs + swing_lows
        all_swings.sort(key=lambda x: x['index'])
        
        for i in range(2, len(all_swings)):
            current_swing = all_swings[i]
            prev_swing = all_swings[i-1]
            prev_prev_swing = all_swings[i-2]
            
            # Detect bullish ChoCH (break above previous swing high)
            if (current_swing['type'] == 'swing_high' and
                prev_swing['type'] == 'swing_low' and
                prev_prev_swing['type'] == 'swing_high'):
                
                if current_swing['price'] > prev_prev_swing['price']:
                    choch_signals.append({
                        'type': 'bullish_choch',
                        'index': current_swing['index'],
                        'price': current_swing['price'],
                        'timestamp': current_swing['timestamp'],
                        'broken_level': prev_prev_swing['price'],
                        'strength': self._calculate_choch_strength(current_swing, prev_prev_swing)
                    })
            
            # Detect bearish ChoCH (break below previous swing low)
            elif (current_swing['type'] == 'swing_low' and
                  prev_swing['type'] == 'swing_high' and
                  prev_prev_swing['type'] == 'swing_low'):
                
                if current_swing['price'] < prev_prev_swing['price']:
                    choch_signals.append({
                        'type': 'bearish_choch',
                        'index': current_swing['index'],
                        'price': current_swing['price'],
                        'timestamp': current_swing['timestamp'],
                        'broken_level': prev_prev_swing['price'],
                        'strength': self._calculate_choch_strength(current_swing, prev_prev_swing)
                    })
        
        return choch_signals
    
    def _detect_bos(self, data: pd.DataFrame, swing_highs: List[Dict], 
                   swing_lows: List[Dict], current_trend: str) -> List[Dict]:
        """
        Detect Break of Structure (BOS) patterns.
        BOS confirms trend continuation.
        """
        bos_signals = []
        recent_close = data['close'].iloc[-1]
        
        # For bullish trend, look for breaks above recent swing highs
        if current_trend == 'bullish' and swing_highs:
            for swing_high in swing_highs[-3:]:  # Check last 3 swing highs
                if recent_close > swing_high['price']:
                    bos_signals.append({
                        'type': 'bullish_bos',
                        'broken_level': swing_high['price'],
                        'current_price': recent_close,
                        'timestamp': data.index[-1] if hasattr(data.index, 'to_pydatetime') else len(data)-1
                    })
        
        # For bearish trend, look for breaks below recent swing lows
        elif current_trend == 'bearish' and swing_lows:
            for swing_low in swing_lows[-3:]:  # Check last 3 swing lows
                if recent_close < swing_low['price']:
                    bos_signals.append({
                        'type': 'bearish_bos',
                        'broken_level': swing_low['price'],
                        'current_price': recent_close,
                        'timestamp': data.index[-1] if hasattr(data.index, 'to_pydatetime') else len(data)-1
                    })
        
        return bos_signals
    
    def _identify_structure_levels(self, swing_highs: List[Dict], 
                                 swing_lows: List[Dict]) -> Dict:
        """Identify key market structure levels."""
        levels = {
            'resistance_levels': [],
            'support_levels': [],
            'key_levels': []
        }
        
        # Recent swing highs as resistance
        if swing_highs:
            for swing_high in swing_highs[-5:]:  # Last 5 swing highs
                levels['resistance_levels'].append({
                    'price': swing_high['price'],
                    'strength': 1,  # Could be enhanced with touch count
                    'timestamp': swing_high['timestamp']
                })
        
        # Recent swing lows as support
        if swing_lows:
            for swing_low in swing_lows[-5:]:  # Last 5 swing lows
                levels['support_levels'].append({
                    'price': swing_low['price'],
                    'strength': 1,  # Could be enhanced with touch count
                    'timestamp': swing_low['timestamp']
                })
        
        # Combine for key levels (most recent and significant)
        all_levels = levels['resistance_levels'] + levels['support_levels']
        if all_levels:
            # Sort by timestamp and take most recent - handle mixed timestamp types
            def sort_key(x):
                timestamp = x['timestamp']
                if hasattr(timestamp, 'timestamp'):  # pandas Timestamp
                    return timestamp.timestamp()
                elif isinstance(timestamp, (int, float)):
                    return timestamp
                else:
                    return 0
            
            all_levels.sort(key=sort_key, reverse=True)
            levels['key_levels'] = all_levels[:3]  # Top 3 most recent levels
        
        return levels
    
    def _calculate_choch_strength(self, current_swing: Dict, broken_swing: Dict) -> float:
        """Calculate the strength of a ChoCH signal."""
        price_diff = abs(current_swing['price'] - broken_swing['price'])
        percentage_move = price_diff / broken_swing['price'] * 100
        return min(percentage_move, 10.0)  # Cap at 10% for normalization
    
    def _calculate_trend_strength(self, data: pd.DataFrame, trend: str) -> float:
        """Calculate the strength of the current trend."""
        if trend == 'sideways':
            return 0.0
        
        if len(data) < 20:
            return 0.5
        
        # Simple trend strength based on price momentum
        recent_prices = data['close'].tail(20)
        price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
        
        # Normalize to 0-1 scale
        strength = min(abs(price_change) * 10, 1.0)
        return strength
    
    def _get_last_structure_break(self, choch_signals: List[Dict], 
                                bos_signals: List[Dict]) -> Optional[Dict]:
        """Get the most recent structure break (ChoCH or BOS)."""
        all_breaks = choch_signals + bos_signals
        if not all_breaks:
            return None
        
        # Return most recent break - use index as primary sort key
        def sort_key(x):
            index = x.get('index')
            if index is not None:
                return index
            timestamp = x.get('timestamp', 0)
            return timestamp if isinstance(timestamp, (int, float)) else 0
        
        all_breaks.sort(key=sort_key, reverse=True)
        return all_breaks[0]
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            'swing_highs': [],
            'swing_lows': [],
            'current_trend': 'sideways',
            'choch_signals': [],
            'bos_signals': [],
            'structure_levels': {'resistance_levels': [], 'support_levels': [], 'key_levels': []},
            'last_structure_break': None,
            'trend_strength': 0.0
        }