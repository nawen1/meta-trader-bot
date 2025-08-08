//+------------------------------------------------------------------+
//|                                          TimeframeAnalysis.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

#include "Utils.mqh"

//+------------------------------------------------------------------+
//| Timeframe Analysis class                                        |
//+------------------------------------------------------------------+
class CTimeframeAnalysis
{
private:
    ENUM_TIMEFRAMES m_contextTF1;    // Primary context timeframe (H4)
    ENUM_TIMEFRAMES m_contextTF2;    // Secondary context timeframe (D1)
    ENUM_TIMEFRAMES m_entryTF1;      // Primary entry timeframe (M1)
    ENUM_TIMEFRAMES m_entryTF2;      // Secondary entry timeframe (M5)
    
    //--- Moving average periods for trend analysis
    int m_fastMA;
    int m_slowMA;
    int m_trendMA;
    
    CUtils* m_utils;
    
public:
    //--- Constructor/Destructor
    CTimeframeAnalysis();
    ~CTimeframeAnalysis() {}
    
    //--- Initialization
    bool Init(ENUM_TIMEFRAMES contextTF1, ENUM_TIMEFRAMES contextTF2, ENUM_TIMEFRAMES entryTF1, ENUM_TIMEFRAMES entryTF2);
    
    //--- Analysis methods
    SMarketContext AnalyzeContext();
    SEntrySignal AnalyzeEntry();
    
    //--- Context analysis helpers
    ENUM_TREND_DIRECTION GetTrendDirection(ENUM_TIMEFRAMES timeframe);
    double GetTrendStrength(ENUM_TIMEFRAMES timeframe);
    double GetVolatility(ENUM_TIMEFRAMES timeframe);
    
    //--- Entry analysis helpers
    bool CheckBullishEntry(ENUM_TIMEFRAMES timeframe);
    bool CheckBearishEntry(ENUM_TIMEFRAMES timeframe);
    bool ValidateMultiTimeframeAlignment();
    
    //--- Support and resistance
    double FindNearestSupport(ENUM_TIMEFRAMES timeframe);
    double FindNearestResistance(ENUM_TIMEFRAMES timeframe);
    
    //--- Utility methods
    void SetUtils(CUtils* utils) { m_utils = utils; }
    string GetAnalysisReport();
};

//+------------------------------------------------------------------+
//| Constructor                                                     |
//+------------------------------------------------------------------+
CTimeframeAnalysis::CTimeframeAnalysis()
{
    m_contextTF1 = PERIOD_H4;
    m_contextTF2 = PERIOD_D1;
    m_entryTF1 = PERIOD_M1;
    m_entryTF2 = PERIOD_M5;
    
    m_fastMA = 21;
    m_slowMA = 50;
    m_trendMA = 200;
    
    m_utils = NULL;
}

//+------------------------------------------------------------------+
//| Initialize timeframe analysis                                   |
//+------------------------------------------------------------------+
bool CTimeframeAnalysis::Init(ENUM_TIMEFRAMES contextTF1, ENUM_TIMEFRAMES contextTF2, ENUM_TIMEFRAMES entryTF1, ENUM_TIMEFRAMES entryTF2)
{
    m_contextTF1 = contextTF1;
    m_contextTF2 = contextTF2;
    m_entryTF1 = entryTF1;
    m_entryTF2 = entryTF2;
    
    Print("Timeframe Analysis initialized - Context: ", EnumToString(m_contextTF1), "/", EnumToString(m_contextTF2), 
          " Entry: ", EnumToString(m_entryTF1), "/", EnumToString(m_entryTF2));
    
    return true;
}

//+------------------------------------------------------------------+
//| Analyze market context on higher timeframes                    |
//+------------------------------------------------------------------+
SMarketContext CTimeframeAnalysis::AnalyzeContext()
{
    SMarketContext context = {};
    
    //--- Analyze primary context timeframe
    ENUM_TREND_DIRECTION trend1 = GetTrendDirection(m_contextTF1);
    double strength1 = GetTrendStrength(m_contextTF1);
    
    //--- Analyze secondary context timeframe
    ENUM_TREND_DIRECTION trend2 = GetTrendDirection(m_contextTF2);
    double strength2 = GetTrendStrength(m_contextTF2);
    
    //--- Determine overall context
    if(trend1 == trend2 && trend1 != TREND_UNDEFINED)
    {
        context.trend = trend1;
        context.strength = (strength1 + strength2) / 2.0;
    }
    else if(trend1 != TREND_UNDEFINED)
    {
        context.trend = trend1;
        context.strength = strength1 * 0.7; // Reduced strength due to divergence
    }
    else if(trend2 != TREND_UNDEFINED)
    {
        context.trend = trend2;
        context.strength = strength2 * 0.5; // Significantly reduced strength
    }
    else
    {
        context.trend = TREND_UNDEFINED;
        context.strength = 0;
    }
    
    //--- Calculate volatility
    context.volatility = (GetVolatility(m_contextTF1) + GetVolatility(m_contextTF2)) / 2.0;
    
    //--- Validate context
    context.isValid = (context.trend != TREND_UNDEFINED && context.strength >= 0.3);
    
    return context;
}

