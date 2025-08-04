//+------------------------------------------------------------------+
//|                                             TradingModels.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

#include "Utils.mqh"

//--- Fibonacci levels
const double FIB_LEVELS[] = {0.236, 0.382, 0.5, 0.618, 0.786, 1.0};

//--- Structures for trading models
struct SLiquidityLevel
{
    double price;
    datetime time;
    bool isSwept;
    int touchCount;
    ENUM_SIGNAL_DIRECTION expectedDirection;
};

struct SFractalPoint
{
    double price;
    datetime time;
    bool isHigh;
    bool isValid;
    int strength;
};

struct SOrderBlock
{
    double highPrice;
    double lowPrice;
    datetime startTime;
    datetime endTime;
    bool isVirgin;
    ENUM_SIGNAL_DIRECTION direction;
    int volume;
};

struct SFibonacciLevel
{
    double price;
    double level;
    bool isRespected;
    int touchCount;
};

//+------------------------------------------------------------------+
//| Trading Models class                                            |
//+------------------------------------------------------------------+
class CTradingModels
{
private:
    bool m_useLiquidity;
    bool m_useFibonacci;
    bool m_useFractals;
    bool m_useOrderBlocks;
    
    //--- Storage for identified patterns
    SLiquidityLevel m_liquidityLevels[];
    SFractalPoint m_fractals[];
    SOrderBlock m_orderBlocks[];
    SFibonacciLevel m_fibLevels[];
    
    //--- Analysis parameters
    int m_lookbackPeriod;
    int m_fractalPeriod;
    double m_liquidityThreshold;
    
    CUtils* m_utils;
    
public:
    //--- Constructor/Destructor
    CTradingModels();
    ~CTradingModels() {}
    
    //--- Initialization
    bool Init(bool useLiquidity, bool useFibonacci, bool useFractals, bool useOrderBlocks);
    
    //--- Main validation methods
    bool ValidateLiquiditySweep(const SEntrySignal &signal);
    bool ValidateFibonacci(const SEntrySignal &signal);
    bool ValidateFractal(const SEntrySignal &signal);
    bool ValidateOrderBlock(const SEntrySignal &signal);
    
    //--- Liquidity sweep methods
    void IdentifyLiquidityLevels();
    bool CheckLiquiditySweep(double currentPrice, ENUM_SIGNAL_DIRECTION direction);
    void UpdateLiquidityLevels();
    
    //--- Fibonacci methods
    void CalculateFibonacciLevels(double high, double low);
    bool IsPriceAtFibLevel(double price, double tolerance = 0.0001);
    double GetNearestFibLevel(double price);
    
    //--- Fractal methods
    void IdentifyFractals(ENUM_TIMEFRAMES timeframe = PERIOD_M15);
    bool IsFractalValid(const SFractalPoint &fractal);
    double GetFractalTP(const SEntrySignal &signal);
    
    //--- Order block methods
    void IdentifyOrderBlocks();
    bool IsOrderBlockVirgin(const SOrderBlock &block);
    bool IsPriceInOrderBlock(double price, const SOrderBlock &block);
    
    //--- Invalidation methods
    bool CheckLiquidPointsAbove(double currentPrice);
    bool CheckLiquidPointsBelow(double currentPrice);
    bool HasLiquidPointsToSweep(const SEntrySignal &signal);
    
    //--- Utility methods
    void SetUtils(CUtils* utils) { m_utils = utils; }
    void UpdateAllPatterns();
    string GetModelsReport();
    
private:
    //--- Helper methods
    bool IsSwingHigh(int index, ENUM_TIMEFRAMES timeframe, int period = 5);
    bool IsSwingLow(int index, ENUM_TIMEFRAMES timeframe, int period = 5);
    double CalculateVolume(datetime start, datetime end);
    void CleanupOldPatterns();
};

