//+------------------------------------------------------------------+
//|                                                    Utils.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

//--- Enumerations
enum ENUM_SIGNAL_DIRECTION
{
    SIGNAL_NONE = 0,
    SIGNAL_BUY = 1,
    SIGNAL_SELL = -1
};

enum ENUM_TREND_DIRECTION
{
    TREND_UNDEFINED = 0,
    TREND_BULLISH = 1,
    TREND_BEARISH = -1
};

//--- Structures
struct SMarketContext
{
    ENUM_TREND_DIRECTION trend;
    double strength;
    double volatility;
    bool isValid;
};

struct SEntrySignal
{
    bool isValid;
    ENUM_SIGNAL_DIRECTION direction;
    double entryPrice;
    double stopLoss;
    double takeProfit1;
    double takeProfit2;
    double takeProfit3;
    string model;
    datetime timestamp;
    ENUM_TIMEFRAMES timeframe;
};

struct SPositionInfo
{
    ulong ticket;
    double entryPrice;
    double currentSL;
    double currentTP;
    double volume;
    ENUM_SIGNAL_DIRECTION direction;
    string model;
    datetime openTime;
    bool tp1Hit;
    bool tp2Hit;
    bool tp3Hit;
    double originalTP1;
    double originalTP2;
    double originalTP3;
};

//+------------------------------------------------------------------+
//| Utilities class for common functions                            |
//+------------------------------------------------------------------+
class CUtils
{
private:
    datetime m_lastBarTime;
    double   m_currentATR;
    bool     m_initialized;
    
public:
    //--- Constructor/Destructor
    CUtils() : m_lastBarTime(0), m_currentATR(0), m_initialized(false) {}
    ~CUtils() {}
    
    //--- Initialization
    bool Init();
    
    //--- Market data functions
    void UpdateMarketData();
    bool IsNewBar(ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT);
    bool IsMarketOpen();
    
    //--- Volatility functions
    double GetATR(int period = 14, ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT);
    bool IsVolatilityFavorable(double multiplier = 1.5);
    
    //--- Price calculation functions
    double CalculateDistance(double price1, double price2);
    double NormalizePrice(double price);
    double CalculateStopLoss(ENUM_SIGNAL_DIRECTION direction, double entry, double atrMultiplier = 2.0);
    double CalculateTakeProfit(ENUM_SIGNAL_DIRECTION direction, double entry, double sl, double ratio = 2.0);
    
    //--- Time functions
    bool IsWithinTradingHours();
    datetime GetBarTime(int shift = 0, ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT);
    
    //--- Validation functions
    bool IsValidPrice(double price);
    bool IsValidVolume(double volume);
    
    //--- Conversion functions
    string DirectionToString(ENUM_SIGNAL_DIRECTION direction);
    string TrendToString(ENUM_TREND_DIRECTION trend);
    string TimeframeToString(ENUM_TIMEFRAMES timeframe);
};