//+------------------------------------------------------------------+
//| Analyze entry signals on lower timeframes                      |
//+------------------------------------------------------------------+
SEntrySignal CTimeframeAnalysis::AnalyzeEntry()
{
    SEntrySignal signal = {};
    signal.timestamp = TimeCurrent();
    
    //--- First check if context allows trading
    SMarketContext context = AnalyzeContext();
    if(!context.isValid)
        return signal;
    
    //--- Check for bullish entries
    if(context.trend == TREND_BULLISH)
    {
        if(CheckBullishEntry(m_entryTF1) || CheckBullishEntry(m_entryTF2))
        {
            signal.direction = SIGNAL_BUY;
            signal.entryPrice = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
        }
    }
    //--- Check for bearish entries
    else if(context.trend == TREND_BEARISH)
    {
        if(CheckBearishEntry(m_entryTF1) || CheckBearishEntry(m_entryTF2))
        {
            signal.direction = SIGNAL_SELL;
            signal.entryPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
        }
    }
    
    //--- If signal found, calculate levels
    if(signal.direction != SIGNAL_NONE && m_utils != NULL)
    {
        //--- Calculate stop loss
        signal.stopLoss = m_utils.CalculateStopLoss(signal.direction, signal.entryPrice, 2.0);
        
        //--- Calculate take profits
        signal.takeProfit1 = m_utils.CalculateTakeProfit(signal.direction, signal.entryPrice, signal.stopLoss, 1.0);
        signal.takeProfit2 = m_utils.CalculateTakeProfit(signal.direction, signal.entryPrice, signal.stopLoss, 2.0);
        signal.takeProfit3 = m_utils.CalculateTakeProfit(signal.direction, signal.entryPrice, signal.stopLoss, 3.0);
        
        signal.model = "MTF_ANALYSIS";
        signal.timeframe = m_entryTF1;
        signal.isValid = true;
    }
    
    return signal;
}

//+------------------------------------------------------------------+
//| Get trend direction for specified timeframe                    |
//+------------------------------------------------------------------+
ENUM_TREND_DIRECTION CTimeframeAnalysis::GetTrendDirection(ENUM_TIMEFRAMES timeframe)
{
    //--- Get moving averages
    double fastMA[], slowMA[], trendMA[];
    
    int fastHandle = iMA(Symbol(), timeframe, m_fastMA, 0, MODE_EMA, PRICE_CLOSE);
    int slowHandle = iMA(Symbol(), timeframe, m_slowMA, 0, MODE_EMA, PRICE_CLOSE);
    int trendHandle = iMA(Symbol(), timeframe, m_trendMA, 0, MODE_SMA, PRICE_CLOSE);
    
    if(fastHandle == INVALID_HANDLE || slowHandle == INVALID_HANDLE || trendHandle == INVALID_HANDLE)
        return TREND_UNDEFINED;
    
    if(CopyBuffer(fastHandle, 0, 0, 3, fastMA) != 3 ||
       CopyBuffer(slowHandle, 0, 0, 3, slowMA) != 3 ||
       CopyBuffer(trendHandle, 0, 0, 3, trendMA) != 3)
    {
        IndicatorRelease(fastHandle);
        IndicatorRelease(slowHandle);
        IndicatorRelease(trendHandle);
        return TREND_UNDEFINED;
    }
    
    IndicatorRelease(fastHandle);
    IndicatorRelease(slowHandle);
    IndicatorRelease(trendHandle);
    
    //--- Determine trend direction
    bool fastAboveSlow = fastMA[0] > slowMA[0];
    bool priceAboveTrend = SymbolInfoDouble(Symbol(), SYMBOL_BID) > trendMA[0];
    bool trendRising = trendMA[0] > trendMA[2];
    
    if(fastAboveSlow && priceAboveTrend && trendRising)
        return TREND_BULLISH;
    else if(!fastAboveSlow && !priceAboveTrend && !trendRising)
        return TREND_BEARISH;
    
    return TREND_UNDEFINED;
}