//+------------------------------------------------------------------+
//| Constructor                                                     |
//+------------------------------------------------------------------+
CTradingModels::CTradingModels()
{
    m_useLiquidity = true;
    m_useFibonacci = true;
    m_useFractals = true;
    m_useOrderBlocks = true;
    
    m_lookbackPeriod = 100;
    m_fractalPeriod = 5;
    m_liquidityThreshold = 0.001;
    
    m_utils = NULL;
    
    ArrayResize(m_liquidityLevels, 0);
    ArrayResize(m_fractals, 0);
    ArrayResize(m_orderBlocks, 0);
    ArrayResize(m_fibLevels, 0);
}

//+------------------------------------------------------------------+
//| Initialize trading models                                       |
//+------------------------------------------------------------------+
bool CTradingModels::Init(bool useLiquidity, bool useFibonacci, bool useFractals, bool useOrderBlocks)
{
    m_useLiquidity = useLiquidity;
    m_useFibonacci = useFibonacci;
    m_useFractals = useFractals;
    m_useOrderBlocks = useOrderBlocks;
    
    Print("Trading Models initialized - Liquidity: ", m_useLiquidity, 
          ", Fibonacci: ", m_useFibonacci, 
          ", Fractals: ", m_useFractals, 
          ", Order Blocks: ", m_useOrderBlocks);
    
    //--- Initial pattern identification
    UpdateAllPatterns();
    
    return true;
}

//+------------------------------------------------------------------+
//| Validate liquidity sweep model                                 |
//+------------------------------------------------------------------+
bool CTradingModels::ValidateLiquiditySweep(const SEntrySignal &signal)
{
    if(!m_useLiquidity) return false;
    
    //--- Update liquidity levels
    UpdateLiquidityLevels();
    
    //--- Check if signal aligns with liquidity sweep
    bool sweepDetected = CheckLiquiditySweep(signal.entryPrice, signal.direction);
    
    //--- Ensure no conflicting liquid points
    bool noConflictingLiquidity = !HasLiquidPointsToSweep(signal);
    
    return (sweepDetected && noConflictingLiquidity);
}

