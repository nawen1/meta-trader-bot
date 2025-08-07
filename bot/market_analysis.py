"""
Market Analysis Module - Trap identification and market structure analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, NamedTuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketStructure(Enum):
    """Market structure types"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"


class LiquidityLevel(NamedTuple):
    """Represents a liquidity level"""
    price: float
    volume: float
    timestamp: pd.Timestamp
    level_type: str  # 'support' or 'resistance'


class TrapSignal(NamedTuple):
    """Represents a trap signal"""
    entry_price: float
    stop_loss: float
    take_profits: List[float]
    confidence: float
    trap_type: str  # 'bull_trap' or 'bear_trap'
    liquidity_above: float
    liquidity_below: float
    safe_entry_exists: bool


class MarketAnalyzer:
    """Advanced market analysis for trap identification"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def identify_liquidity_levels(self, df: pd.DataFrame) -> List[LiquidityLevel]:
        """
        Identify liquidity levels based on volume and price action
        """
        liquidity_levels = []
        
        # Calculate volume-weighted average price (VWAP)
        df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        
        # Identify support and resistance levels
        window = 20
        df['resistance'] = df['high'].rolling(window=window, center=True).max()
        df['support'] = df['low'].rolling(window=window, center=True).min()
        
        # Find significant volume spikes
        volume_threshold = df['volume'].quantile(0.8)
        high_volume_bars = df[df['volume'] > volume_threshold]
        
        for idx, row in high_volume_bars.iterrows():
            # Check for resistance level
            if row['high'] == df.loc[max(0, idx-window):min(len(df), idx+window), 'high'].max():
                liquidity_levels.append(LiquidityLevel(
                    price=row['high'],
                    volume=row['volume'],
                    timestamp=row.name if hasattr(row, 'name') else pd.Timestamp.now(),
                    level_type='resistance'
                ))
            
            # Check for support level
            if row['low'] == df.loc[max(0, idx-window):min(len(df), idx+window), 'low'].min():
                liquidity_levels.append(LiquidityLevel(
                    price=row['low'],
                    volume=row['volume'],
                    timestamp=row.name if hasattr(row, 'name') else pd.Timestamp.now(),
                    level_type='support'
                ))
        
        return sorted(liquidity_levels, key=lambda x: x.volume, reverse=True)
    
    def identify_inductions(self, df: pd.DataFrame) -> List[Dict]:
        """
        Identify market inductions (false breakouts that lead to reversals)
        """
        inductions = []
        confirmation_bars = self.config.trap_identification.induction_confirmation_bars
        
        # Calculate key levels
        df['swing_high'] = df['high'].rolling(window=10, center=True).max()
        df['swing_low'] = df['low'].rolling(window=10, center=True).min()
        
        for i in range(confirmation_bars, len(df) - confirmation_bars):
            current_bar = df.iloc[i]
            
            # Check for bullish induction (false breakdown)
            if self._is_bullish_induction(df, i, confirmation_bars):
                inductions.append({
                    'type': 'bullish_induction',
                    'entry_bar': i,
                    'fake_breakdown_price': df.iloc[i]['low'],
                    'reversal_confirmation': i + confirmation_bars,
                    'strength': self._calculate_induction_strength(df, i, 'bullish')
                })
            
            # Check for bearish induction (false breakout)
            elif self._is_bearish_induction(df, i, confirmation_bars):
                inductions.append({
                    'type': 'bearish_induction',
                    'entry_bar': i,
                    'fake_breakout_price': df.iloc[i]['high'],
                    'reversal_confirmation': i + confirmation_bars,
                    'strength': self._calculate_induction_strength(df, i, 'bearish')
                })
        
        return inductions
    
    def _is_bullish_induction(self, df: pd.DataFrame, idx: int, confirmation_bars: int) -> bool:
        """Check if the current bar represents a bullish induction"""
        current = df.iloc[idx]
        prev_support = df.iloc[max(0, idx-20):idx]['low'].min()
        
        # Fake breakdown below support
        fake_breakdown = current['low'] < prev_support
        
        # Reversal confirmation in next bars
        reversal_confirmed = all(
            df.iloc[idx + i]['close'] > current['low'] 
            for i in range(1, min(confirmation_bars + 1, len(df) - idx))
        )
        
        return fake_breakdown and reversal_confirmed
    
    def _is_bearish_induction(self, df: pd.DataFrame, idx: int, confirmation_bars: int) -> bool:
        """Check if the current bar represents a bearish induction"""
        current = df.iloc[idx]
        prev_resistance = df.iloc[max(0, idx-20):idx]['high'].max()
        
        # Fake breakout above resistance
        fake_breakout = current['high'] > prev_resistance
        
        # Reversal confirmation in next bars
        reversal_confirmed = all(
            df.iloc[idx + i]['close'] < current['high'] 
            for i in range(1, min(confirmation_bars + 1, len(df) - idx))
        )
        
        return fake_breakout and reversal_confirmed
    
    def _calculate_induction_strength(self, df: pd.DataFrame, idx: int, induction_type: str) -> float:
        """Calculate the strength of an induction signal"""
        volume_strength = df.iloc[idx]['volume'] / df['volume'].rolling(20).mean().iloc[idx]
        
        if induction_type == 'bullish':
            price_strength = abs(df.iloc[idx]['low'] - df.iloc[max(0, idx-20):idx]['low'].min()) / df.iloc[idx]['close']
        else:
            price_strength = abs(df.iloc[idx]['high'] - df.iloc[max(0, idx-20):idx]['high'].max()) / df.iloc[idx]['close']
        
        return min(1.0, (volume_strength + price_strength) / 2)
    
    def identify_traps(self, df: pd.DataFrame, liquidity_levels: List[LiquidityLevel]) -> List[TrapSignal]:
        """
        Identify trap setups based on liquidity and inductions
        """
        traps = []
        inductions = self.identify_inductions(df)
        
        for induction in inductions:
            trap_signal = self._analyze_trap_opportunity(df, induction, liquidity_levels)
            if trap_signal and trap_signal.confidence >= self.config.min_entry_confidence:
                traps.append(trap_signal)
        
        return traps
    
    def _analyze_trap_opportunity(self, df: pd.DataFrame, induction: Dict, 
                                 liquidity_levels: List[LiquidityLevel]) -> Optional[TrapSignal]:
        """Analyze if an induction presents a valid trap trading opportunity"""
        
        entry_idx = induction['entry_bar']
        current_price = df.iloc[entry_idx]['close']
        
        # Find relevant liquidity levels
        liquidity_above = self._find_liquidity_above(current_price, liquidity_levels)
        liquidity_below = self._find_liquidity_below(current_price, liquidity_levels)
        
        # Check if liquidity meets minimum threshold
        if not self._validate_liquidity_threshold(liquidity_above, liquidity_below):
            return None
        
        # Determine trap type and entry parameters
        if induction['type'] == 'bullish_induction':
            return self._create_bullish_trap_signal(df, induction, liquidity_above, liquidity_below)
        else:
            return self._create_bearish_trap_signal(df, induction, liquidity_above, liquidity_below)
    
    def _find_liquidity_above(self, price: float, levels: List[LiquidityLevel]) -> float:
        """Find total liquidity above current price"""
        return sum(level.volume for level in levels 
                  if level.price > price and level.level_type == 'resistance')
    
    def _find_liquidity_below(self, price: float, levels: List[LiquidityLevel]) -> float:
        """Find total liquidity below current price"""
        return sum(level.volume for level in levels 
                  if level.price < price and level.level_type == 'support')
    
    def _validate_liquidity_threshold(self, liquidity_above: float, liquidity_below: float) -> bool:
        """Validate that liquidity meets minimum thresholds"""
        total_liquidity = liquidity_above + liquidity_below
        threshold = self.config.trap_identification.liquidity_threshold
        
        return total_liquidity > 0 and (liquidity_above / total_liquidity > threshold or 
                                       liquidity_below / total_liquidity > threshold)
    
    def _create_bullish_trap_signal(self, df: pd.DataFrame, induction: Dict, 
                                   liquidity_above: float, liquidity_below: float) -> TrapSignal:
        """Create a bullish trap signal"""
        entry_price = df.iloc[induction['entry_bar']]['close']
        fake_low = induction['fake_breakdown_price']
        
        # Calculate stop loss and take profits
        stop_loss = fake_low * 0.995  # Slight buffer below fake breakdown
        risk = entry_price - stop_loss
        
        take_profits = [
            entry_price + risk * self.config.risk_management.tp1_ratio,
            entry_price + risk * self.config.risk_management.tp2_ratio,
            entry_price + risk * self.config.risk_management.tp3_ratio
        ]
        
        # Check for safe entry point before trap
        safe_entry = self._has_safe_entry_point(df, induction['entry_bar'], 'bullish')
        
        confidence = min(1.0, induction['strength'] * 
                        (liquidity_below / (liquidity_above + liquidity_below + 1)))
        
        return TrapSignal(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            confidence=confidence,
            trap_type='bull_trap',
            liquidity_above=liquidity_above,
            liquidity_below=liquidity_below,
            safe_entry_exists=safe_entry
        )
    
    def _create_bearish_trap_signal(self, df: pd.DataFrame, induction: Dict, 
                                   liquidity_above: float, liquidity_below: float) -> TrapSignal:
        """Create a bearish trap signal"""
        entry_price = df.iloc[induction['entry_bar']]['close']
        fake_high = induction['fake_breakout_price']
        
        # Calculate stop loss and take profits
        stop_loss = fake_high * 1.005  # Slight buffer above fake breakout
        risk = stop_loss - entry_price
        
        take_profits = [
            entry_price - risk * self.config.risk_management.tp1_ratio,
            entry_price - risk * self.config.risk_management.tp2_ratio,
            entry_price - risk * self.config.risk_management.tp3_ratio
        ]
        
        # Check for safe entry point before trap
        safe_entry = self._has_safe_entry_point(df, induction['entry_bar'], 'bearish')
        
        confidence = min(1.0, induction['strength'] * 
                        (liquidity_above / (liquidity_above + liquidity_below + 1)))
        
        return TrapSignal(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            confidence=confidence,
            trap_type='bear_trap',
            liquidity_above=liquidity_above,
            liquidity_below=liquidity_below,
            safe_entry_exists=safe_entry
        )
    
    def _has_safe_entry_point(self, df: pd.DataFrame, trap_bar: int, direction: str) -> bool:
        """Check if there's a safe entry point before the trap"""
        lookback = min(10, trap_bar)
        
        for i in range(trap_bar - lookback, trap_bar):
            if i < 0:
                continue
                
            current_bar = df.iloc[i]
            
            if direction == 'bullish':
                # Look for a higher low or consolidation before the trap
                if (current_bar['low'] > df.iloc[max(0, i-5):i]['low'].min() and
                    current_bar['close'] > current_bar['open']):
                    return True
            else:
                # Look for a lower high or consolidation before the trap
                if (current_bar['high'] < df.iloc[max(0, i-5):i]['high'].max() and
                    current_bar['close'] < current_bar['open']):
                    return True
        
        return False
    
    def analyze_higher_timeframes(self, df_dict: Dict[str, pd.DataFrame]) -> Dict[str, MarketStructure]:
        """Analyze market structure on higher timeframes for context"""
        htf_analysis = {}
        
        for timeframe, df in df_dict.items():
            if timeframe in self.config.analysis.higher_timeframes:
                structure = self._determine_market_structure(df)
                htf_analysis[timeframe] = structure
        
        return htf_analysis
    
    def _determine_market_structure(self, df: pd.DataFrame) -> MarketStructure:
        """Determine the overall market structure for a timeframe"""
        if len(df) < 50:
            return MarketStructure.SIDEWAYS
        
        # Calculate trend using moving averages
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma50'] = df['close'].rolling(50).mean()
        
        current_close = df['close'].iloc[-1]
        ma20 = df['ma20'].iloc[-1]
        ma50 = df['ma50'].iloc[-1]
        
        # Determine trend direction
        if current_close > ma20 > ma50 and ma20 > df['ma20'].iloc[-10]:
            return MarketStructure.BULLISH
        elif current_close < ma20 < ma50 and ma20 < df['ma20'].iloc[-10]:
            return MarketStructure.BEARISH
        else:
            return MarketStructure.SIDEWAYS