//+------------------------------------------------------------------+
//| Get trend strength (0.0 to 1.0)                               |
//+------------------------------------------------------------------+
double CTimeframeAnalysis::GetTrendStrength(ENUM_TIMEFRAMES timeframe)
{
    //--- Calculate based on MA separation and slope
    double fastMA[], slowMA[];
    
    int fastHandle = iMA(Symbol(), timeframe, m_fastMA, 0, MODE_EMA, PRICE_CLOSE);
    int slowHandle = iMA(Symbol(), timeframe, m_slowMA, 0, MODE_EMA, PRICE_CLOSE);
    
    if(fastHandle == INVALID_HANDLE || slowHandle == INVALID_HANDLE)
        return 0;
    
    if(CopyBuffer(fastHandle, 0, 0, 5, fastMA) != 5 ||
       CopyBuffer(slowHandle, 0, 0, 5, slowMA) != 5)
    {
        IndicatorRelease(fastHandle);
        IndicatorRelease(slowHandle);
        return 0;
    }
    
    IndicatorRelease(fastHandle);
    IndicatorRelease(slowHandle);
    
    //--- Calculate separation strength
    double currentSeparation = MathAbs(fastMA[0] - slowMA[0]);
    double averageSeparation = 0;
    for(int i = 0; i < 5; i++)
        averageSeparation += MathAbs(fastMA[i] - slowMA[i]);
    averageSeparation /= 5.0;
    
    //--- Calculate slope strength
    double fastSlope = (fastMA[0] - fastMA[4]) / 4.0;
    double slowSlope = (slowMA[0] - slowMA[4]) / 4.0;
    double combinedSlope = (fastSlope + slowSlope) / 2.0;
    
    //--- Normalize to 0-1 range
    double separationStrength = MathMin(currentSeparation / (averageSeparation * 2.0), 1.0);
    double slopeStrength = MathMin(MathAbs(combinedSlope) / (SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 100), 1.0);
    
    return (separationStrength + slopeStrength) / 2.0;
}

//+------------------------------------------------------------------+
//| Get volatility for specified timeframe                         |
//+------------------------------------------------------------------+
double CTimeframeAnalysis::GetVolatility(ENUM_TIMEFRAMES timeframe)
{
    if(m_utils == NULL)
        return 0;
    
    return m_utils.GetATR(14, timeframe);
}

//+------------------------------------------------------------------+
//| Check for bullish entry conditions                             |
//+------------------------------------------------------------------+
bool CTimeframeAnalysis::CheckBullishEntry(ENUM_TIMEFRAMES timeframe)
{
    //--- Get current and previous candles
    double open[], high[], low[], close[];
    
    if(CopyOpen(Symbol(), timeframe, 0, 3, open) != 3 ||
       CopyHigh(Symbol(), timeframe, 0, 3, high) != 3 ||
       CopyLow(Symbol(), timeframe, 0, 3, low) != 3 ||
       CopyClose(Symbol(), timeframe, 0, 3, close) != 3)
        return false;
    
    //--- Check for bullish patterns
    bool bullishCandle = close[1] > open[1]; // Previous candle is bullish
    bool higherLow = low[1] > low[2]; // Higher low formation
    bool breakingResistance = close[1] > high[2]; // Breaking previous high
    
    //--- Check momentum
    double fastMA[], slowMA[];
    int fastHandle = iMA(Symbol(), timeframe, 8, 0, MODE_EMA, PRICE_CLOSE);
    int slowHandle = iMA(Symbol(), timeframe, 21, 0, MODE_EMA, PRICE_CLOSE);
    
    bool momentumBullish = false;
    if(fastHandle != INVALID_HANDLE && slowHandle != INVALID_HANDLE)
    {
        if(CopyBuffer(fastHandle, 0, 0, 2, fastMA) == 2 &&
           CopyBuffer(slowHandle, 0, 0, 2, slowMA) == 2)
        {
            momentumBullish = (fastMA[0] > slowMA[0] && fastMA[0] > fastMA[1]);
        }
        IndicatorRelease(fastHandle);
        IndicatorRelease(slowHandle);
    }
    
    return (bullishCandle && (higherLow || breakingResistance) && momentumBullish);
}

//+------------------------------------------------------------------+
//| Check for bearish entry conditions                             |
//+------------------------------------------------------------------+
bool CTimeframeAnalysis::CheckBearishEntry(ENUM_TIMEFRAMES timeframe)
{
    //--- Get current and previous candles
    double open[], high[], low[], close[];
    
    if(CopyOpen(Symbol(), timeframe, 0, 3, open) != 3 ||
       CopyHigh(Symbol(), timeframe, 0, 3, high) != 3 ||
       CopyLow(Symbol(), timeframe, 0, 3, low) != 3 ||
       CopyClose(Symbol(), timeframe, 0, 3, close) != 3)
        return false;
    
    //--- Check for bearish patterns
    bool bearishCandle = close[1] < open[1]; // Previous candle is bearish
    bool lowerHigh = high[1] < high[2]; // Lower high formation
    bool breakingSupport = close[1] < low[2]; // Breaking previous low
    
    //--- Check momentum
    double fastMA[], slowMA[];
    int fastHandle = iMA(Symbol(), timeframe, 8, 0, MODE_EMA, PRICE_CLOSE);
    int slowHandle = iMA(Symbol(), timeframe, 21, 0, MODE_EMA, PRICE_CLOSE);
    
    bool momentumBearish = false;
    if(fastHandle != INVALID_HANDLE && slowHandle != INVALID_HANDLE)
    {
        if(CopyBuffer(fastHandle, 0, 0, 2, fastMA) == 2 &&
           CopyBuffer(slowHandle, 0, 0, 2, slowMA) == 2)
        {
            momentumBearish = (fastMA[0] < slowMA[0] && fastMA[0] < fastMA[1]);
        }
        IndicatorRelease(fastHandle);
        IndicatorRelease(slowHandle);
    }
    
    return (bearishCandle && (lowerHigh || breakingSupport) && momentumBearish);
}