//+------------------------------------------------------------------+
//| Validate Fibonacci retracement model                           |
//+------------------------------------------------------------------+
bool CTradingModels::ValidateFibonacci(const SEntrySignal &signal)
{
    if(!m_useFibonacci) return false;
    
    //--- Get recent swing high and low
    double high[], low[];
    if(CopyHigh(Symbol(), PERIOD_H1, 0, m_lookbackPeriod, high) != m_lookbackPeriod ||
       CopyLow(Symbol(), PERIOD_H1, 0, m_lookbackPeriod, low) != m_lookbackPeriod)
        return false;
    
    //--- Find significant swing points
    double swingHigh = high[ArrayMaximum(high)];
    double swingLow = low[ArrayMinimum(low)];
    
    //--- Calculate Fibonacci levels
    CalculateFibonacciLevels(swingHigh, swingLow);
    
    //--- Check if price is at key Fibonacci level (50%-61.8%)
    double currentPrice = signal.entryPrice;
    for(int i = 0; i < ArraySize(m_fibLevels); i++)
    {
        if(m_fibLevels[i].level >= 0.5 && m_fibLevels[i].level <= 0.618)
        {
            double distance = MathAbs(currentPrice - m_fibLevels[i].price);
            double tolerance = SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 10;
            
            if(distance <= tolerance)
                return true;
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Validate fractal model                                         |
//+------------------------------------------------------------------+
bool CTradingModels::ValidateFractal(const SEntrySignal &signal)
{
    if(!m_useFractals) return false;
    
    //--- Identify fractals on M1-M15 timeframes
    IdentifyFractals(PERIOD_M1);
    IdentifyFractals(PERIOD_M5);
    IdentifyFractals(PERIOD_M15);
    
    //--- Check if signal aligns with fractal break
    double currentPrice = signal.entryPrice;
    
    for(int i = 0; i < ArraySize(m_fractals); i++)
    {
        if(!IsFractalValid(m_fractals[i])) continue;
        
        double distance = MathAbs(currentPrice - m_fractals[i].price);
        double tolerance = SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 20;
        
        if(distance <= tolerance)
        {
            //--- Check if breaking in the right direction
            if(signal.direction == SIGNAL_BUY && !m_fractals[i].isHigh)
                return true;
            if(signal.direction == SIGNAL_SELL && m_fractals[i].isHigh)
                return true;
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Validate order block model                                     |
//+------------------------------------------------------------------+
bool CTradingModels::ValidateOrderBlock(const SEntrySignal &signal)
{
    if(!m_useOrderBlocks) return false;
    
    //--- Update order blocks
    IdentifyOrderBlocks();
    
    //--- Check if price is reacting from virgin order block
    double currentPrice = signal.entryPrice;
    
    for(int i = 0; i < ArraySize(m_orderBlocks); i++)
    {
        if(!IsOrderBlockVirgin(m_orderBlocks[i])) continue;
        
        if(IsPriceInOrderBlock(currentPrice, m_orderBlocks[i]))
        {
            //--- Check direction alignment
            if(m_orderBlocks[i].direction == signal.direction)
                return true;
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Identify liquidity levels                                      |
//+------------------------------------------------------------------+
void CTradingModels::IdentifyLiquidityLevels()
{
    ArrayResize(m_liquidityLevels, 0);
    
    double high[], low[];
    if(CopyHigh(Symbol(), PERIOD_H1, 0, m_lookbackPeriod, high) != m_lookbackPeriod ||
       CopyLow(Symbol(), PERIOD_H1, 0, m_lookbackPeriod, low) != m_lookbackPeriod)
        return;
    
    //--- Find swing highs and lows as potential liquidity levels
    for(int i = m_fractalPeriod; i < m_lookbackPeriod - m_fractalPeriod; i++)
    {
        //--- Check for swing high
        if(IsSwingHigh(i, PERIOD_H1, m_fractalPeriod))
        {
            SLiquidityLevel level = {};
            level.price = high[i];
            level.time = iTime(Symbol(), PERIOD_H1, i);
            level.isSwept = false;
            level.touchCount = 1;
            level.expectedDirection = SIGNAL_SELL;
            
            int size = ArraySize(m_liquidityLevels);
            ArrayResize(m_liquidityLevels, size + 1);
            m_liquidityLevels[size] = level;
        }
        
        //--- Check for swing low
        if(IsSwingLow(i, PERIOD_H1, m_fractalPeriod))
        {
            SLiquidityLevel level = {};
            level.price = low[i];
            level.time = iTime(Symbol(), PERIOD_H1, i);
            level.isSwept = false;
            level.touchCount = 1;
            level.expectedDirection = SIGNAL_BUY;
            
            int size = ArraySize(m_liquidityLevels);
            ArrayResize(m_liquidityLevels, size + 1);
            m_liquidityLevels[size] = level;
        }
    }
}

//+------------------------------------------------------------------+
//| Check for liquidity sweep                                      |
//+------------------------------------------------------------------+
bool CTradingModels::CheckLiquiditySweep(double currentPrice, ENUM_SIGNAL_DIRECTION direction)
{
    for(int i = 0; i < ArraySize(m_liquidityLevels); i++)
    {
        if(m_liquidityLevels[i].isSwept) continue;
        
        double distance = MathAbs(currentPrice - m_liquidityLevels[i].price);
        double threshold = SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 50;
        
        if(distance <= threshold)
        {
            //--- Check if sweep occurred and reversal expected
            if(direction == SIGNAL_BUY && m_liquidityLevels[i].expectedDirection == SIGNAL_BUY)
            {
                //--- Mark as swept
                m_liquidityLevels[i].isSwept = true;
                return true;
            }
            else if(direction == SIGNAL_SELL && m_liquidityLevels[i].expectedDirection == SIGNAL_SELL)
            {
                //--- Mark as swept
                m_liquidityLevels[i].isSwept = true;
                return true;
            }
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Update liquidity levels                                        |
//+------------------------------------------------------------------+
void CTradingModels::UpdateLiquidityLevels()
{
    //--- Re-identify if array is empty or old
    if(ArraySize(m_liquidityLevels) == 0)
    {
        IdentifyLiquidityLevels();
        return;
    }
    
    //--- Check for recent sweeps
    double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
    
    for(int i = 0; i < ArraySize(m_liquidityLevels); i++)
    {
        if(m_liquidityLevels[i].isSwept) continue;
        
        //--- Check if level was swept
        if(m_liquidityLevels[i].expectedDirection == SIGNAL_BUY && currentPrice < m_liquidityLevels[i].price)
        {
            m_liquidityLevels[i].isSwept = true;
        }
        else if(m_liquidityLevels[i].expectedDirection == SIGNAL_SELL && currentPrice > m_liquidityLevels[i].price)
        {
            m_liquidityLevels[i].isSwept = true;
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate Fibonacci levels                                     |
//+------------------------------------------------------------------+
void CTradingModels::CalculateFibonacciLevels(double high, double low)
{
    ArrayResize(m_fibLevels, 0);
    double range = high - low;
    
    for(int i = 0; i < ArraySize(FIB_LEVELS); i++)
    {
        SFibonacciLevel fib = {};
        fib.level = FIB_LEVELS[i];
        fib.price = low + (range * FIB_LEVELS[i]);
        fib.isRespected = false;
        fib.touchCount = 0;
        
        int size = ArraySize(m_fibLevels);
        ArrayResize(m_fibLevels, size + 1);
        m_fibLevels[size] = fib;
    }
}

//+------------------------------------------------------------------+
//| Check if price is at Fibonacci level                          |
//+------------------------------------------------------------------+
bool CTradingModels::IsPriceAtFibLevel(double price, double tolerance = 0.0001)
{
    for(int i = 0; i < ArraySize(m_fibLevels); i++)
    {
        if(MathAbs(price - m_fibLevels[i].price) <= tolerance)
            return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Get nearest Fibonacci level                                    |
//+------------------------------------------------------------------+
double CTradingModels::GetNearestFibLevel(double price)
{
    double nearestLevel = 0;
    double minDistance = DBL_MAX;
    
    for(int i = 0; i < ArraySize(m_fibLevels); i++)
    {
        double distance = MathAbs(price - m_fibLevels[i].price);
        if(distance < minDistance)
        {
            minDistance = distance;
            nearestLevel = m_fibLevels[i].price;
        }
    }
    
    return nearestLevel;
}

//+------------------------------------------------------------------+
//| Identify fractals                                              |
//+------------------------------------------------------------------+
void CTradingModels::IdentifyFractals(ENUM_TIMEFRAMES timeframe = PERIOD_M15)
{
    //--- Only identify for shorter timeframes
    if(timeframe > PERIOD_M15) return;
    
    double high[], low[];
    if(CopyHigh(Symbol(), timeframe, 0, 50, high) != 50 ||
       CopyLow(Symbol(), timeframe, 0, 50, low) != 50)
        return;
    
    //--- Find fractal points
    for(int i = m_fractalPeriod; i < 50 - m_fractalPeriod; i++)
    {
        //--- Check for fractal high
        if(IsSwingHigh(i, timeframe, m_fractalPeriod))
        {
            SFractalPoint fractal = {};
            fractal.price = high[i];
            fractal.time = iTime(Symbol(), timeframe, i);
            fractal.isHigh = true;
            fractal.isValid = true;
            fractal.strength = CalculateFractalStrength(i, high, true);
            
            int size = ArraySize(m_fractals);
            ArrayResize(m_fractals, size + 1);
            m_fractals[size] = fractal;
        }
        
        //--- Check for fractal low
        if(IsSwingLow(i, timeframe, m_fractalPeriod))
        {
            SFractalPoint fractal = {};
            fractal.price = low[i];
            fractal.time = iTime(Symbol(), timeframe, i);
            fractal.isHigh = false;
            fractal.isValid = true;
            fractal.strength = CalculateFractalStrength(i, low, false);
            
            int size = ArraySize(m_fractals);
            ArrayResize(m_fractals, size + 1);
            m_fractals[size] = fractal;
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate fractal strength                                     |
//+------------------------------------------------------------------+
int CalculateFractalStrength(int index, const double &array[], bool isHigh)
{
    int strength = 0;
    int period = 3;
    
    for(int i = 1; i <= period; i++)
    {
        if(isHigh)
        {
            if(index - i >= 0 && array[index] > array[index - i]) strength++;
            if(index + i < ArraySize(array) && array[index] > array[index + i]) strength++;
        }
        else
        {
            if(index - i >= 0 && array[index] < array[index - i]) strength++;
            if(index + i < ArraySize(array) && array[index] < array[index + i]) strength++;
        }
    }
    
    return strength;
}

//+------------------------------------------------------------------+
//| Check if fractal is valid                                      |
//+------------------------------------------------------------------+
bool CTradingModels::IsFractalValid(const SFractalPoint &fractal)
{
    //--- Check age of fractal (not too old)
    datetime currentTime = TimeCurrent();
    if(currentTime - fractal.time > 86400) // 24 hours
        return false;
    
    //--- Check strength
    return (fractal.strength >= 3);
}

//+------------------------------------------------------------------+
//| Get fractal-based take profit                                 |
//+------------------------------------------------------------------+
double CTradingModels::GetFractalTP(const SEntrySignal &signal)
{
    double targetPrice = 0;
    datetime nearestTime = 0;
    
    //--- Find the fractal where the signal originated
    for(int i = 0; i < ArraySize(m_fractals); i++)
    {
        if(!IsFractalValid(m_fractals[i])) continue;
        
        //--- Look for opposite fractal in recent history
        if(signal.direction == SIGNAL_BUY && m_fractals[i].isHigh)
        {
            if(m_fractals[i].time > nearestTime)
            {
                nearestTime = m_fractals[i].time;
                targetPrice = m_fractals[i].price;
            }
        }
        else if(signal.direction == SIGNAL_SELL && !m_fractals[i].isHigh)
        {
            if(m_fractals[i].time > nearestTime)
            {
                nearestTime = m_fractals[i].time;
                targetPrice = m_fractals[i].price;
            }
        }
    }
    
    return targetPrice;
}

//+------------------------------------------------------------------+
//| Identify order blocks                                          |
//+------------------------------------------------------------------+
void CTradingModels::IdentifyOrderBlocks()
{
    ArrayResize(m_orderBlocks, 0);
    
    double open[], high[], low[], close[];
    if(CopyOpen(Symbol(), PERIOD_M15, 0, 100, open) != 100 ||
       CopyHigh(Symbol(), PERIOD_M15, 0, 100, high) != 100 ||
       CopyLow(Symbol(), PERIOD_M15, 0, 100, low) != 100 ||
       CopyClose(Symbol(), PERIOD_M15, 0, 100, close) != 100)
        return;
    
    //--- Look for strong impulse moves followed by retracements
    for(int i = 10; i < 90; i++)
    {
        //--- Check for bullish order block
        if(close[i] > open[i] && (close[i] - open[i]) > (high[i] - low[i]) * 0.7)
        {
            //--- Verify impulse continuation
            bool strongMove = false;
            for(int j = i - 5; j < i; j++)
            {
                if(close[j] > close[j + 3])
                {
                    strongMove = true;
                    break;
                }
            }
            
            if(strongMove)
            {
                SOrderBlock block = {};
                block.highPrice = high[i];
                block.lowPrice = low[i];
                block.startTime = iTime(Symbol(), PERIOD_M15, i);
                block.endTime = iTime(Symbol(), PERIOD_M15, i);
                block.isVirgin = true;
                block.direction = SIGNAL_BUY;
                block.volume = (int)iVolume(Symbol(), PERIOD_M15, i);
                
                int size = ArraySize(m_orderBlocks);
                ArrayResize(m_orderBlocks, size + 1);
                m_orderBlocks[size] = block;
            }
        }
        
        //--- Check for bearish order block
        if(close[i] < open[i] && (open[i] - close[i]) > (high[i] - low[i]) * 0.7)
        {
            //--- Verify impulse continuation
            bool strongMove = false;
            for(int j = i - 5; j < i; j++)
            {
                if(close[j] < close[j + 3])
                {
                    strongMove = true;
                    break;
                }
            }
            
            if(strongMove)
            {
                SOrderBlock block = {};
                block.highPrice = high[i];
                block.lowPrice = low[i];
                block.startTime = iTime(Symbol(), PERIOD_M15, i);
                block.endTime = iTime(Symbol(), PERIOD_M15, i);
                block.isVirgin = true;
                block.direction = SIGNAL_SELL;
                block.volume = (int)iVolume(Symbol(), PERIOD_M15, i);
                
                int size = ArraySize(m_orderBlocks);
                ArrayResize(m_orderBlocks, size + 1);
                m_orderBlocks[size] = block;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check if order block is virgin (untested)                     |
//+------------------------------------------------------------------+
bool CTradingModels::IsOrderBlockVirgin(const SOrderBlock &block)
{
    //--- Check if price has returned to the block since creation
    double high[], low[];
    datetime startBar = iBarShift(Symbol(), PERIOD_M15, block.startTime);
    int barsToCheck = (int)(startBar);
    
    if(barsToCheck <= 0) return true;
    
    if(CopyHigh(Symbol(), PERIOD_M15, 0, barsToCheck, high) != barsToCheck ||
       CopyLow(Symbol(), PERIOD_M15, 0, barsToCheck, low) != barsToCheck)
        return true;
    
    //--- Check if any bar has touched the order block
    for(int i = 0; i < barsToCheck; i++)
    {
        if(high[i] >= block.lowPrice && low[i] <= block.highPrice)
            return false; // Block has been tested
    }
    
    return true; // Still virgin
}

//+------------------------------------------------------------------+
//| Check if price is in order block                              |
//+------------------------------------------------------------------+
bool CTradingModels::IsPriceInOrderBlock(double price, const SOrderBlock &block)
{
    return (price >= block.lowPrice && price <= block.highPrice);
}

//+------------------------------------------------------------------+
//| Check for liquid points above current price                   |
//+------------------------------------------------------------------+
bool CTradingModels::CheckLiquidPointsAbove(double currentPrice)
{
    for(int i = 0; i < ArraySize(m_liquidityLevels); i++)
    {
        if(!m_liquidityLevels[i].isSwept && m_liquidityLevels[i].price > currentPrice)
        {
            double distance = m_liquidityLevels[i].price - currentPrice;
            if(distance < SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 200) // Within 20 pips
                return true;
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Check for liquid points below current price                   |
//+------------------------------------------------------------------+
bool CTradingModels::CheckLiquidPointsBelow(double currentPrice)
{
    for(int i = 0; i < ArraySize(m_liquidityLevels); i++)
    {
        if(!m_liquidityLevels[i].isSwept && m_liquidityLevels[i].price < currentPrice)
        {
            double distance = currentPrice - m_liquidityLevels[i].price;
            if(distance < SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 200) // Within 20 pips
                return true;
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| Check if signal has conflicting liquid points to sweep        |
//+------------------------------------------------------------------+
bool CTradingModels::HasLiquidPointsToSweep(const SEntrySignal &signal)
{
    if(signal.direction == SIGNAL_BUY)
    {
        //--- For buy signals, check if there are unswept lows below
        return CheckLiquidPointsBelow(signal.entryPrice);
    }
    else if(signal.direction == SIGNAL_SELL)
    {
        //--- For sell signals, check if there are unswept highs above
        return CheckLiquidPointsAbove(signal.entryPrice);
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Check if swing high                                           |
//+------------------------------------------------------------------+
bool CTradingModels::IsSwingHigh(int index, ENUM_TIMEFRAMES timeframe, int period = 5)
{
    double high[];
    if(CopyHigh(Symbol(), timeframe, 0, index + period + 1, high) != index + period + 1)
        return false;
    
    double centerPrice = high[index];
    
    //--- Check left side
    for(int i = index + 1; i <= index + period; i++)
    {
        if(high[i] >= centerPrice)
            return false;
    }
    
    //--- Check right side
    for(int i = index - period; i < index; i++)
    {
        if(i >= 0 && high[i] >= centerPrice)
            return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check if swing low                                            |
//+------------------------------------------------------------------+
bool CTradingModels::IsSwingLow(int index, ENUM_TIMEFRAMES timeframe, int period = 5)
{
    double low[];
    if(CopyLow(Symbol(), timeframe, 0, index + period + 1, low) != index + period + 1)
        return false;
    
    double centerPrice = low[index];
    
    //--- Check left side
    for(int i = index + 1; i <= index + period; i++)
    {
        if(low[i] <= centerPrice)
            return false;
    }
    
    //--- Check right side
    for(int i = index - period; i < index; i++)
    {
        if(i >= 0 && low[i] <= centerPrice)
            return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Calculate volume for time period                              |
//+------------------------------------------------------------------+
double CTradingModels::CalculateVolume(datetime start, datetime end)
{
    int startBar = iBarShift(Symbol(), PERIOD_M15, start);
    int endBar = iBarShift(Symbol(), PERIOD_M15, end);
    
    double totalVolume = 0;
    for(int i = endBar; i <= startBar; i++)
    {
        totalVolume += iVolume(Symbol(), PERIOD_M15, i);
    }
    
    return totalVolume;
}

//+------------------------------------------------------------------+
//| Update all patterns                                           |
//+------------------------------------------------------------------+
void CTradingModels::UpdateAllPatterns()
{
    CleanupOldPatterns();
    
    if(m_useLiquidity) IdentifyLiquidityLevels();
    if(m_useFractals) 
    {
        IdentifyFractals(PERIOD_M1);
        IdentifyFractals(PERIOD_M5);
        IdentifyFractals(PERIOD_M15);
    }
    if(m_useOrderBlocks) IdentifyOrderBlocks();
}

//+------------------------------------------------------------------+
//| Cleanup old patterns                                          |
//+------------------------------------------------------------------+
void CTradingModels::CleanupOldPatterns()
{
    datetime cutoffTime = TimeCurrent() - 86400 * 7; // 1 week old
    
    //--- Remove old fractals
    for(int i = ArraySize(m_fractals) - 1; i >= 0; i--)
    {
        if(m_fractals[i].time < cutoffTime)
        {
            ArrayRemove(m_fractals, i, 1);
        }
    }
    
    //--- Remove old order blocks
    for(int i = ArraySize(m_orderBlocks) - 1; i >= 0; i--)
    {
        if(m_orderBlocks[i].startTime < cutoffTime)
        {
            ArrayRemove(m_orderBlocks, i, 1);
        }
    }
    
    //--- Remove old liquidity levels
    for(int i = ArraySize(m_liquidityLevels) - 1; i >= 0; i--)
    {
        if(m_liquidityLevels[i].time < cutoffTime)
        {
            ArrayRemove(m_liquidityLevels, i, 1);
        }
    }
}

//+------------------------------------------------------------------+
//| Generate models report                                         |
//+------------------------------------------------------------------+
string CTradingModels::GetModelsReport()
{
    string report = "\n=== TRADING MODELS REPORT ===\n";
    report += "Liquidity Levels: " + IntegerToString(ArraySize(m_liquidityLevels)) + "\n";
    report += "Fractals: " + IntegerToString(ArraySize(m_fractals)) + "\n";
    report += "Order Blocks: " + IntegerToString(ArraySize(m_orderBlocks)) + "\n";
    report += "Fibonacci Levels: " + IntegerToString(ArraySize(m_fibLevels)) + "\n";
    
    report += "\nActive Models:\n";
    report += "- Liquidity Sweeps: " + (m_useLiquidity ? "ENABLED" : "DISABLED") + "\n";
    report += "- Fibonacci: " + (m_useFibonacci ? "ENABLED" : "DISABLED") + "\n";
    report += "- Fractals: " + (m_useFractals ? "ENABLED" : "DISABLED") + "\n";
    report += "- Order Blocks: " + (m_useOrderBlocks ? "ENABLED" : "DISABLED") + "\n";
    report += "============================\n";
    
    return report;
}