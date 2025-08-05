"""
Liquidity analyzer for detecting liquidity sweeps and zones.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from config import LIQUIDITY_CONFIG


class LiquidityAnalyzer:
    """
    Analyzes market liquidity patterns and detects liquidity sweeps,
    which are key zones for institutional trading activity.
    """
    
    def __init__(self):
        self.config = LIQUIDITY_CONFIG
        self.lookback_periods = self.config['lookback_periods']
        self.volume_threshold = self.config['min_volume_threshold']
    
    def analyze_liquidity(self, data: pd.DataFrame) -> Dict:
        """
        Comprehensive liquidity analysis.
        
        Args:
            data: OHLCV DataFrame with volume data
            
        Returns:
            Dictionary containing liquidity analysis
        """
        if data.empty or len(data) < self.lookback_periods:
            return self._empty_liquidity_analysis()
        
        # Detect liquidity pools
        liquidity_pools = self._detect_liquidity_pools(data)
        
        # Detect liquidity sweeps
        liquidity_sweeps = self._detect_liquidity_sweeps(data, liquidity_pools)
        
        # Identify liquidity zones
        liquidity_zones = self._identify_liquidity_zones(data, liquidity_pools)
        
        # Detect stop hunt patterns
        stop_hunts = self._detect_stop_hunts(data)
        
        # Calculate liquidity imbalance
        liquidity_imbalance = self._calculate_liquidity_imbalance(data)
        
        return {
            'liquidity_pools': liquidity_pools,
            'liquidity_sweeps': liquidity_sweeps,
            'liquidity_zones': liquidity_zones,
            'stop_hunts': stop_hunts,
            'liquidity_imbalance': liquidity_imbalance,
            'current_liquidity_state': self._assess_current_liquidity_state(data),
            'next_liquidity_target': self._identify_next_liquidity_target(liquidity_pools, data)
        }
    
    def _detect_liquidity_pools(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect areas of accumulated liquidity (high/low areas with volume).
        """
        liquidity_pools = []
        
        # Use volume-weighted approach to identify liquidity
        if 'volume' not in data.columns:
            # If no volume data, use price action patterns
            return self._detect_liquidity_pools_price_action(data)
        
        # Calculate volume moving average for comparison
        volume_ma = data['volume'].rolling(window=10).mean()
        
        for i in range(self.lookback_periods, len(data)):
            current_volume = data['volume'].iloc[i]
            avg_volume = volume_ma.iloc[i]
            
            # High volume suggests liquidity accumulation
            if current_volume > avg_volume * self.volume_threshold:
                # Determine if it's a high or low liquidity pool
                high_price = data['high'].iloc[i]
                low_price = data['low'].iloc[i]
                close_price = data['close'].iloc[i]
                
                # Check if price reached significant levels
                recent_highs = data['high'].iloc[i-self.lookback_periods:i].max()
                recent_lows = data['low'].iloc[i-self.lookback_periods:i].min()
                
                pool_type = None
                target_price = None
                
                if high_price >= recent_highs * 0.999:  # Near recent high
                    pool_type = 'sell_side_liquidity'
                    target_price = high_price
                elif low_price <= recent_lows * 1.001:  # Near recent low
                    pool_type = 'buy_side_liquidity'
                    target_price = low_price
                
                if pool_type:
                    liquidity_pools.append({
                        'index': i,
                        'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                        'type': pool_type,
                        'price': target_price,
                        'volume': current_volume,
                        'strength': current_volume / avg_volume,
                        'status': 'active'
                    })
        
        return liquidity_pools
    
    def _detect_liquidity_pools_price_action(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect liquidity pools using price action when volume data is not available.
        """
        liquidity_pools = []
        
        # Look for price levels that were tested multiple times
        for i in range(self.lookback_periods, len(data)):
            current_high = data['high'].iloc[i]
            current_low = data['low'].iloc[i]
            
            # Check recent price history for similar levels
            recent_data = data.iloc[i-self.lookback_periods:i]
            
            # Count touches near current high (sell-side liquidity)
            high_touches = sum(1 for price in recent_data['high'] 
                             if abs(price - current_high) / current_high < 0.002)
            
            # Count touches near current low (buy-side liquidity)
            low_touches = sum(1 for price in recent_data['low'] 
                            if abs(price - current_low) / current_low < 0.002)
            
            if high_touches >= 2:  # Multiple touches suggest liquidity
                liquidity_pools.append({
                    'index': i,
                    'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                    'type': 'sell_side_liquidity',
                    'price': current_high,
                    'volume': None,
                    'strength': high_touches,
                    'status': 'active'
                })
            
            if low_touches >= 2:
                liquidity_pools.append({
                    'index': i,
                    'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                    'type': 'buy_side_liquidity',
                    'price': current_low,
                    'volume': None,
                    'strength': low_touches,
                    'status': 'active'
                })
        
        return liquidity_pools
    
    def _detect_liquidity_sweeps(self, data: pd.DataFrame, 
                               liquidity_pools: List[Dict]) -> List[Dict]:
        """
        Detect when liquidity pools are swept (taken/consumed).
        """
        liquidity_sweeps = []
        
        for pool in liquidity_pools:
            pool_price = pool['price']
            pool_index = pool['index']
            pool_type = pool['type']
            
            # Look for sweeps after the pool formation
            for i in range(pool_index + 1, len(data)):
                current_high = data['high'].iloc[i]
                current_low = data['low'].iloc[i]
                current_close = data['close'].iloc[i]
                
                swept = False
                sweep_type = None
                
                # Check for sell-side liquidity sweep (price goes above and then reverses)
                if pool_type == 'sell_side_liquidity' and current_high > pool_price:
                    # Look for reversal within next few candles
                    reversal_found = False
                    for j in range(i, min(i + 3, len(data))):
                        if data['close'].iloc[j] < pool_price * 0.998:  # 0.2% below
                            reversal_found = True
                            break
                    
                    if reversal_found:
                        swept = True
                        sweep_type = 'sell_side_sweep'
                
                # Check for buy-side liquidity sweep (price goes below and then reverses)
                elif pool_type == 'buy_side_liquidity' and current_low < pool_price:
                    # Look for reversal within next few candles
                    reversal_found = False
                    for j in range(i, min(i + 3, len(data))):
                        if data['close'].iloc[j] > pool_price * 1.002:  # 0.2% above
                            reversal_found = True
                            break
                    
                    if reversal_found:
                        swept = True
                        sweep_type = 'buy_side_sweep'
                
                if swept:
                    liquidity_sweeps.append({
                        'pool_index': pool_index,
                        'sweep_index': i,
                        'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                        'type': sweep_type,
                        'pool_price': pool_price,
                        'sweep_price': current_high if sweep_type == 'sell_side_sweep' else current_low,
                        'reversal_strength': self._calculate_reversal_strength(data, i),
                        'volume': data['volume'].iloc[i] if 'volume' in data.columns else None
                    })
                    
                    # Mark pool as swept
                    pool['status'] = 'swept'
                    break
        
        return liquidity_sweeps
    
    def _identify_liquidity_zones(self, data: pd.DataFrame, 
                                liquidity_pools: List[Dict]) -> List[Dict]:
        """
        Identify broader liquidity zones based on multiple pools.
        """
        if not liquidity_pools:
            return []
        
        liquidity_zones = []
        
        # Group nearby liquidity pools into zones
        sell_side_pools = [p for p in liquidity_pools if p['type'] == 'sell_side_liquidity']
        buy_side_pools = [p for p in liquidity_pools if p['type'] == 'buy_side_liquidity']
        
        # Create sell-side liquidity zones
        if sell_side_pools:
            sell_prices = [p['price'] for p in sell_side_pools]
            zone_high = max(sell_prices)
            zone_low = min(sell_prices)
            
            liquidity_zones.append({
                'type': 'sell_side_zone',
                'high': zone_high,
                'low': zone_low,
                'strength': len(sell_side_pools),
                'pools': sell_side_pools
            })
        
        # Create buy-side liquidity zones
        if buy_side_pools:
            buy_prices = [p['price'] for p in buy_side_pools]
            zone_high = max(buy_prices)
            zone_low = min(buy_prices)
            
            liquidity_zones.append({
                'type': 'buy_side_zone',
                'high': zone_high,
                'low': zone_low,
                'strength': len(buy_side_pools),
                'pools': buy_side_pools
            })
        
        return liquidity_zones
    
    def _detect_stop_hunts(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect potential stop hunt patterns (quick moves that reverse).
        """
        stop_hunts = []
        
        for i in range(5, len(data) - 2):
            # Look for sudden price spikes that quickly reverse
            current_high = data['high'].iloc[i]
            current_low = data['low'].iloc[i]
            
            # Get context (5 candles before)
            context_highs = data['high'].iloc[i-5:i]
            context_lows = data['low'].iloc[i-5:i]
            context_avg_high = context_highs.mean()
            context_avg_low = context_lows.mean()
            
            # Check for upward spike and reversal
            if current_high > context_avg_high * 1.005:  # 0.5% above average
                # Check for reversal in next 2 candles
                reversal_found = False
                for j in range(i + 1, min(i + 3, len(data))):
                    if data['close'].iloc[j] < context_avg_high:
                        reversal_found = True
                        break
                
                if reversal_found:
                    stop_hunts.append({
                        'index': i,
                        'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                        'type': 'upward_stop_hunt',
                        'spike_price': current_high,
                        'context_level': context_avg_high,
                        'spike_magnitude': (current_high - context_avg_high) / context_avg_high
                    })
            
            # Check for downward spike and reversal
            if current_low < context_avg_low * 0.995:  # 0.5% below average
                # Check for reversal in next 2 candles
                reversal_found = False
                for j in range(i + 1, min(i + 3, len(data))):
                    if data['close'].iloc[j] > context_avg_low:
                        reversal_found = True
                        break
                
                if reversal_found:
                    stop_hunts.append({
                        'index': i,
                        'timestamp': data.index[i] if hasattr(data.index, 'to_pydatetime') else i,
                        'type': 'downward_stop_hunt',
                        'spike_price': current_low,
                        'context_level': context_avg_low,
                        'spike_magnitude': (context_avg_low - current_low) / context_avg_low
                    })
        
        return stop_hunts
    
    def _calculate_liquidity_imbalance(self, data: pd.DataFrame) -> Dict:
        """
        Calculate liquidity imbalance based on recent price action.
        """
        if len(data) < 10:
            return {'imbalance': 0, 'direction': 'neutral'}
        
        recent_data = data.tail(10)
        
        # Simple imbalance calculation based on wick analysis
        buy_pressure = 0
        sell_pressure = 0
        
        for _, candle in recent_data.iterrows():
            high = candle['high']
            low = candle['low']
            open_price = candle['open']
            close = candle['close']
            
            # Upper wick (sell pressure)
            upper_wick = high - max(open_price, close)
            # Lower wick (buy pressure)
            lower_wick = min(open_price, close) - low
            
            sell_pressure += upper_wick
            buy_pressure += lower_wick
        
        # Calculate imbalance ratio
        total_pressure = buy_pressure + sell_pressure
        if total_pressure > 0:
            imbalance = (buy_pressure - sell_pressure) / total_pressure
        else:
            imbalance = 0
        
        direction = 'bullish' if imbalance > 0.1 else 'bearish' if imbalance < -0.1 else 'neutral'
        
        return {
            'imbalance': imbalance,
            'direction': direction,
            'buy_pressure': buy_pressure,
            'sell_pressure': sell_pressure
        }
    
    def _assess_current_liquidity_state(self, data: pd.DataFrame) -> str:
        """
        Assess the current overall liquidity state of the market.
        """
        if len(data) < 5:
            return 'insufficient_data'
        
        recent_data = data.tail(5)
        
        # Check for high volatility (potential liquidity hunting)
        price_ranges = []
        for _, candle in recent_data.iterrows():
            range_pct = (candle['high'] - candle['low']) / candle['close']
            price_ranges.append(range_pct)
        
        avg_range = np.mean(price_ranges)
        
        if avg_range > 0.02:  # 2% average range
            return 'high_volatility_liquidity_hunting'
        elif avg_range < 0.005:  # 0.5% average range
            return 'low_volatility_consolidation'
        else:
            return 'normal_liquidity_state'
    
    def _identify_next_liquidity_target(self, liquidity_pools: List[Dict], 
                                      data: pd.DataFrame) -> Optional[Dict]:
        """
        Identify the next likely liquidity target based on current price and pools.
        """
        if not liquidity_pools or data.empty:
            return None
        
        current_price = data['close'].iloc[-1]
        active_pools = [p for p in liquidity_pools if p['status'] == 'active']
        
        if not active_pools:
            return None
        
        # Find closest liquidity pool
        closest_pool = None
        min_distance = float('inf')
        
        for pool in active_pools:
            distance = abs(pool['price'] - current_price)
            if distance < min_distance:
                min_distance = distance
                closest_pool = pool
        
        if closest_pool:
            return {
                'target_price': closest_pool['price'],
                'target_type': closest_pool['type'],
                'distance': min_distance,
                'distance_pct': min_distance / current_price * 100,
                'strength': closest_pool['strength']
            }
        
        return None
    
    def _calculate_reversal_strength(self, data: pd.DataFrame, sweep_index: int) -> float:
        """
        Calculate the strength of reversal after a liquidity sweep.
        """
        if sweep_index + 3 >= len(data):
            return 0.0
        
        sweep_price = data['close'].iloc[sweep_index]
        
        # Look at next 3 candles for reversal strength
        max_reversal = 0.0
        for i in range(sweep_index + 1, min(sweep_index + 4, len(data))):
            reversal_pct = abs(data['close'].iloc[i] - sweep_price) / sweep_price
            max_reversal = max(max_reversal, reversal_pct)
        
        return max_reversal * 100  # Return as percentage
    
    def _empty_liquidity_analysis(self) -> Dict:
        """Return empty liquidity analysis structure."""
        return {
            'liquidity_pools': [],
            'liquidity_sweeps': [],
            'liquidity_zones': [],
            'stop_hunts': [],
            'liquidity_imbalance': {'imbalance': 0, 'direction': 'neutral'},
            'current_liquidity_state': 'insufficient_data',
            'next_liquidity_target': None
        }