//+------------------------------------------------------------------+
//| Validate multi-timeframe alignment                             |
//+------------------------------------------------------------------+
bool CTimeframeAnalysis::ValidateMultiTimeframeAlignment()
{
    ENUM_TREND_DIRECTION contextTrend = GetTrendDirection(m_contextTF1);
    ENUM_TREND_DIRECTION entryTrend1 = GetTrendDirection(m_entryTF1);
    ENUM_TREND_DIRECTION entryTrend2 = GetTrendDirection(m_entryTF2);
    
    //--- Check for alignment (at least 2 out of 3 should agree)
    int bullishCount = 0;
    int bearishCount = 0;
    
    if(contextTrend == TREND_BULLISH) bullishCount++;
    else if(contextTrend == TREND_BEARISH) bearishCount++;
    
    if(entryTrend1 == TREND_BULLISH) bullishCount++;
    else if(entryTrend1 == TREND_BEARISH) bearishCount++;
    
    if(entryTrend2 == TREND_BULLISH) bullishCount++;
    else if(entryTrend2 == TREND_BEARISH) bearishCount++;
    
    return (bullishCount >= 2 || bearishCount >= 2);
}

//+------------------------------------------------------------------+
//| Find nearest support level                                     |
//+------------------------------------------------------------------+
double CTimeframeAnalysis::FindNearestSupport(ENUM_TIMEFRAMES timeframe)
{
    double low[];
    if(CopyLow(Symbol(), timeframe, 0, 50, low) != 50)
        return 0;
    
    double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
    double nearestSupport = 0;
    
    //--- Find the highest low below current price
    for(int i = 0; i < 50; i++)
    {
        if(low[i] < currentPrice && low[i] > nearestSupport)
            nearestSupport = low[i];
    }
    
    return nearestSupport;
}

//+------------------------------------------------------------------+
//| Find nearest resistance level                                  |
//+------------------------------------------------------------------+
double CTimeframeAnalysis::FindNearestResistance(ENUM_TIMEFRAMES timeframe)
{
    double high[];
    if(CopyHigh(Symbol(), timeframe, 0, 50, high) != 50)
        return 0;
    
    double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
    double nearestResistance = 999999;
    
    //--- Find the lowest high above current price
    for(int i = 0; i < 50; i++)
    {
        if(high[i] > currentPrice && high[i] < nearestResistance)
            nearestResistance = high[i];
    }
    
    return (nearestResistance < 999999) ? nearestResistance : 0;
}

//+------------------------------------------------------------------+
//| Generate analysis report                                       |
//+------------------------------------------------------------------+
string CTimeframeAnalysis::GetAnalysisReport()
{
    SMarketContext context = AnalyzeContext();
    
    string report = "\n=== TIMEFRAME ANALYSIS REPORT ===\n";
    report += "Context TF1 (" + EnumToString(m_contextTF1) + "): " + EnumToString(GetTrendDirection(m_contextTF1)) + "\n";
    report += "Context TF2 (" + EnumToString(m_contextTF2) + "): " + EnumToString(GetTrendDirection(m_contextTF2)) + "\n";
    report += "Entry TF1 (" + EnumToString(m_entryTF1) + "): " + EnumToString(GetTrendDirection(m_entryTF1)) + "\n";
    report += "Entry TF2 (" + EnumToString(m_entryTF2) + "): " + EnumToString(GetTrendDirection(m_entryTF2)) + "\n";
    report += "Overall Trend: " + EnumToString(context.trend) + "\n";
    report += "Trend Strength: " + DoubleToString(context.strength * 100, 1) + "%\n";
    report += "Volatility: " + DoubleToString(context.volatility, 5) + "\n";
    report += "Multi-TF Alignment: " + (ValidateMultiTimeframeAlignment() ? "YES" : "NO") + "\n";
    report += "===============================\n";
    
    return report;
}