//+------------------------------------------------------------------+
//| Initialize utilities                                             |
//+------------------------------------------------------------------+
bool CUtils::Init()
{
    m_lastBarTime = 0;
    m_currentATR = 0;
    m_initialized = true;
    
    UpdateMarketData();
    
    Print("Utils module initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Update current market data                                      |
//+------------------------------------------------------------------+
void CUtils::UpdateMarketData()
{
    if(!m_initialized) return;
    
    //--- Update ATR
    m_currentATR = GetATR();
}

//+------------------------------------------------------------------+
//| Check if new bar formed                                         |
//+------------------------------------------------------------------+
bool CUtils::IsNewBar(ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT)
{
    datetime currentBarTime = GetBarTime(0, timeframe);
    
    if(timeframe == PERIOD_CURRENT)
    {
        if(currentBarTime != m_lastBarTime)
        {
            m_lastBarTime = currentBarTime;
            return true;
        }
    }
    else
    {
        static datetime lastBarTimes[];
        int tfIndex = (int)timeframe;
        
        if(ArraySize(lastBarTimes) <= tfIndex)
            ArrayResize(lastBarTimes, tfIndex + 1);
        
        if(currentBarTime != lastBarTimes[tfIndex])
        {
            lastBarTimes[tfIndex] = currentBarTime;
            return true;
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Check if market is open                                         |
//+------------------------------------------------------------------+
bool CUtils::IsMarketOpen()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    //--- Check if it's weekend
    if(dt.day_of_week == 0 || dt.day_of_week == 6)
        return false;
    
    //--- Check symbol trading session
    datetime from, to;
    if(!SymbolInfoSessionTrade(Symbol(), (ENUM_DAY_OF_WEEK)dt.day_of_week, 0, from, to))
        return false;
    
    uint currentTime = (uint)(dt.hour * 3600 + dt.min * 60 + dt.sec);
    uint fromTime = (uint)(from % 86400);
    uint toTime = (uint)(to % 86400);
    
    return (currentTime >= fromTime && currentTime <= toTime);
}

//+------------------------------------------------------------------+
//| Get Average True Range                                          |
//+------------------------------------------------------------------+
double CUtils::GetATR(int period = 14, ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT)
{
    double atr[];
    int handle = iATR(Symbol(), timeframe, period);
    
    if(handle == INVALID_HANDLE)
        return 0;
    
    if(CopyBuffer(handle, 0, 0, 1, atr) != 1)
        return 0;
    
    IndicatorRelease(handle);
    return atr[0];
}

//+------------------------------------------------------------------+
//| Check if volatility is favorable for trading                   |
//+------------------------------------------------------------------+
bool CUtils::IsVolatilityFavorable(double multiplier = 1.5)
{
    double currentATR = GetATR();
    double averageATR = GetATR(50); // Longer period for average
    
    if(currentATR <= 0 || averageATR <= 0)
        return false;
    
    //--- Current volatility should not be extremely high
    return (currentATR <= averageATR * multiplier);
}

//+------------------------------------------------------------------+
//| Calculate distance between two prices                          |
//+------------------------------------------------------------------+
double CUtils::CalculateDistance(double price1, double price2)
{
    return MathAbs(price1 - price2);
}

//+------------------------------------------------------------------+
//| Normalize price to symbol's tick size                          |
//+------------------------------------------------------------------+
double CUtils::NormalizePrice(double price)
{
    double tickSize = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_SIZE);
    if(tickSize > 0)
        return NormalizeDouble(MathRound(price / tickSize) * tickSize, (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS));
    
    return NormalizeDouble(price, (int)SymbolInfoInteger(Symbol(), SYMBOL_DIGITS));
}

//+------------------------------------------------------------------+
//| Calculate stop loss based on ATR                               |
//+------------------------------------------------------------------+
double CUtils::CalculateStopLoss(ENUM_SIGNAL_DIRECTION direction, double entry, double atrMultiplier = 2.0)
{
    double atr = GetATR();
    if(atr <= 0) return 0;
    
    double distance = atr * atrMultiplier;
    double sl;
    
    if(direction == SIGNAL_BUY)
        sl = entry - distance;
    else
        sl = entry + distance;
    
    return NormalizePrice(sl);
}

//+------------------------------------------------------------------+
//| Calculate take profit based on risk:reward ratio               |
//+------------------------------------------------------------------+
double CUtils::CalculateTakeProfit(ENUM_SIGNAL_DIRECTION direction, double entry, double sl, double ratio = 2.0)
{
    double distance = CalculateDistance(entry, sl) * ratio;
    double tp;
    
    if(direction == SIGNAL_BUY)
        tp = entry + distance;
    else
        tp = entry - distance;
    
    return NormalizePrice(tp);
}

//+------------------------------------------------------------------+
//| Check if within allowed trading hours                          |
//+------------------------------------------------------------------+
bool CUtils::IsWithinTradingHours()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    //--- Allow trading during main sessions (customize as needed)
    int hour = dt.hour;
    
    //--- London session: 08:00-17:00
    //--- New York session: 13:00-22:00
    //--- Combined: 08:00-22:00 GMT
    return (hour >= 8 && hour <= 22);
}

//+------------------------------------------------------------------+
//| Get bar time for specified shift and timeframe                 |
//+------------------------------------------------------------------+
datetime CUtils::GetBarTime(int shift = 0, ENUM_TIMEFRAMES timeframe = PERIOD_CURRENT)
{
    return iTime(Symbol(), timeframe, shift);
}

//+------------------------------------------------------------------+
//| Validate price value                                           |
//+------------------------------------------------------------------+
bool CUtils::IsValidPrice(double price)
{
    return (price > 0 && !MathIsInf(price) && !MathIsNaN(price));
}

//+------------------------------------------------------------------+
//| Validate volume value                                          |
//+------------------------------------------------------------------+
bool CUtils::IsValidVolume(double volume)
{
    double minVol = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
    double maxVol = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
    
    return (volume >= minVol && volume <= maxVol && volume > 0);
}

//+------------------------------------------------------------------+
//| Convert signal direction to string                             |
//+------------------------------------------------------------------+
string CUtils::DirectionToString(ENUM_SIGNAL_DIRECTION direction)
{
    switch(direction)
    {
        case SIGNAL_BUY: return "BUY";
        case SIGNAL_SELL: return "SELL";
        default: return "NONE";
    }
}

//+------------------------------------------------------------------+
//| Convert trend direction to string                              |
//+------------------------------------------------------------------+
string CUtils::TrendToString(ENUM_TREND_DIRECTION trend)
{
    switch(trend)
    {
        case TREND_BULLISH: return "BULLISH";
        case TREND_BEARISH: return "BEARISH";
        default: return "UNDEFINED";
    }
}

//+------------------------------------------------------------------+
//| Convert timeframe to string                                    |
//+------------------------------------------------------------------+
string CUtils::TimeframeToString(ENUM_TIMEFRAMES timeframe)
{
    switch(timeframe)
    {
        case PERIOD_M1: return "M1";
        case PERIOD_M5: return "M5";
        case PERIOD_M15: return "M15";
        case PERIOD_M30: return "M30";
        case PERIOD_H1: return "H1";
        case PERIOD_H4: return "H4";
        case PERIOD_D1: return "D1";
        case PERIOD_W1: return "W1";
        case PERIOD_MN1: return "MN1";
        default: return "UNKNOWN";
    }
}