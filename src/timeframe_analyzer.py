"""
Multi-timeframe analyzer module.
Implements the core logic for prioritizing higher timeframes over lower ones.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from config import TIMEFRAMES_ORDERED, TIMEFRAME_PRIORITY


class TimeframeAnalyzer:
    """
    Manages multi-timeframe analysis with priority-based approach.
    Higher timeframes always take precedence over lower ones.
    """
    
    def __init__(self):
        self.timeframes = TIMEFRAMES_ORDERED
        self.priority_map = TIMEFRAME_PRIORITY
        self.analysis_cache = {}
    
    def get_ordered_timeframes(self) -> List[str]:
        """Returns timeframes ordered from highest to lowest priority."""
        return self.timeframes.copy()
    
    def get_timeframe_priority(self, timeframe: str) -> int:
        """Returns the priority level of a given timeframe."""
        return self.priority_map.get(timeframe, 0)
    
    def is_higher_timeframe(self, tf1: str, tf2: str) -> bool:
        """Check if tf1 has higher priority than tf2."""
        return self.get_timeframe_priority(tf1) > self.get_timeframe_priority(tf2)
    
    def get_higher_timeframes(self, current_tf: str) -> List[str]:
        """Get all timeframes with higher priority than current_tf."""
        current_priority = self.get_timeframe_priority(current_tf)
        return [tf for tf in self.timeframes 
                if self.get_timeframe_priority(tf) > current_priority]
    
    def get_lower_timeframes(self, current_tf: str) -> List[str]:
        """Get all timeframes with lower priority than current_tf."""
        current_priority = self.get_timeframe_priority(current_tf)
        return [tf for tf in self.timeframes 
                if self.get_timeframe_priority(tf) < current_priority]
    
    def analyze_timeframe_hierarchy(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Analyze market conditions starting from highest timeframe and working down.
        
        Args:
            data: Dictionary with timeframe as key and OHLCV data as value
            
        Returns:
            Dictionary with hierarchical analysis results
        """
        analysis_results = {
            'timeframe_context': {},
            'higher_tf_bias': None,
            'entry_timeframes': [],
            'conflicting_signals': []
        }
        
        # Start analysis from highest timeframe
        for timeframe in self.timeframes:
            if timeframe not in data:
                continue
                
            tf_data = data[timeframe]
            if tf_data.empty:
                continue
            
            # Analyze this timeframe
            tf_analysis = self._analyze_single_timeframe(tf_data, timeframe)
            analysis_results['timeframe_context'][timeframe] = tf_analysis
            
            # Set higher timeframe bias if not already set
            if analysis_results['higher_tf_bias'] is None and tf_analysis.get('trend'):
                analysis_results['higher_tf_bias'] = tf_analysis['trend']
        
        # Determine valid entry timeframes based on higher TF alignment
        analysis_results['entry_timeframes'] = self._get_aligned_entry_timeframes(
            analysis_results['timeframe_context']
        )
        
        # Identify conflicting signals
        analysis_results['conflicting_signals'] = self._detect_signal_conflicts(
            analysis_results['timeframe_context']
        )
        
        return analysis_results
    
    def _analyze_single_timeframe(self, data: pd.DataFrame, timeframe: str) -> Dict:
        """
        Analyze a single timeframe for basic market structure.
        This is a simplified version - would be enhanced with actual technical analysis.
        """
        if data.empty or len(data) < 2:
            return {'trend': None, 'strength': 0}
        
        # Simple trend analysis based on price movement
        recent_close = data['close'].iloc[-1]
        older_close = data['close'].iloc[-min(10, len(data))]
        
        trend = 'bullish' if recent_close > older_close else 'bearish'
        strength = abs((recent_close - older_close) / older_close) * 100
        
        return {
            'trend': trend,
            'strength': strength,
            'timeframe': timeframe,
            'priority': self.get_timeframe_priority(timeframe)
        }
    
    def _get_aligned_entry_timeframes(self, tf_context: Dict) -> List[str]:
        """
        Determine which timeframes are aligned with higher timeframe bias.
        """
        if not tf_context:
            return []
        
        # Get the highest timeframe trend as reference
        highest_tf_trend = None
        for tf in self.timeframes:
            if tf in tf_context and tf_context[tf].get('trend'):
                highest_tf_trend = tf_context[tf]['trend']
                break
        
        if not highest_tf_trend:
            return []
        
        # Find aligned timeframes
        aligned_tfs = []
        for tf in self.timeframes:
            if tf in tf_context:
                tf_trend = tf_context[tf].get('trend')
                if tf_trend == highest_tf_trend:
                    aligned_tfs.append(tf)
        
        return aligned_tfs
    
    def _detect_signal_conflicts(self, tf_context: Dict) -> List[Dict]:
        """
        Detect conflicts between timeframe signals.
        """
        conflicts = []
        
        for i, tf1 in enumerate(self.timeframes):
            if tf1 not in tf_context:
                continue
                
            for tf2 in self.timeframes[i+1:]:
                if tf2 not in tf_context:
                    continue
                
                trend1 = tf_context[tf1].get('trend')
                trend2 = tf_context[tf2].get('trend')
                
                if trend1 and trend2 and trend1 != trend2:
                    conflicts.append({
                        'higher_tf': tf1,
                        'lower_tf': tf2,
                        'higher_trend': trend1,
                        'lower_trend': trend2,
                        'priority_difference': self.get_timeframe_priority(tf1) - self.get_timeframe_priority(tf2)
                    })
        
        return conflicts
    
    def should_allow_entry(self, entry_tf: str, tf_analysis: Dict) -> Tuple[bool, str]:
        """
        Determine if entry should be allowed based on timeframe hierarchy.
        
        Args:
            entry_tf: Timeframe where entry signal is generated
            tf_analysis: Complete timeframe analysis results
            
        Returns:
            Tuple of (allow_entry: bool, reason: str)
        """
        higher_tfs = self.get_higher_timeframes(entry_tf)
        
        # Check if higher timeframes provide context
        higher_tf_context = tf_analysis.get('timeframe_context', {})
        
        # Must have at least one higher timeframe analysis
        has_higher_tf_data = any(tf in higher_tf_context for tf in higher_tfs)
        if not has_higher_tf_data:
            return False, "No higher timeframe context available"
        
        # Check alignment with higher timeframe bias
        higher_tf_bias = tf_analysis.get('higher_tf_bias')
        entry_tf_trend = higher_tf_context.get(entry_tf, {}).get('trend')
        
        if higher_tf_bias and entry_tf_trend:
            if higher_tf_bias != entry_tf_trend:
                return False, f"Entry TF trend ({entry_tf_trend}) conflicts with higher TF bias ({higher_tf_bias})"
        
        # Check for critical conflicts
        conflicts = tf_analysis.get('conflicting_signals', [])
        critical_conflicts = [c for c in conflicts if c['priority_difference'] >= 2]
        
        if critical_conflicts:
            return False, f"Critical timeframe conflicts detected: {len(critical_conflicts)} conflicts"
        
        return True, "Entry aligned with higher timeframe context"