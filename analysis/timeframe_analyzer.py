"""
Multi-Timeframe Analysis
Analyzes higher timeframes for context before determining entries in lower timeframes
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from utils.data_handler import DataHandler
from utils.config import TradingConfig
from analysis.fractals import FractalAnalyzer
from analysis.choch_detector import CHOCHDetector
from analysis.liquidity_zones import LiquidityZoneDetector
import logging

logger = logging.getLogger(__name__)

class TimeframeAnalyzer:
    """
    Analyzes multiple timeframes to provide context for trading decisions
    Uses higher TF as context before determining entries in lower TF
    """
    
    def __init__(self, config: TradingConfig):
        """
        Initialize timeframe analyzer
        
        Args:
            config: Trading configuration with timeframe settings
        """
        self.config = config
        self.data_handler = DataHandler()
        self.fractal_analyzer = FractalAnalyzer(period=config.fractal_period)
        self.choch_detector = CHOCHDetector(confirmation_period=config.choch_confirmation_period)
        self.liquidity_detector = LiquidityZoneDetector(zone_buffer=config.liquidity_zone_buffer)
        
        # Cache for analyzed data
        self.analysis_cache: Dict[str, Dict[str, pd.DataFrame]] = {}
    
    def analyze_symbol(self, symbol: str) -> Dict[str, Dict]:
        """
        Perform comprehensive multi-timeframe analysis for a symbol
        
        Args:
            symbol: Trading symbol to analyze
            
        Returns:
            Dictionary with analysis results for each timeframe
        """
        logger.info(f"Starting multi-timeframe analysis for {symbol}")
        
        # Fetch data for all timeframes
        all_timeframes = self.config.timeframes.higher_timeframes + self.config.timeframes.lower_timeframes
        timeframe_data = self.data_handler.get_multiple_timeframes(
            symbol, all_timeframes, self.config.timeframes.context_period
        )
        
        analysis_results = {}
        
        # Analyze each timeframe
        for timeframe in all_timeframes:
            if timeframe in timeframe_data and not timeframe_data[timeframe].empty:
                logger.info(f"Analyzing {symbol} on {timeframe}")
                analysis_results[timeframe] = self._analyze_timeframe(
                    timeframe_data[timeframe], timeframe, symbol
                )
            else:
                logger.warning(f"No data available for {symbol} on {timeframe}")
                analysis_results[timeframe] = self._empty_analysis()
        
        # Create comprehensive context analysis
        context_analysis = self._create_context_analysis(analysis_results)
        
        # Generate trading opportunities based on multi-timeframe alignment
        opportunities = self._identify_trading_opportunities(analysis_results, context_analysis)
        
        return {
            'timeframe_analysis': analysis_results,
            'context_analysis': context_analysis,
            'opportunities': opportunities,
            'last_update': pd.Timestamp.now()
        }
    
    def _analyze_timeframe(self, data: pd.DataFrame, timeframe: str, symbol: str) -> Dict:
        """
        Analyze a single timeframe
        
        Args:
            data: OHLCV data for the timeframe
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Analysis results for the timeframe
        """
        try:
            # Add basic indicators
            data = self.data_handler.calculate_indicators(data)
            
            # Fractal analysis
            fractal_data = self.fractal_analyzer.identify_fractals(data)
            
            # CHOCH analysis
            choch_data = self.choch_detector.detect_choch(fractal_data, fractal_data)
            
            # Liquidity zone analysis
            liquidity_data = self.liquidity_detector.detect_liquidity_zones(choch_data, fractal_data)
            
            # Market structure analysis
            market_structure = self._analyze_market_structure(liquidity_data)
            
            # Trend analysis
            trend_analysis = self._analyze_trend(liquidity_data)
            
            # Support/Resistance levels
            key_levels = self._identify_key_levels(liquidity_data)
            
            # Cache the analyzed data
            cache_key = f"{symbol}_{timeframe}"
            if symbol not in self.analysis_cache:
                self.analysis_cache[symbol] = {}
            self.analysis_cache[symbol][timeframe] = liquidity_data
            
            return {
                'data': liquidity_data,
                'market_structure': market_structure,
                'trend': trend_analysis,
                'key_levels': key_levels,
                'fractals': self.fractal_analyzer.get_recent_fractals(fractal_data),
                'choch': self.choch_detector.get_current_market_structure(choch_data),
                'liquidity_zones': self.liquidity_detector.get_active_zones(liquidity_data),
                'timeframe': timeframe,
                'last_price': liquidity_data['close'].iloc[-1],
                'analysis_time': pd.Timestamp.now()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} on {timeframe}: {str(e)}")
            return self._empty_analysis()
    
    def _analyze_market_structure(self, data: pd.DataFrame) -> Dict:
        """Analyze current market structure"""
        try:
            # Get recent price action
            recent_data = data.tail(50)
            
            # Identify swing points
            swing_highs = []
            swing_lows = []
            
            # Use fractal data if available
            if 'fractal_high' in recent_data.columns:
                for idx in recent_data.index:
                    if recent_data.loc[idx, 'fractal_high']:
                        swing_highs.append((idx, recent_data.loc[idx, 'high']))
                    if recent_data.loc[idx, 'fractal_low']:
                        swing_lows.append((idx, recent_data.loc[idx, 'low']))
            
            # Determine structure type
            structure_type = self._determine_structure_type(swing_highs, swing_lows)
            
            # Calculate structure strength
            structure_strength = self._calculate_structure_strength(recent_data, swing_highs, swing_lows)
            
            # Identify break of structure
            bos_signals = self._identify_bos(recent_data, swing_highs, swing_lows)
            
            return {
                'type': structure_type,
                'strength': structure_strength,
                'swing_highs': swing_highs[-3:] if len(swing_highs) >= 3 else swing_highs,
                'swing_lows': swing_lows[-3:] if len(swing_lows) >= 3 else swing_lows,
                'break_of_structure': bos_signals,
                'last_structure_update': recent_data.index[-1]
            }
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {str(e)}")
            return {'type': 'unknown', 'strength': 0.0, 'swing_highs': [], 'swing_lows': []}
    
    def _determine_structure_type(self, swing_highs: List[Tuple], swing_lows: List[Tuple]) -> str:
        """Determine if market structure is bullish, bearish, or ranging"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'ranging'
        
        # Check for higher highs and higher lows (bullish)
        recent_highs = sorted(swing_highs, key=lambda x: x[0])[-2:]
        recent_lows = sorted(swing_lows, key=lambda x: x[0])[-2:]
        
        higher_highs = recent_highs[1][1] > recent_highs[0][1]
        higher_lows = recent_lows[1][1] > recent_lows[0][1]
        
        # Check for lower highs and lower lows (bearish)
        lower_highs = recent_highs[1][1] < recent_highs[0][1]
        lower_lows = recent_lows[1][1] < recent_lows[0][1]
        
        if higher_highs and higher_lows:
            return 'bullish'
        elif lower_highs and lower_lows:
            return 'bearish'
        else:
            return 'ranging'
    
    def _calculate_structure_strength(self, data: pd.DataFrame, swing_highs: List[Tuple], 
                                    swing_lows: List[Tuple]) -> float:
        """Calculate the strength of the current market structure"""
        if len(data) < 20:
            return 0.0
        
        # Price momentum
        price_change = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
        momentum_score = min(abs(price_change) * 10, 1.0)
        
        # Trend consistency (using EMA alignment)
        if 'ema_20' in data.columns and 'ema_50' in data.columns:
            ema_alignment = 1.0 if data['ema_20'].iloc[-1] > data['ema_50'].iloc[-1] else 0.0
        else:
            ema_alignment = 0.5
        
        # Volume confirmation
        volume_score = 0.5  # Default if volume not available
        if 'volume' in data.columns and data['volume'].sum() > 0:
            recent_volume = data['volume'].tail(10).mean()
            avg_volume = data['volume'].mean()
            volume_score = min(recent_volume / avg_volume, 2.0) / 2.0
        
        # Combine scores
        total_strength = (momentum_score * 0.4 + ema_alignment * 0.3 + volume_score * 0.3)
        return min(total_strength, 1.0)
    
    def _identify_bos(self, data: pd.DataFrame, swing_highs: List[Tuple], 
                     swing_lows: List[Tuple]) -> List[Dict]:
        """Identify break of structure signals"""
        bos_signals = []
        
        # Look for recent breaks
        recent_data = data.tail(20)
        
        for idx in recent_data.index:
            current_price = recent_data.loc[idx, 'close']
            
            # Check for bullish BOS (break above recent swing high)
            for swing_idx, swing_price in swing_highs:
                if swing_idx < idx and current_price > swing_price:
                    bos_signals.append({
                        'type': 'bullish_bos',
                        'index': idx,
                        'price': current_price,
                        'broken_level': swing_price,
                        'strength': min((current_price - swing_price) / swing_price * 100, 1.0)
                    })
                    break
            
            # Check for bearish BOS (break below recent swing low)
            for swing_idx, swing_price in swing_lows:
                if swing_idx < idx and current_price < swing_price:
                    bos_signals.append({
                        'type': 'bearish_bos',
                        'index': idx,
                        'price': current_price,
                        'broken_level': swing_price,
                        'strength': min((swing_price - current_price) / swing_price * 100, 1.0)
                    })
                    break
        
        return bos_signals
    
    def _analyze_trend(self, data: pd.DataFrame) -> Dict:
        """Analyze overall trend direction and strength"""
        try:
            # Multiple trend indicators
            trends = {}
            
            # EMA trend
            if 'ema_20' in data.columns and 'ema_50' in data.columns:
                ema_trend = 'bullish' if data['ema_20'].iloc[-1] > data['ema_50'].iloc[-1] else 'bearish'
                trends['ema'] = ema_trend
            
            # Price vs MA trend
            if 'sma_200' in data.columns:
                ma_trend = 'bullish' if data['close'].iloc[-1] > data['sma_200'].iloc[-1] else 'bearish'
                trends['ma_200'] = ma_trend
            
            # Momentum trend (RSI)
            if 'rsi' in data.columns:
                rsi_value = data['rsi'].iloc[-1]
                if rsi_value > 60:
                    rsi_trend = 'bullish'
                elif rsi_value < 40:
                    rsi_trend = 'bearish'
                else:
                    rsi_trend = 'neutral'
                trends['rsi'] = rsi_trend
            
            # Price action trend
            price_change_20 = (data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
            if price_change_20 > 0.02:
                trends['price_action'] = 'bullish'
            elif price_change_20 < -0.02:
                trends['price_action'] = 'bearish'
            else:
                trends['price_action'] = 'neutral'
            
            # Overall trend consensus
            bullish_count = sum(1 for trend in trends.values() if trend == 'bullish')
            bearish_count = sum(1 for trend in trends.values() if trend == 'bearish')
            
            if bullish_count > bearish_count:
                overall_trend = 'bullish'
                trend_strength = bullish_count / len(trends)
            elif bearish_count > bullish_count:
                overall_trend = 'bearish'
                trend_strength = bearish_count / len(trends)
            else:
                overall_trend = 'neutral'
                trend_strength = 0.5
            
            return {
                'overall': overall_trend,
                'strength': trend_strength,
                'components': trends,
                'momentum': rsi_value if 'rsi' in data.columns else 50
            }
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            return {'overall': 'neutral', 'strength': 0.5, 'components': {}}
    
    def _identify_key_levels(self, data: pd.DataFrame) -> Dict:
        """Identify key support and resistance levels"""
        try:
            support_levels = []
            resistance_levels = []
            
            # From liquidity zones
            if 'liquidity_zone' in data.columns:
                zone_data = data[data['liquidity_zone']].tail(10)  # Recent zones
                for idx in zone_data.index:
                    zone_type = zone_data.loc[idx, 'zone_type']
                    price = zone_data.loc[idx, 'close']
                    strength = zone_data.loc[idx, 'zone_strength']
                    
                    if 'support' in zone_type or 'demand' in zone_type:
                        support_levels.append({'price': price, 'strength': strength, 'type': zone_type})
                    elif 'resistance' in zone_type or 'supply' in zone_type:
                        resistance_levels.append({'price': price, 'strength': strength, 'type': zone_type})
            
            # From fractals
            if 'fractal_high' in data.columns and 'fractal_low' in data.columns:
                recent_fractals = data.tail(50)
                
                # Resistance from fractal highs
                fractal_highs = recent_fractals[recent_fractals['fractal_high']]
                for idx in fractal_highs.index:
                    price = fractal_highs.loc[idx, 'fractal_high_price']
                    strength = fractal_highs.loc[idx, 'fractal_strength'] if 'fractal_strength' in fractal_highs.columns else 0.5
                    resistance_levels.append({'price': price, 'strength': strength, 'type': 'fractal_high'})
                
                # Support from fractal lows
                fractal_lows = recent_fractals[recent_fractals['fractal_low']]
                for idx in fractal_lows.index:
                    price = fractal_lows.loc[idx, 'fractal_low_price']
                    strength = fractal_lows.loc[idx, 'fractal_strength'] if 'fractal_strength' in fractal_lows.columns else 0.5
                    support_levels.append({'price': price, 'strength': strength, 'type': 'fractal_low'})
            
            # Sort by strength and remove duplicates
            support_levels = sorted(support_levels, key=lambda x: x['strength'], reverse=True)[:5]
            resistance_levels = sorted(resistance_levels, key=lambda x: x['strength'], reverse=True)[:5]
            
            return {
                'support': support_levels,
                'resistance': resistance_levels,
                'current_price': data['close'].iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error identifying key levels: {str(e)}")
            return {'support': [], 'resistance': [], 'current_price': data['close'].iloc[-1]}
    
    def _create_context_analysis(self, analysis_results: Dict[str, Dict]) -> Dict:
        """Create comprehensive context from all timeframes"""
        higher_tfs = self.config.timeframes.higher_timeframes
        lower_tfs = self.config.timeframes.lower_timeframes
        
        # Higher timeframe context
        htf_context = self._analyze_htf_context(analysis_results, higher_tfs)
        
        # Lower timeframe signals
        ltf_signals = self._analyze_ltf_signals(analysis_results, lower_tfs)
        
        # Multi-timeframe alignment
        alignment = self._calculate_timeframe_alignment(analysis_results)
        
        return {
            'htf_context': htf_context,
            'ltf_signals': ltf_signals,
            'alignment': alignment,
            'overall_bias': self._determine_overall_bias(htf_context, alignment)
        }
    
    def _analyze_htf_context(self, analysis_results: Dict, higher_tfs: List[str]) -> Dict:
        """Analyze higher timeframe context"""
        htf_trends = []
        htf_structures = []
        
        for tf in higher_tfs:
            if tf in analysis_results and analysis_results[tf]:
                trend = analysis_results[tf].get('trend', {}).get('overall', 'neutral')
                structure = analysis_results[tf].get('market_structure', {}).get('type', 'ranging')
                
                htf_trends.append(trend)
                htf_structures.append(structure)
        
        # Determine dominant HTF trend
        bullish_count = htf_trends.count('bullish')
        bearish_count = htf_trends.count('bearish')
        
        if bullish_count > bearish_count:
            dominant_trend = 'bullish'
        elif bearish_count > bullish_count:
            dominant_trend = 'bearish'
        else:
            dominant_trend = 'neutral'
        
        return {
            'dominant_trend': dominant_trend,
            'trend_strength': max(bullish_count, bearish_count) / len(htf_trends) if htf_trends else 0,
            'structures': htf_structures,
            'consensus': len([t for t in htf_trends if t == dominant_trend]) / len(htf_trends) if htf_trends else 0
        }
    
    def _analyze_ltf_signals(self, analysis_results: Dict, lower_tfs: List[str]) -> Dict:
        """Analyze lower timeframe entry signals"""
        signals = []
        
        for tf in lower_tfs:
            if tf in analysis_results and analysis_results[tf]:
                tf_analysis = analysis_results[tf]
                
                # Check for CHOCH signals
                choch = tf_analysis.get('choch', {})
                if choch.get('last_choch'):
                    signals.append({
                        'type': 'choch',
                        'timeframe': tf,
                        'direction': choch['last_choch'][0],
                        'strength': choch['last_choch'][2],
                        'recency': 0.8  # Recent signal
                    })
                
                # Check for BOS signals
                market_structure = tf_analysis.get('market_structure', {})
                bos_signals = market_structure.get('break_of_structure', [])
                if bos_signals:
                    latest_bos = bos_signals[-1]
                    signals.append({
                        'type': 'bos',
                        'timeframe': tf,
                        'direction': latest_bos['type'].replace('_bos', ''),
                        'strength': latest_bos['strength'],
                        'recency': 0.9  # Very recent
                    })
        
        return signals
    
    def _calculate_timeframe_alignment(self, analysis_results: Dict) -> Dict:
        """Calculate alignment across timeframes"""
        all_trends = []
        
        for tf, analysis in analysis_results.items():
            if analysis and 'trend' in analysis:
                trend = analysis['trend'].get('overall', 'neutral')
                all_trends.append(trend)
        
        if not all_trends:
            return {'score': 0.0, 'direction': 'neutral'}
        
        bullish_ratio = all_trends.count('bullish') / len(all_trends)
        bearish_ratio = all_trends.count('bearish') / len(all_trends)
        
        if bullish_ratio > 0.6:
            return {'score': bullish_ratio, 'direction': 'bullish'}
        elif bearish_ratio > 0.6:
            return {'score': bearish_ratio, 'direction': 'bearish'}
        else:
            return {'score': 0.5, 'direction': 'neutral'}
    
    def _determine_overall_bias(self, htf_context: Dict, alignment: Dict) -> str:
        """Determine overall trading bias"""
        htf_weight = 0.7  # Higher timeframe has more weight
        alignment_weight = 0.3
        
        htf_trend = htf_context.get('dominant_trend', 'neutral')
        alignment_direction = alignment.get('direction', 'neutral')
        
        if htf_trend == alignment_direction and htf_trend != 'neutral':
            return htf_trend
        elif htf_trend != 'neutral':
            return htf_trend  # HTF takes precedence
        else:
            return alignment_direction
    
    def _identify_trading_opportunities(self, analysis_results: Dict, context_analysis: Dict) -> List[Dict]:
        """Identify potential trading opportunities based on multi-timeframe analysis"""
        opportunities = []
        
        overall_bias = context_analysis.get('overall_bias', 'neutral')
        if overall_bias == 'neutral':
            return opportunities
        
        # Look for entry opportunities in lower timeframes that align with higher timeframe bias
        lower_tfs = self.config.timeframes.lower_timeframes
        
        for tf in lower_tfs:
            if tf in analysis_results and analysis_results[tf]:
                tf_analysis = analysis_results[tf]
                
                # Check for pullback opportunities
                opportunity = self._check_pullback_opportunity(tf_analysis, overall_bias, tf)
                if opportunity:
                    opportunities.append(opportunity)
                
                # Check for breakout opportunities
                opportunity = self._check_breakout_opportunity(tf_analysis, overall_bias, tf)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Sort by strength/quality
        opportunities.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        return opportunities
    
    def _check_pullback_opportunity(self, tf_analysis: Dict, bias: str, timeframe: str) -> Optional[Dict]:
        """Check for pullback trading opportunities"""
        # Implementation for pullback opportunity detection
        # This would look for retracements in the opposite direction of bias
        # that could provide good entry points
        
        market_structure = tf_analysis.get('market_structure', {})
        key_levels = tf_analysis.get('key_levels', {})
        
        if bias == 'bullish':
            # Look for pullbacks to support levels
            support_levels = key_levels.get('support', [])
            if support_levels:
                closest_support = min(support_levels, key=lambda x: abs(x['price'] - key_levels['current_price']))
                distance_to_support = abs(closest_support['price'] - key_levels['current_price']) / key_levels['current_price']
                
                if distance_to_support < 0.02:  # Within 2% of support
                    return {
                        'type': 'pullback',
                        'direction': 'bullish',
                        'timeframe': timeframe,
                        'entry_price': closest_support['price'],
                        'quality_score': closest_support['strength'] * 0.8,
                        'setup': 'pullback_to_support'
                    }
        
        elif bias == 'bearish':
            # Look for pullbacks to resistance levels
            resistance_levels = key_levels.get('resistance', [])
            if resistance_levels:
                closest_resistance = min(resistance_levels, key=lambda x: abs(x['price'] - key_levels['current_price']))
                distance_to_resistance = abs(closest_resistance['price'] - key_levels['current_price']) / key_levels['current_price']
                
                if distance_to_resistance < 0.02:  # Within 2% of resistance
                    return {
                        'type': 'pullback',
                        'direction': 'bearish',
                        'timeframe': timeframe,
                        'entry_price': closest_resistance['price'],
                        'quality_score': closest_resistance['strength'] * 0.8,
                        'setup': 'pullback_to_resistance'
                    }
        
        return None
    
    def _check_breakout_opportunity(self, tf_analysis: Dict, bias: str, timeframe: str) -> Optional[Dict]:
        """Check for breakout trading opportunities"""
        # Implementation for breakout opportunity detection
        market_structure = tf_analysis.get('market_structure', {})
        bos_signals = market_structure.get('break_of_structure', [])
        
        if bos_signals:
            latest_bos = bos_signals[-1]
            bos_direction = latest_bos['type'].replace('_bos', '')
            
            if bos_direction == bias:
                return {
                    'type': 'breakout',
                    'direction': bias,
                    'timeframe': timeframe,
                    'entry_price': latest_bos['price'],
                    'quality_score': latest_bos['strength'],
                    'setup': 'break_of_structure'
                }
        
        return None
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'data': pd.DataFrame(),
            'market_structure': {'type': 'unknown', 'strength': 0.0},
            'trend': {'overall': 'neutral', 'strength': 0.5},
            'key_levels': {'support': [], 'resistance': []},
            'fractals': {'highs': [], 'lows': []},
            'choch': {'trend': 'ranging', 'last_choch': None},
            'liquidity_zones': [],
            'timeframe': '',
            'last_price': 0.0,
            'analysis_time': pd.Timestamp.now()
        }