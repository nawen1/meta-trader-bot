"""
Liquidity Zones Detection
Autonomously identifies key liquidity zones, sweeps, and retests
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class LiquidityZoneDetector:
    """
    Detects and manages liquidity zones in the market
    Identifies areas where liquidity is likely to be resting
    """
    
    def __init__(self, zone_buffer: float = 0.001, min_touches: int = 2):
        """
        Initialize liquidity zone detector
        
        Args:
            zone_buffer: Buffer around price levels as percentage
            min_touches: Minimum touches required to confirm a zone
        """
        self.zone_buffer = zone_buffer
        self.min_touches = min_touches
        self.active_zones = []
    
    def detect_liquidity_zones(self, data: pd.DataFrame, fractals_data: pd.DataFrame = None) -> pd.DataFrame:
        """
        Detect liquidity zones in the market
        
        Args:
            data: OHLCV DataFrame
            fractals_data: DataFrame with fractal information
            
        Returns:
            DataFrame with liquidity zone information
        """
        data = data.copy()
        
        # Initialize liquidity zone columns
        data['liquidity_zone'] = False
        data['zone_type'] = ''  # 'support', 'resistance', 'supply', 'demand'
        data['zone_strength'] = 0.0
        data['liquidity_swept'] = False
        data['zone_retest'] = False
        
        # Identify potential liquidity zones
        zones = self._identify_zones(data, fractals_data)
        
        # Validate and strength-test zones
        validated_zones = self._validate_zones(data, zones)
        
        # Apply zones to data
        for zone in validated_zones:
            self._apply_zone_to_data(data, zone)
        
        # Detect liquidity sweeps
        data = self._detect_liquidity_sweeps(data, validated_zones)
        
        # Detect zone retests
        data = self._detect_zone_retests(data, validated_zones)
        
        return data
    
    def _identify_zones(self, data: pd.DataFrame, fractals_data: pd.DataFrame = None) -> List[Dict]:
        """Identify potential liquidity zones"""
        zones = []
        
        # Method 1: Fractal-based zones
        if fractals_data is not None:
            fractal_zones = self._get_fractal_zones(data, fractals_data)
            zones.extend(fractal_zones)
        
        # Method 2: Equal highs/lows zones
        equal_level_zones = self._get_equal_level_zones(data)
        zones.extend(equal_level_zones)
        
        # Method 3: Volume-based zones
        volume_zones = self._get_volume_zones(data)
        zones.extend(volume_zones)
        
        # Method 4: Previous day/session highs and lows
        session_zones = self._get_session_zones(data)
        zones.extend(session_zones)
        
        return zones
    
    def _get_fractal_zones(self, data: pd.DataFrame, fractals_data: pd.DataFrame) -> List[Dict]:
        """Get liquidity zones from fractal points"""
        zones = []
        
        # High fractal zones (resistance/supply)
        high_fractals = fractals_data[fractals_data['fractal_high']].copy()
        for idx in high_fractals.index:
            price = high_fractals.loc[idx, 'fractal_high_price']
            strength = high_fractals.loc[idx, 'fractal_strength'] if 'fractal_strength' in high_fractals.columns else 0.5
            
            zone = {
                'price': price,
                'type': 'resistance',
                'strength': strength,
                'touches': 1,
                'created_at': idx,
                'last_test': idx,
                'upper_bound': price * (1 + self.zone_buffer),
                'lower_bound': price * (1 - self.zone_buffer)
            }
            zones.append(zone)
        
        # Low fractal zones (support/demand)
        low_fractals = fractals_data[fractals_data['fractal_low']].copy()
        for idx in low_fractals.index:
            price = low_fractals.loc[idx, 'fractal_low_price']
            strength = low_fractals.loc[idx, 'fractal_strength'] if 'fractal_strength' in low_fractals.columns else 0.5
            
            zone = {
                'price': price,
                'type': 'support',
                'strength': strength,
                'touches': 1,
                'created_at': idx,
                'last_test': idx,
                'upper_bound': price * (1 + self.zone_buffer),
                'lower_bound': price * (1 - self.zone_buffer)
            }
            zones.append(zone)
        
        return zones
    
    def _get_equal_level_zones(self, data: pd.DataFrame) -> List[Dict]:
        """Identify zones from equal highs and lows"""
        zones = []
        
        # Find equal highs
        equal_highs = self._find_equal_levels(data['high'], 'high')
        for level, indices in equal_highs.items():
            if len(indices) >= self.min_touches:
                zone = {
                    'price': level,
                    'type': 'resistance',
                    'strength': min(len(indices) * 0.2, 1.0),
                    'touches': len(indices),
                    'created_at': min(indices),
                    'last_test': max(indices),
                    'upper_bound': level * (1 + self.zone_buffer),
                    'lower_bound': level * (1 - self.zone_buffer)
                }
                zones.append(zone)
        
        # Find equal lows
        equal_lows = self._find_equal_levels(data['low'], 'low')
        for level, indices in equal_lows.items():
            if len(indices) >= self.min_touches:
                zone = {
                    'price': level,
                    'type': 'support',
                    'strength': min(len(indices) * 0.2, 1.0),
                    'touches': len(indices),
                    'created_at': min(indices),
                    'last_test': max(indices),
                    'upper_bound': level * (1 + self.zone_buffer),
                    'lower_bound': level * (1 - self.zone_buffer)
                }
                zones.append(zone)
        
        return zones
    
    def _find_equal_levels(self, series: pd.Series, level_type: str) -> Dict[float, List[int]]:
        """Find equal price levels within tolerance"""
        levels = {}
        tolerance = series.mean() * self.zone_buffer
        
        for idx, price in series.items():
            # Check if this price is close to any existing level
            matched = False
            for existing_level in levels.keys():
                if abs(price - existing_level) <= tolerance:
                    levels[existing_level].append(idx)
                    matched = True
                    break
            
            if not matched:
                levels[price] = [idx]
        
        # Filter out levels with only one touch
        return {level: indices for level, indices in levels.items() if len(indices) > 1}
    
    def _get_volume_zones(self, data: pd.DataFrame) -> List[Dict]:
        """Identify zones based on high volume areas"""
        zones = []
        
        if 'volume' not in data.columns or data['volume'].sum() == 0:
            return zones
        
        # Find high volume periods
        volume_threshold = data['volume'].quantile(0.8)  # Top 20% volume
        high_volume_candles = data[data['volume'] >= volume_threshold]
        
        # For simplicity, treat each high volume candle as a potential zone
        for idx in high_volume_candles.index:
            candle = high_volume_candles.loc[idx]
            avg_price = (candle['high'] + candle['low']) / 2
            volume_strength = candle['volume'] / data['volume'].mean()
            
            zone = {
                'price': avg_price,
                'type': 'volume_zone',
                'strength': min(volume_strength * 0.3, 1.0),
                'touches': 1,
                'created_at': idx,
                'last_test': idx,
                'upper_bound': candle['high'] * (1 + self.zone_buffer),
                'lower_bound': candle['low'] * (1 - self.zone_buffer)
            }
            zones.append(zone)
        
        return zones
    
    def _get_session_zones(self, data: pd.DataFrame) -> List[Dict]:
        """Identify session highs and lows as liquidity zones"""
        zones = []
        
        # Assuming daily sessions, group by date
        data_with_date = data.copy()
        data_with_date['date'] = pd.to_datetime(data_with_date.index).date
        
        for date in data_with_date['date'].unique()[-5:]:  # Last 5 sessions
            session_data = data_with_date[data_with_date['date'] == date]
            if len(session_data) > 0:
                session_high = session_data['high'].max()
                session_low = session_data['low'].min()
                session_idx = session_data.index[-1]  # Use last index of session
                
                # Session high zone
                high_zone = {
                    'price': session_high,
                    'type': 'session_high',
                    'strength': 0.6,
                    'touches': 1,
                    'created_at': session_idx,
                    'last_test': session_idx,
                    'upper_bound': session_high * (1 + self.zone_buffer),
                    'lower_bound': session_high * (1 - self.zone_buffer)
                }
                zones.append(high_zone)
                
                # Session low zone
                low_zone = {
                    'price': session_low,
                    'type': 'session_low',
                    'strength': 0.6,
                    'touches': 1,
                    'created_at': session_idx,
                    'last_test': session_idx,
                    'upper_bound': session_low * (1 + self.zone_buffer),
                    'lower_bound': session_low * (1 - self.zone_buffer)
                }
                zones.append(low_zone)
        
        return zones
    
    def _group_consecutive_indices(self, indices: List) -> List[List]:
        """Group consecutive indices together"""
        if not indices:
            return []
        
        # If indices are datetime-like, work with positions instead
        if indices and hasattr(indices[0], 'to_pydatetime'):
            # For datetime indices, we can't easily determine consecutiveness
            # So we'll group based on position proximity
            return [indices]  # Return as single group for now
        
        groups = []
        current_group = [indices[0]]
        
        for i in range(1, len(indices)):
            try:
                if isinstance(indices[i], int) and isinstance(indices[i-1], int):
                    if indices[i] == indices[i-1] + 1:
                        current_group.append(indices[i])
                    else:
                        groups.append(current_group)
                        current_group = [indices[i]]
                else:
                    # For non-integer indices, start new group
                    groups.append(current_group)
                    current_group = [indices[i]]
            except:
                groups.append(current_group)
                current_group = [indices[i]]
        
        groups.append(current_group)
        return groups
    
    def _validate_zones(self, data: pd.DataFrame, zones: List[Dict]) -> List[Dict]:
        """Validate and filter zones based on various criteria"""
        validated_zones = []
        
        for zone in zones:
            # Check zone age (not too old)
            created_idx = zone['created_at']
            if isinstance(created_idx, pd.Timestamp):
                # For timestamp indices, use position-based age calculation
                try:
                    created_position = data.index.get_loc(created_idx)
                    zone_age = len(data) - created_position - 1
                except KeyError:
                    continue  # Skip if index not found
            else:
                zone_age = len(data) - created_idx
            
            if zone_age > 500:  # Skip zones older than 500 candles
                continue
            
            # Check if zone has been tested multiple times
            touches = self._count_zone_touches(data, zone)
            zone['touches'] = touches
            
            # Update strength based on touches and other factors
            zone['strength'] = self._calculate_zone_strength(zone, touches, zone_age)
            
            # Only keep zones with sufficient strength
            if zone['strength'] >= 0.3:
                validated_zones.append(zone)
        
        # Remove overlapping zones (keep stronger ones)
        validated_zones = self._remove_overlapping_zones(validated_zones)
        
        return validated_zones
    
    def _count_zone_touches(self, data: pd.DataFrame, zone: Dict) -> int:
        """Count how many times price has touched this zone"""
        touches = 0
        
        for idx in data.index:
            if idx <= zone['created_at']:
                continue
            
            candle = data.loc[idx]
            
            # Check if high or low touched the zone
            if (candle['high'] >= zone['lower_bound'] and candle['high'] <= zone['upper_bound']) or \
               (candle['low'] >= zone['lower_bound'] and candle['low'] <= zone['upper_bound']):
                touches += 1
                zone['last_test'] = idx
        
        return touches
    
    def _calculate_zone_strength(self, zone: Dict, touches: int, age: int) -> float:
        """Calculate zone strength based on multiple factors"""
        base_strength = zone['strength']
        
        # Touch factor (more touches = stronger zone, but diminishing returns)
        touch_factor = min(touches * 0.1, 0.4)
        
        # Age factor (newer zones might be more relevant)
        age_factor = max(0, (500 - age) / 500) * 0.2
        
        # Zone type factor
        type_factor = 0.0
        if zone['type'] in ['resistance', 'support']:
            type_factor = 0.1
        elif zone['type'] in ['session_high', 'session_low']:
            type_factor = 0.15
        
        total_strength = base_strength + touch_factor + age_factor + type_factor
        return min(total_strength, 1.0)
    
    def _remove_overlapping_zones(self, zones: List[Dict]) -> List[Dict]:
        """Remove overlapping zones, keeping stronger ones"""
        if len(zones) <= 1:
            return zones
        
        # Sort by strength descending
        zones.sort(key=lambda x: x['strength'], reverse=True)
        
        filtered_zones = []
        
        for zone in zones:
            overlap = False
            for existing in filtered_zones:
                if self._zones_overlap(zone, existing):
                    overlap = True
                    break
            
            if not overlap:
                filtered_zones.append(zone)
        
        return filtered_zones
    
    def _zones_overlap(self, zone1: Dict, zone2: Dict) -> bool:
        """Check if two zones overlap"""
        return not (zone1['upper_bound'] < zone2['lower_bound'] or 
                   zone2['upper_bound'] < zone1['lower_bound'])
    
    def _apply_zone_to_data(self, data: pd.DataFrame, zone: Dict):
        """Apply zone information to the data DataFrame"""
        # Mark the creation point
        creation_idx = zone['created_at']
        if creation_idx in data.index:
            data.loc[creation_idx, 'liquidity_zone'] = True
            data.loc[creation_idx, 'zone_type'] = zone['type']
            data.loc[creation_idx, 'zone_strength'] = zone['strength']
    
    def _detect_liquidity_sweeps(self, data: pd.DataFrame, zones: List[Dict]) -> pd.DataFrame:
        """Detect when liquidity zones are swept"""
        data['liquidity_swept'] = False
        data['sweep_type'] = ''
        
        for zone in zones:
            for idx in data.index:
                if idx <= zone['created_at']:
                    continue
                
                candle = data.loc[idx]
                
                # Check for sweep (price goes through zone and then reverses)
                if zone['type'] in ['resistance', 'session_high']:
                    # Bullish sweep (price breaks above resistance and comes back)
                    if candle['high'] > zone['upper_bound']:
                        # Check for reversal in next few candles
                        if self._check_reversal_after_sweep(data, idx, zone, 'bullish'):
                            data.loc[idx, 'liquidity_swept'] = True
                            data.loc[idx, 'sweep_type'] = 'bullish_sweep'
                
                elif zone['type'] in ['support', 'session_low']:
                    # Bearish sweep (price breaks below support and comes back)
                    if candle['low'] < zone['lower_bound']:
                        # Check for reversal in next few candles
                        if self._check_reversal_after_sweep(data, idx, zone, 'bearish'):
                            data.loc[idx, 'liquidity_swept'] = True
                            data.loc[idx, 'sweep_type'] = 'bearish_sweep'
        
        return data
    
    def _check_reversal_after_sweep(self, data: pd.DataFrame, sweep_idx: int, 
                                   zone: Dict, sweep_type: str) -> bool:
        """Check for price reversal after liquidity sweep"""
        lookforward = 5  # Look 5 candles ahead
        
        try:
            # Get position-based index
            if isinstance(sweep_idx, pd.Timestamp):
                sweep_position = data.index.get_loc(sweep_idx)
            else:
                sweep_position = sweep_idx
            
            for i in range(1, lookforward + 1):
                check_position = sweep_position + i
                if check_position >= len(data):
                    break
                
                candle = data.iloc[check_position]
                
                if sweep_type == 'bullish':
                    # After bullish sweep, price should come back into or below the zone
                    if candle['close'] <= zone['price']:
                        return True
                else:  # bearish sweep
                    # After bearish sweep, price should come back into or above the zone
                    if candle['close'] >= zone['price']:
                        return True
        except (KeyError, IndexError):
            pass
        
        return False
    
    def _detect_zone_retests(self, data: pd.DataFrame, zones: List[Dict]) -> pd.DataFrame:
        """Detect retests of liquidity zones"""
        data['zone_retest'] = False
        data['retest_type'] = ''
        
        for zone in zones:
            retest_count = 0
            
            for idx in data.index:
                if idx <= zone['created_at']:
                    continue
                
                candle = data.loc[idx]
                
                # Check if price is retesting the zone
                in_zone = (candle['low'] <= zone['upper_bound'] and 
                          candle['high'] >= zone['lower_bound'])
                
                if in_zone:
                    retest_count += 1
                    
                    # Determine retest type based on zone type and price action
                    if zone['type'] in ['resistance', 'session_high']:
                        if candle['close'] < zone['price']:  # Rejection from resistance
                            data.loc[idx, 'zone_retest'] = True
                            data.loc[idx, 'retest_type'] = 'resistance_rejection'
                        elif candle['close'] > zone['upper_bound']:  # Break above
                            data.loc[idx, 'zone_retest'] = True
                            data.loc[idx, 'retest_type'] = 'resistance_break'
                    
                    elif zone['type'] in ['support', 'session_low']:
                        if candle['close'] > zone['price']:  # Bounce from support
                            data.loc[idx, 'zone_retest'] = True
                            data.loc[idx, 'retest_type'] = 'support_bounce'
                        elif candle['close'] < zone['lower_bound']:  # Break below
                            data.loc[idx, 'zone_retest'] = True
                            data.loc[idx, 'retest_type'] = 'support_break'
        
        return data
    
    def get_active_zones(self, data: pd.DataFrame, lookback: int = 100) -> List[Dict]:
        """Get currently active liquidity zones"""
        # This would return zones that are still relevant
        # Implementation would filter zones based on recent price action
        recent_data = data.tail(lookback)
        current_price = recent_data['close'].iloc[-1]
        
        active_zones = []
        
        # Get zones from recent data analysis
        zones = self.detect_liquidity_zones(recent_data)
        
        # Filter for zones close to current price
        price_range = current_price * 0.05  # 5% range
        
        for idx in zones.index:
            if zones.loc[idx, 'liquidity_zone']:
                zone_price = zones.loc[idx, 'close']  # Use close as proxy for zone price
                if abs(zone_price - current_price) <= price_range:
                    active_zones.append({
                        'price': zone_price,
                        'type': zones.loc[idx, 'zone_type'],
                        'strength': zones.loc[idx, 'zone_strength'],
                        'index': idx
                    })
        
        return active_zones