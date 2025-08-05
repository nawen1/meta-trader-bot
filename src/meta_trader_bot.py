"""
Main Multi-Timeframe Trading Bot.
Orchestrates all analysis components with strict timeframe hierarchy.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from config import TIMEFRAMES_ORDERED, ENTRY_CONFIG
from timeframe_analyzer import TimeframeAnalyzer
from market_structure import MarketStructureAnalyzer
from liquidity_analyzer import LiquidityAnalyzer
from support_resistance import SupportResistanceAnalyzer
from entry_signals import EntrySignalGenerator


class MetaTraderBot:
    """
    Main trading bot that implements multi-timeframe analysis with strict hierarchy.
    Higher timeframes always take precedence over lower timeframes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the trading bot with all analysis components.
        
        Args:
            config: Optional configuration overrides
        """
        self.config = config or {}
        
        # Initialize analysis components
        self.tf_analyzer = TimeframeAnalyzer()
        self.structure_analyzer = MarketStructureAnalyzer()
        self.liquidity_analyzer = LiquidityAnalyzer()
        self.sr_analyzer = SupportResistanceAnalyzer()
        self.entry_generator = EntrySignalGenerator()
        
        # Bot state
        self.last_analysis = {}
        self.analysis_history = []
        self.active_signals = []
        
        print(f"MetaTraderBot initialized with timeframe hierarchy: {TIMEFRAMES_ORDERED}")
    
    def analyze_market(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Comprehensive market analysis across all timeframes.
        
        Args:
            market_data: Dictionary with timeframe keys and OHLCV DataFrames
            
        Returns:
            Complete market analysis with timeframe hierarchy
        """
        analysis_timestamp = datetime.now()
        
        print(f"\n=== Market Analysis Started at {analysis_timestamp} ===")
        
        # Step 1: Validate data
        validated_data = self._validate_market_data(market_data)
        if not validated_data:
            return self._empty_analysis("No valid market data provided")
        
        # Step 2: Analyze timeframe hierarchy
        print("Analyzing timeframe hierarchy...")
        tf_hierarchy = self.tf_analyzer.analyze_timeframe_hierarchy(validated_data)
        
        # Step 3: Analyze each timeframe in order of priority
        print("Analyzing individual timeframes...")
        timeframe_analyses = self._analyze_individual_timeframes(validated_data)
        
        # Step 4: Determine market context from higher timeframes
        print("Determining market context from higher timeframes...")
        market_context = self._determine_market_context(timeframe_analyses, tf_hierarchy)
        
        # Step 5: Identify zones and levels across timeframes
        print("Identifying key zones and levels...")
        key_zones = self._identify_key_zones(timeframe_analyses)
        
        # Step 6: Assess liquidity conditions
        print("Assessing liquidity conditions...")
        liquidity_assessment = self._assess_overall_liquidity(timeframe_analyses)
        
        # Compile complete analysis
        complete_analysis = {
            'timestamp': analysis_timestamp,
            'timeframe_hierarchy': tf_hierarchy,
            'market_context': market_context,
            'timeframe_analyses': timeframe_analyses,
            'key_zones': key_zones,
            'liquidity_assessment': liquidity_assessment,
            'trading_recommendation': self._generate_trading_recommendation(
                market_context, tf_hierarchy, key_zones
            )
        }
        
        # Store analysis
        self.last_analysis = complete_analysis
        self.analysis_history.append(complete_analysis)
        
        print(f"=== Market Analysis Completed ===\n")
        return complete_analysis
    
    def generate_entry_signals(self, market_data: Dict[str, pd.DataFrame], 
                             target_timeframe: str) -> Dict:
        """
        Generate entry signals for a specific timeframe with full context.
        
        Args:
            market_data: Multi-timeframe market data
            target_timeframe: Timeframe to generate signals for
            
        Returns:
            Entry signals with complete analysis context
        """
        print(f"\n=== Generating Entry Signals for {target_timeframe} ===")
        
        # First ensure we have current market analysis
        if not self.last_analysis or self._analysis_is_stale():
            print("Performing fresh market analysis...")
            self.analyze_market(market_data)
        
        # Generate signals using the entry generator
        signal_analysis = self.entry_generator.generate_entry_signals(
            market_data, target_timeframe
        )
        
        # Add bot context and validation
        enhanced_signals = self._enhance_signals_with_context(
            signal_analysis, target_timeframe
        )
        
        # Update active signals
        self._update_active_signals(enhanced_signals)
        
        print(f"Generated {len(enhanced_signals.get('signals', []))} valid signals")
        print(f"=== Entry Signal Generation Completed ===\n")
        
        return enhanced_signals
    
    def get_trading_recommendation(self) -> Dict:
        """
        Get current trading recommendation based on latest analysis.
        """
        if not self.last_analysis:
            return {
                'recommendation': 'NO_ACTION',
                'reason': 'No market analysis available',
                'confidence': 0.0
            }
        
        return self.last_analysis.get('trading_recommendation', {
            'recommendation': 'NO_ACTION',
            'reason': 'No recommendation generated',
            'confidence': 0.0
        })
    
    def get_market_summary(self) -> Dict:
        """
        Get a summary of current market conditions.
        """
        if not self.last_analysis:
            return {'status': 'No analysis available'}
        
        market_context = self.last_analysis.get('market_context', {})
        tf_hierarchy = self.last_analysis.get('timeframe_hierarchy', {})
        
        return {
            'overall_bias': market_context.get('overall_bias', 'Unknown'),
            'trend_strength': market_context.get('trend_strength', 0),
            'higher_tf_bias': tf_hierarchy.get('higher_tf_bias', 'Unknown'),
            'conflicting_signals': len(tf_hierarchy.get('conflicting_signals', [])),
            'aligned_timeframes': tf_hierarchy.get('entry_timeframes', []),
            'last_analysis_time': self.last_analysis.get('timestamp'),
            'active_signals': len(self.active_signals)
        }
    
    def _validate_market_data(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Validate and clean market data."""
        validated_data = {}
        
        for timeframe, data in market_data.items():
            if timeframe not in TIMEFRAMES_ORDERED:
                print(f"Warning: Unknown timeframe {timeframe}, skipping...")
                continue
            
            if data.empty:
                print(f"Warning: Empty data for timeframe {timeframe}, skipping...")
                continue
            
            # Check required columns
            required_columns = ['open', 'high', 'low', 'close']
            if not all(col in data.columns for col in required_columns):
                print(f"Warning: Missing required columns in {timeframe}, skipping...")
                continue
            
            # Basic data validation
            if len(data) < 50:  # Minimum data requirement
                print(f"Warning: Insufficient data for {timeframe} ({len(data)} candles), skipping...")
                continue
            
            validated_data[timeframe] = data
            print(f"Validated {timeframe}: {len(data)} candles")
        
        return validated_data
    
    def _analyze_individual_timeframes(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """Analyze each timeframe individually."""
        timeframe_analyses = {}
        
        for timeframe in TIMEFRAMES_ORDERED:
            if timeframe not in market_data:
                continue
            
            data = market_data[timeframe]
            print(f"  Analyzing {timeframe}...")
            
            # Comprehensive analysis for this timeframe
            analysis = {
                'timeframe': timeframe,
                'priority': self.tf_analyzer.get_timeframe_priority(timeframe),
                'structure': self.structure_analyzer.analyze_market_structure(data),
                'liquidity': self.liquidity_analyzer.analyze_liquidity(data),
                'support_resistance': self.sr_analyzer.analyze_support_resistance(data),
                'current_price': data['close'].iloc[-1],
                'data_quality': {
                    'candle_count': len(data),
                    'date_range': {
                        'start': str(data.index[0]) if hasattr(data.index, 'to_pydatetime') else 0,
                        'end': str(data.index[-1]) if hasattr(data.index, 'to_pydatetime') else len(data)-1
                    }
                }
            }
            
            timeframe_analyses[timeframe] = analysis
        
        return timeframe_analyses
    
    def _determine_market_context(self, timeframe_analyses: Dict, 
                                tf_hierarchy: Dict) -> Dict:
        """Determine overall market context from higher timeframes."""
        
        # Start with highest priority timeframe
        overall_bias = None
        trend_strength = 0
        context_sources = []
        
        for timeframe in TIMEFRAMES_ORDERED:
            if timeframe not in timeframe_analyses:
                continue
            
            analysis = timeframe_analyses[timeframe]
            structure = analysis['structure']
            
            current_trend = structure.get('current_trend')
            if current_trend and current_trend != 'sideways':
                if overall_bias is None:  # First valid trend sets overall bias
                    overall_bias = current_trend
                    trend_strength = structure.get('trend_strength', 0)
                    context_sources.append({
                        'timeframe': timeframe,
                        'trend': current_trend,
                        'strength': trend_strength,
                        'priority': analysis['priority']
                    })
                elif overall_bias == current_trend:
                    # Confirming trend adds to strength
                    trend_strength += structure.get('trend_strength', 0) * 0.5
                    context_sources.append({
                        'timeframe': timeframe,
                        'trend': current_trend,
                        'strength': structure.get('trend_strength', 0),
                        'priority': analysis['priority']
                    })
                # Conflicting trends are already captured in tf_hierarchy
        
        # Normalize trend strength
        trend_strength = min(trend_strength, 1.0)
        
        return {
            'overall_bias': overall_bias or 'sideways',
            'trend_strength': trend_strength,
            'context_sources': context_sources,
            'higher_tf_dominance': len([s for s in context_sources if s['priority'] >= 4]) > 0,
            'multi_tf_alignment': self._check_multi_tf_alignment(context_sources)
        }
    
    def _check_multi_tf_alignment(self, context_sources: List[Dict]) -> Dict:
        """Check alignment across multiple timeframes."""
        if len(context_sources) < 2:
            return {'aligned': False, 'alignment_score': 0.0}
        
        # Count trends
        bullish_count = sum(1 for s in context_sources if s['trend'] == 'bullish')
        bearish_count = sum(1 for s in context_sources if s['trend'] == 'bearish')
        total_count = len(context_sources)
        
        # Calculate alignment score
        if bullish_count > bearish_count:
            alignment_score = bullish_count / total_count
            dominant_trend = 'bullish'
        elif bearish_count > bullish_count:
            alignment_score = bearish_count / total_count
            dominant_trend = 'bearish'
        else:
            alignment_score = 0.5
            dominant_trend = 'mixed'
        
        return {
            'aligned': alignment_score >= 0.7,  # 70% agreement required
            'alignment_score': alignment_score,
            'dominant_trend': dominant_trend,
            'timeframe_count': total_count
        }
    
    def _identify_key_zones(self, timeframe_analyses: Dict) -> Dict:
        """Identify key zones across all timeframes."""
        key_zones = {
            'liquidity_zones': [],
            'structure_levels': [],
            'support_resistance': [],
            'confluence_areas': []
        }
        
        all_liquidity_zones = []
        all_structure_levels = []
        all_sr_levels = []
        
        # Collect zones from all timeframes
        for timeframe, analysis in timeframe_analyses.items():
            priority = analysis['priority']
            
            # Liquidity zones
            for zone in analysis['liquidity'].get('liquidity_zones', []):
                zone_with_context = {**zone, 'timeframe': timeframe, 'priority': priority}
                all_liquidity_zones.append(zone_with_context)
            
            # Structure levels
            structure_levels = analysis['structure'].get('structure_levels', {})
            for level_type in ['resistance_levels', 'support_levels']:
                for level in structure_levels.get(level_type, []):
                    level_with_context = {
                        **level, 
                        'timeframe': timeframe, 
                        'priority': priority,
                        'type': level_type[:-7]  # Remove '_levels' suffix
                    }
                    all_structure_levels.append(level_with_context)
            
            # Support/Resistance levels
            for level_type in ['support_levels', 'resistance_levels']:
                for level in analysis['support_resistance'].get(level_type, []):
                    level_with_context = {
                        **level, 
                        'timeframe': timeframe, 
                        'priority': priority
                    }
                    all_sr_levels.append(level_with_context)
        
        # Sort by priority (higher timeframes first)
        key_zones['liquidity_zones'] = sorted(all_liquidity_zones, 
                                            key=lambda x: x['priority'], reverse=True)[:10]
        key_zones['structure_levels'] = sorted(all_structure_levels, 
                                             key=lambda x: x['priority'], reverse=True)[:10]
        key_zones['support_resistance'] = sorted(all_sr_levels, 
                                                key=lambda x: (x['priority'], x.get('strength', 0)), 
                                                reverse=True)[:10]
        
        # Find confluence areas (levels that appear in multiple timeframes)
        key_zones['confluence_areas'] = self._find_confluence_areas(
            all_structure_levels + all_sr_levels
        )
        
        return key_zones
    
    def _find_confluence_areas(self, all_levels: List[Dict]) -> List[Dict]:
        """Find areas where levels from multiple timeframes converge."""
        confluence_areas = []
        tolerance = 0.01  # 1% tolerance
        
        processed_levels = []
        
        for i, level1 in enumerate(all_levels):
            if i in processed_levels:
                continue
            
            confluent_levels = [level1]
            processed_levels.append(i)
            
            for j, level2 in enumerate(all_levels[i+1:], i+1):
                if j in processed_levels:
                    continue
                
                price1 = level1.get('price', 0)
                price2 = level2.get('price', 0)
                
                if price1 > 0 and abs(price1 - price2) / price1 < tolerance:
                    confluent_levels.append(level2)
                    processed_levels.append(j)
            
            if len(confluent_levels) > 1:
                # Calculate confluence strength
                total_priority = sum(l['priority'] for l in confluent_levels)
                avg_price = sum(l.get('price', 0) for l in confluent_levels) / len(confluent_levels)
                
                confluence_areas.append({
                    'price': avg_price,
                    'level_count': len(confluent_levels),
                    'total_priority': total_priority,
                    'timeframes': list(set(l['timeframe'] for l in confluent_levels)),
                    'levels': confluent_levels
                })
        
        # Sort by significance (priority and level count)
        confluence_areas.sort(key=lambda x: (x['total_priority'], x['level_count']), reverse=True)
        return confluence_areas[:5]  # Top 5 confluence areas
    
    def _assess_overall_liquidity(self, timeframe_analyses: Dict) -> Dict:
        """Assess overall liquidity conditions across timeframes."""
        liquidity_states = []
        sweep_counts = []
        imbalances = []
        
        for timeframe, analysis in timeframe_analyses.items():
            liquidity = analysis['liquidity']
            
            liquidity_states.append(liquidity.get('current_liquidity_state', 'unknown'))
            sweep_counts.append(len(liquidity.get('liquidity_sweeps', [])))
            
            imbalance = liquidity.get('liquidity_imbalance', {})
            if imbalance.get('direction') != 'neutral':
                imbalances.append({
                    'timeframe': timeframe,
                    'direction': imbalance.get('direction'),
                    'strength': abs(imbalance.get('imbalance', 0)),
                    'priority': analysis['priority']
                })
        
        # Determine dominant liquidity state
        state_counts = {}
        for state in liquidity_states:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        dominant_state = max(state_counts.items(), key=lambda x: x[1])[0] if state_counts else 'unknown'
        
        # Assess liquidity bias from imbalances
        liquidity_bias = 'neutral'
        if imbalances:
            # Weight by timeframe priority
            weighted_bullish = sum(i['strength'] * i['priority'] for i in imbalances if i['direction'] == 'bullish')
            weighted_bearish = sum(i['strength'] * i['priority'] for i in imbalances if i['direction'] == 'bearish')
            
            if weighted_bullish > weighted_bearish * 1.2:
                liquidity_bias = 'bullish'
            elif weighted_bearish > weighted_bullish * 1.2:
                liquidity_bias = 'bearish'
        
        return {
            'dominant_state': dominant_state,
            'liquidity_bias': liquidity_bias,
            'total_sweeps': sum(sweep_counts),
            'imbalance_count': len(imbalances),
            'high_activity': sum(sweep_counts) > len(timeframe_analyses) * 2,
            'imbalances_by_tf': imbalances
        }
    
    def _generate_trading_recommendation(self, market_context: Dict, 
                                       tf_hierarchy: Dict, key_zones: Dict) -> Dict:
        """Generate overall trading recommendation."""
        
        overall_bias = market_context.get('overall_bias')
        trend_strength = market_context.get('trend_strength', 0)
        alignment = market_context.get('multi_tf_alignment', {})
        conflicts = len(tf_hierarchy.get('conflicting_signals', []))
        
        # Determine recommendation
        if overall_bias == 'sideways' or trend_strength < 0.3:
            recommendation = 'NO_ACTION'
            reason = 'Market showing sideways movement with low trend strength'
            confidence = 0.2
        
        elif conflicts > 2:
            recommendation = 'WAIT'
            reason = f'Multiple timeframe conflicts detected ({conflicts} conflicts)'
            confidence = 0.3
        
        elif not alignment.get('aligned', False):
            recommendation = 'WAIT'
            reason = f'Low multi-timeframe alignment ({alignment.get("alignment_score", 0):.1%})'
            confidence = 0.4
        
        elif overall_bias in ['bullish', 'bearish'] and alignment.get('aligned', False):
            recommendation = f'LOOK_FOR_{overall_bias.upper()}_ENTRIES'
            reason = f'Strong {overall_bias} bias with {alignment.get("alignment_score", 0):.1%} TF alignment'
            confidence = min(0.8, trend_strength + alignment.get('alignment_score', 0))
        
        else:
            recommendation = 'MONITOR'
            reason = 'Market conditions require monitoring'
            confidence = 0.5
        
        return {
            'recommendation': recommendation,
            'reason': reason,
            'confidence': confidence,
            'bias_direction': overall_bias,
            'trend_strength': trend_strength,
            'timeframe_alignment': alignment.get('alignment_score', 0),
            'conflict_count': conflicts
        }
    
    def _enhance_signals_with_context(self, signal_analysis: Dict, 
                                    target_timeframe: str) -> Dict:
        """Enhance signals with additional bot context."""
        
        # Add market context to signals
        market_context = self.last_analysis.get('market_context', {})
        enhanced_analysis = {**signal_analysis}
        
        # Add context to each signal
        for signal in enhanced_analysis.get('signals', []):
            signal['market_context'] = {
                'overall_bias': market_context.get('overall_bias'),
                'trend_strength': market_context.get('trend_strength'),
                'higher_tf_dominance': market_context.get('higher_tf_dominance'),
                'bot_recommendation': self.get_trading_recommendation()
            }
            
            # Add unique signal ID
            signal['signal_id'] = f"{target_timeframe}_{signal['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return enhanced_analysis
    
    def _update_active_signals(self, signal_analysis: Dict):
        """Update the list of active signals."""
        new_signals = signal_analysis.get('signals', [])
        
        # Add new signals to active list
        for signal in new_signals:
            if signal not in self.active_signals:
                self.active_signals.append({
                    **signal,
                    'created_at': datetime.now(),
                    'status': 'active'
                })
        
        # Keep only recent signals (last 100)
        if len(self.active_signals) > 100:
            self.active_signals = self.active_signals[-100:]
    
    def _analysis_is_stale(self, max_age_minutes: int = 30) -> bool:
        """Check if the last analysis is too old."""
        if not self.last_analysis:
            return True
        
        last_time = self.last_analysis.get('timestamp')
        if not last_time:
            return True
        
        age = (datetime.now() - last_time).total_seconds() / 60
        return age > max_age_minutes
    
    def _empty_analysis(self, reason: str) -> Dict:
        """Return empty analysis structure with reason."""
        return {
            'timestamp': datetime.now(),
            'error': reason,
            'timeframe_hierarchy': {},
            'market_context': {},
            'timeframe_analyses': {},
            'key_zones': {},
            'liquidity_assessment': {},
            'trading_recommendation': {
                'recommendation': 'NO_ACTION',
                'reason': reason,
                'confidence': 0.0
            }
        }
    
    def export_analysis(self, filename: Optional[str] = None) -> str:
        """Export the last analysis to JSON file."""
        if not self.last_analysis:
            raise ValueError("No analysis available to export")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"market_analysis_{timestamp}.json"
        
        # Convert datetime objects to strings for JSON serialization
        exportable_analysis = self._prepare_for_json_export(self.last_analysis)
        
        with open(filename, 'w') as f:
            json.dump(exportable_analysis, f, indent=2, default=str)
        
        return filename
    
    def _prepare_for_json_export(self, analysis: Dict) -> Dict:
        """Prepare analysis for JSON export by converting non-serializable objects."""
        if isinstance(analysis, dict):
            return {k: self._prepare_for_json_export(v) for k, v in analysis.items()}
        elif isinstance(analysis, list):
            return [self._prepare_for_json_export(item) for item in analysis]
        elif isinstance(analysis, (datetime, pd.Timestamp)):
            return str(analysis)
        else:
            return analysis