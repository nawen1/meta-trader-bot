//+------------------------------------------------------------------+
//|                                            PositionManager.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

#include "Utils.mqh"

//--- Position management structures
struct SPositionData
{
    ulong ticket;
    double entryPrice;
    double originalSL;
    double currentSL;
    double originalTP1;
    double originalTP2;
    double originalTP3;
    double currentTP;
    double volume;
    double partialVolume1;
    double partialVolume2;
    double partialVolume3;
    ENUM_SIGNAL_DIRECTION direction;
    string model;
    datetime openTime;
    datetime lastUpdate;
    bool tp1Hit;
    bool tp2Hit;
    bool tp3Hit;
    bool slMovedToTP2;
    bool isActive;
    double unrealizedPnL;
    double realizedPnL;
    int magicNumber;
};

struct SVolatilityData
{
    double currentATR;
    double averageATR;
    double volatilityRatio;
    bool isHighVolatility;
    datetime lastUpdate;
};

//+------------------------------------------------------------------+
//| Position Manager class                                          |
//+------------------------------------------------------------------+
class CPositionManager
{
private:
    bool     m_useTP3;
    double   m_tp1Ratio;
    double   m_tp2Ratio;
    double   m_tp3Ratio;
    bool     m_moveSLToTP2;
    
    //--- Position tracking
    SPositionData m_positions[];
    int      m_maxPositions;
    
    //--- Volatility tracking
    SVolatilityData m_volatility;
    double   m_volatilityMultiplier;
    
    //--- Partial close percentages
    double   m_tp1Percentage;  // % of position to close at TP1
    double   m_tp2Percentage;  // % of remaining position to close at TP2
    
    CUtils*  m_utils;
    
public:
    //--- Constructor/Destructor
    CPositionManager();
    ~CPositionManager() {}
    
    //--- Initialization
    bool Init(bool useTP3, double tp1Ratio, double tp2Ratio, double tp3Ratio, bool moveSLToTP2);
    
    //--- Position registration and management
    bool RegisterPosition(ulong ticket, const SEntrySignal &signal);
    void UpdatePositions();
    void UpdateSinglePosition(int index);
    
    //--- TP/SL management
    bool MoveSLToBreakeven(int index);
    bool MoveSLToTP2(int index);
    bool AdjustSLForVolatility(int index);
    void CalculateDynamicTP(int index, const SEntrySignal &signal);
    
    //--- Partial closing
    bool ClosePartialPosition(int index, double percentage, string reason);
    double CalculatePartialVolume(double totalVolume, double percentage);
    
    //--- Volatility management
    void UpdateVolatilityData();
    bool IsHighVolatilityPeriod();
    double GetVolatilityAdjustedSL(double originalSL, double entryPrice, ENUM_SIGNAL_DIRECTION direction);
    
    //--- Position monitoring
    void CheckTPLevels(int index);
    void UpdatePnL(int index);
    bool IsPositionValid(int index);
    
    //--- Position utilities
    int FindPositionByTicket(ulong ticket);
    void RemovePosition(int index);
    void CleanupClosedPositions();
    
    //--- Risk management
    bool ValidateTPSLLevels(double entry, double sl, double tp1, double tp2, double tp3, ENUM_SIGNAL_DIRECTION direction);
    double CalculateRiskRewardRatio(double entry, double sl, double tp);
    
    //--- Reporting
    string GetPositionsReport();
    int GetActivePositionsCount();
    double GetTotalUnrealizedPnL();
    double GetTotalRealizedPnL();
    
    //--- Utility methods
    void SetUtils(CUtils* utils) { m_utils = utils; }
    void SetVolatilityMultiplier(double multiplier) { m_volatilityMultiplier = multiplier; }
    
private:
    //--- Helper methods
    bool ModifyPosition(ulong ticket, double sl, double tp);
    bool ClosePosition(ulong ticket, double volume);
    double GetCurrentPrice(ENUM_SIGNAL_DIRECTION direction);
    void LogPositionUpdate(int index, string action, string details);
};

//+------------------------------------------------------------------+
//| Constructor                                                     |
//+------------------------------------------------------------------+
CPositionManager::CPositionManager()
{
    m_useTP3 = true;
    m_tp1Ratio = 1.0;
    m_tp2Ratio = 2.0;
    m_tp3Ratio = 3.0;
    m_moveSLToTP2 = true;
    
    m_maxPositions = 20;
    ArrayResize(m_positions, 0);
    
    m_tp1Percentage = 0.33; // Close 33% at TP1
    m_tp2Percentage = 0.50; // Close 50% of remaining at TP2
    
    m_volatilityMultiplier = 1.5;
    
    //--- Initialize volatility data
    m_volatility.currentATR = 0;
    m_volatility.averageATR = 0;
    m_volatility.volatilityRatio = 1.0;
    m_volatility.isHighVolatility = false;
    m_volatility.lastUpdate = 0;
    
    m_utils = NULL;
}

//+------------------------------------------------------------------+
//| Initialize position manager                                     |
//+------------------------------------------------------------------+
bool CPositionManager::Init(bool useTP3, double tp1Ratio, double tp2Ratio, double tp3Ratio, bool moveSLToTP2)
{
    m_useTP3 = useTP3;
    m_tp1Ratio = tp1Ratio;
    m_tp2Ratio = tp2Ratio;
    m_tp3Ratio = tp3Ratio;
    m_moveSLToTP2 = moveSLToTP2;
    
    //--- Validate ratios
    if(m_tp1Ratio <= 0 || m_tp2Ratio <= m_tp1Ratio || (m_useTP3 && m_tp3Ratio <= m_tp2Ratio))
    {
        Print("ERROR: Invalid TP ratios");
        return false;
    }
    
    //--- Initialize volatility tracking
    UpdateVolatilityData();
    
    Print("Position Manager initialized - TP1:", m_tp1Ratio, " TP2:", m_tp2Ratio, " TP3:", m_tp3Ratio, " MoveSL:", m_moveSLToTP2);
    return true;
}

//+------------------------------------------------------------------+
//| Register new position for management                           |
//+------------------------------------------------------------------+
bool CPositionManager::RegisterPosition(ulong ticket, const SEntrySignal &signal)
{
    //--- Check if position already exists
    if(FindPositionByTicket(ticket) >= 0)
        return false;
    
    //--- Get position info
    if(!PositionSelectByTicket(ticket))
        return false;
    
    //--- Create position data
    SPositionData pos = {};
    pos.ticket = ticket;
    pos.entryPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    pos.volume = PositionGetDouble(POSITION_VOLUME);
    pos.direction = (ENUM_SIGNAL_DIRECTION)PositionGetInteger(POSITION_TYPE);
    pos.model = signal.model;
    pos.openTime = (datetime)PositionGetInteger(POSITION_TIME);
    pos.lastUpdate = TimeCurrent();
    pos.magicNumber = (int)PositionGetInteger(POSITION_MAGIC);
    
    //--- Set original levels
    pos.originalSL = signal.stopLoss;
    pos.currentSL = signal.stopLoss;
    pos.originalTP1 = signal.takeProfit1;
    pos.originalTP2 = signal.takeProfit2;
    pos.originalTP3 = signal.takeProfit3;
    pos.currentTP = signal.takeProfit1;
    
    //--- Calculate partial volumes
    pos.partialVolume1 = CalculatePartialVolume(pos.volume, m_tp1Percentage);
    pos.partialVolume2 = CalculatePartialVolume(pos.volume - pos.partialVolume1, m_tp2Percentage);
    pos.partialVolume3 = pos.volume - pos.partialVolume1 - pos.partialVolume2;
    
    //--- Initialize flags
    pos.tp1Hit = false;
    pos.tp2Hit = false;
    pos.tp3Hit = false;
    pos.slMovedToTP2 = false;
    pos.isActive = true;
    pos.unrealizedPnL = 0;
    pos.realizedPnL = 0;
    
    //--- Adjust SL for volatility if needed
    if(IsHighVolatilityPeriod())
    {
        pos.currentSL = GetVolatilityAdjustedSL(pos.originalSL, pos.entryPrice, pos.direction);
        ModifyPosition(ticket, pos.currentSL, pos.currentTP);
    }
    
    //--- Add to positions array
    int size = ArraySize(m_positions);
    ArrayResize(m_positions, size + 1);
    m_positions[size] = pos;
    
    Print("Position registered: Ticket=", ticket, " Model=", signal.model, " Volume=", pos.volume);
    return true;
}

//+------------------------------------------------------------------+
//| Update all active positions                                    |
//+------------------------------------------------------------------+
void CPositionManager::UpdatePositions()
{
    //--- Update volatility data
    UpdateVolatilityData();
    
    //--- Clean up closed positions first
    CleanupClosedPositions();
    
    //--- Update each active position
    for(int i = 0; i < ArraySize(m_positions); i++)
    {
        if(m_positions[i].isActive)
        {
            UpdateSinglePosition(i);
        }
    }
}

//+------------------------------------------------------------------+
//| Update single position                                         |
//+------------------------------------------------------------------+
void CPositionManager::UpdateSinglePosition(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return;
    
    //--- Check if position still exists
    if(!PositionSelectByTicket(m_positions[index].ticket))
    {
        m_positions[index].isActive = false;
        return;
    }
    
    //--- Update P&L
    UpdatePnL(index);
    
    //--- Check TP levels
    CheckTPLevels(index);
    
    //--- Adjust SL for volatility if needed
    if(IsHighVolatilityPeriod() && !m_positions[index].slMovedToTP2)
    {
        AdjustSLForVolatility(index);
    }
    
    //--- Update timestamp
    m_positions[index].lastUpdate = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Move stop loss to breakeven                                   |
//+------------------------------------------------------------------+
bool CPositionManager::MoveSLToBreakeven(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return false;
    
    double newSL = m_positions[index].entryPrice;
    
    //--- Add small buffer to avoid immediate closure
    double buffer = SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 5;
    if(m_positions[index].direction == SIGNAL_BUY)
        newSL += buffer;
    else
        newSL -= buffer;
    
    if(ModifyPosition(m_positions[index].ticket, newSL, m_positions[index].currentTP))
    {
        m_positions[index].currentSL = newSL;
        LogPositionUpdate(index, "SL_TO_BREAKEVEN", "SL moved to breakeven + buffer");
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Move stop loss to TP2 level                                   |
//+------------------------------------------------------------------+
bool CPositionManager::MoveSLToTP2(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return false;
    
    if(m_positions[index].slMovedToTP2)
        return true;
    
    double newSL = m_positions[index].originalTP2;
    
    //--- Add small buffer
    double buffer = SymbolInfoDouble(Symbol(), SYMBOL_POINT) * 10;
    if(m_positions[index].direction == SIGNAL_BUY)
        newSL -= buffer;
    else
        newSL += buffer;
    
    if(ModifyPosition(m_positions[index].ticket, newSL, m_positions[index].currentTP))
    {
        m_positions[index].currentSL = newSL;
        m_positions[index].slMovedToTP2 = true;
        LogPositionUpdate(index, "SL_TO_TP2", "SL moved to TP2 level - risk eliminated");
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Adjust stop loss for high volatility                          |
//+------------------------------------------------------------------+
bool CPositionManager::AdjustSLForVolatility(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return false;
    
    if(!IsHighVolatilityPeriod())
        return false;
    
    double adjustedSL = GetVolatilityAdjustedSL(m_positions[index].originalSL, 
                                               m_positions[index].entryPrice, 
                                               m_positions[index].direction);
    
    //--- Only adjust if it's further from entry (safer)
    bool shouldAdjust = false;
    if(m_positions[index].direction == SIGNAL_BUY)
        shouldAdjust = (adjustedSL < m_positions[index].currentSL);
    else
        shouldAdjust = (adjustedSL > m_positions[index].currentSL);
    
    if(shouldAdjust && ModifyPosition(m_positions[index].ticket, adjustedSL, m_positions[index].currentTP))
    {
        double oldSL = m_positions[index].currentSL;
        m_positions[index].currentSL = adjustedSL;
        LogPositionUpdate(index, "SL_VOLATILITY_ADJUSTED", 
                         "SL adjusted for volatility: " + DoubleToString(oldSL, 5) + " -> " + DoubleToString(adjustedSL, 5));
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Calculate dynamic take profit levels                          |
//+------------------------------------------------------------------+
void CPositionManager::CalculateDynamicTP(int index, const SEntrySignal &signal)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return;
    
    double entry = m_positions[index].entryPrice;
    double sl = m_positions[index].currentSL;
    double slDistance = MathAbs(entry - sl);
    
    //--- Calculate TP levels based on risk:reward ratios
    if(m_positions[index].direction == SIGNAL_BUY)
    {
        m_positions[index].originalTP1 = entry + (slDistance * m_tp1Ratio);
        m_positions[index].originalTP2 = entry + (slDistance * m_tp2Ratio);
        if(m_useTP3)
            m_positions[index].originalTP3 = entry + (slDistance * m_tp3Ratio);
    }
    else
    {
        m_positions[index].originalTP1 = entry - (slDistance * m_tp1Ratio);
        m_positions[index].originalTP2 = entry - (slDistance * m_tp2Ratio);
        if(m_useTP3)
            m_positions[index].originalTP3 = entry - (slDistance * m_tp3Ratio);
    }
    
    //--- For fractals, use fractal-based TP if available
    if(signal.model == "FRACTAL" && m_utils != NULL)
    {
        // This would integrate with TradingModels to get fractal TP
        // For now, use calculated levels
    }
    
    m_positions[index].currentTP = m_positions[index].originalTP1;
}

//+------------------------------------------------------------------+
//| Close partial position                                         |
//+------------------------------------------------------------------+
bool CPositionManager::ClosePartialPosition(int index, double percentage, string reason)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return false;
    
    if(!PositionSelectByTicket(m_positions[index].ticket))
        return false;
    
    double currentVolume = PositionGetDouble(POSITION_VOLUME);
    double volumeToClose = CalculatePartialVolume(currentVolume, percentage);
    
    if(volumeToClose <= 0)
        return false;
    
    if(ClosePosition(m_positions[index].ticket, volumeToClose))
    {
        //--- Update position data
        m_positions[index].volume = currentVolume - volumeToClose;
        
        //--- Calculate realized P&L for closed portion
        double currentPrice = GetCurrentPrice(m_positions[index].direction);
        double pnlPerLot = 0;
        
        if(m_positions[index].direction == SIGNAL_BUY)
            pnlPerLot = currentPrice - m_positions[index].entryPrice;
        else
            pnlPerLot = m_positions[index].entryPrice - currentPrice;
        
        double pipValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
        double pipSize = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
        m_positions[index].realizedPnL += (pnlPerLot * pipValue * volumeToClose) / pipSize;
        
        LogPositionUpdate(index, "PARTIAL_CLOSE", reason + " - Volume: " + DoubleToString(volumeToClose, 2));
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Calculate partial volume                                       |
//+------------------------------------------------------------------+
double CPositionManager::CalculatePartialVolume(double totalVolume, double percentage)
{
    double volume = totalVolume * percentage;
    double lotStep = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
    
    if(lotStep > 0)
        volume = MathFloor(volume / lotStep) * lotStep;
    
    double minLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
    return (volume >= minLot) ? volume : 0;
}

//+------------------------------------------------------------------+
//| Update volatility data                                         |
//+------------------------------------------------------------------+
void CPositionManager::UpdateVolatilityData()
{
    if(m_utils == NULL)
        return;
    
    datetime currentTime = TimeCurrent();
    
    //--- Update every hour
    if(currentTime - m_volatility.lastUpdate < 3600)
        return;
    
    m_volatility.currentATR = m_utils.GetATR(14, PERIOD_H1);
    m_volatility.averageATR = m_utils.GetATR(50, PERIOD_H1);
    
    if(m_volatility.averageATR > 0)
    {
        m_volatility.volatilityRatio = m_volatility.currentATR / m_volatility.averageATR;
        m_volatility.isHighVolatility = (m_volatility.volatilityRatio > m_volatilityMultiplier);
    }
    
    m_volatility.lastUpdate = currentTime;
}

//+------------------------------------------------------------------+
//| Check if in high volatility period                            |
//+------------------------------------------------------------------+
bool CPositionManager::IsHighVolatilityPeriod()
{
    UpdateVolatilityData();
    return m_volatility.isHighVolatility;
}

//+------------------------------------------------------------------+
//| Get volatility adjusted stop loss                             |
//+------------------------------------------------------------------+
double CPositionManager::GetVolatilityAdjustedSL(double originalSL, double entryPrice, ENUM_SIGNAL_DIRECTION direction)
{
    if(m_volatility.volatilityRatio <= 1.0)
        return originalSL;
    
    //--- Increase SL distance by volatility ratio, but cap at 2x
    double multiplier = MathMin(m_volatility.volatilityRatio, 2.0);
    double originalDistance = MathAbs(entryPrice - originalSL);
    double adjustedDistance = originalDistance * multiplier;
    
    double adjustedSL;
    if(direction == SIGNAL_BUY)
        adjustedSL = entryPrice - adjustedDistance;
    else
        adjustedSL = entryPrice + adjustedDistance;
    
    if(m_utils != NULL)
        return m_utils.NormalizePrice(adjustedSL);
    
    return adjustedSL;
}

//+------------------------------------------------------------------+
//| Check take profit levels                                      |
//+------------------------------------------------------------------+
void CPositionManager::CheckTPLevels(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return;
    
    double currentPrice = GetCurrentPrice(m_positions[index].direction);
    bool isTP1Hit = false, isTP2Hit = false, isTP3Hit = false;
    
    //--- Check TP levels based on direction
    if(m_positions[index].direction == SIGNAL_BUY)
    {
        isTP1Hit = (currentPrice >= m_positions[index].originalTP1);
        isTP2Hit = (currentPrice >= m_positions[index].originalTP2);
        if(m_useTP3)
            isTP3Hit = (currentPrice >= m_positions[index].originalTP3);
    }
    else
    {
        isTP1Hit = (currentPrice <= m_positions[index].originalTP1);
        isTP2Hit = (currentPrice <= m_positions[index].originalTP2);
        if(m_useTP3)
            isTP3Hit = (currentPrice <= m_positions[index].originalTP3);
    }
    
    //--- Handle TP1
    if(isTP1Hit && !m_positions[index].tp1Hit)
    {
        ClosePartialPosition(index, m_tp1Percentage, "TP1 reached");
        MoveSLToBreakeven(index);
        m_positions[index].tp1Hit = true;
        m_positions[index].currentTP = m_positions[index].originalTP2;
        ModifyPosition(m_positions[index].ticket, m_positions[index].currentSL, m_positions[index].currentTP);
    }
    
    //--- Handle TP2
    if(isTP2Hit && !m_positions[index].tp2Hit && m_positions[index].tp1Hit)
    {
        double closePercentage = m_useTP3 ? m_tp2Percentage : 1.0; // Close remaining if no TP3
        ClosePartialPosition(index, closePercentage, "TP2 reached");
        
        if(m_moveSLToTP2)
            MoveSLToTP2(index);
        
        m_positions[index].tp2Hit = true;
        
        if(m_useTP3)
        {
            m_positions[index].currentTP = m_positions[index].originalTP3;
            ModifyPosition(m_positions[index].ticket, m_positions[index].currentSL, m_positions[index].currentTP);
        }
    }
    
    //--- Handle TP3
    if(m_useTP3 && isTP3Hit && !m_positions[index].tp3Hit && m_positions[index].tp2Hit)
    {
        ClosePartialPosition(index, 1.0, "TP3 reached - closing remaining position");
        m_positions[index].tp3Hit = true;
        m_positions[index].isActive = false;
    }
}

//+------------------------------------------------------------------+
//| Update position P&L                                           |
//+------------------------------------------------------------------+
void CPositionManager::UpdatePnL(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return;
    
    if(!PositionSelectByTicket(m_positions[index].ticket))
        return;
    
    m_positions[index].unrealizedPnL = PositionGetDouble(POSITION_PROFIT);
}

//+------------------------------------------------------------------+
//| Check if position is valid                                    |
//+------------------------------------------------------------------+
bool CPositionManager::IsPositionValid(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return false;
    
    return PositionSelectByTicket(m_positions[index].ticket);
}

//+------------------------------------------------------------------+
//| Find position by ticket                                       |
//+------------------------------------------------------------------+
int CPositionManager::FindPositionByTicket(ulong ticket)
{
    for(int i = 0; i < ArraySize(m_positions); i++)
    {
        if(m_positions[i].ticket == ticket)
            return i;
    }
    return -1;
}

//+------------------------------------------------------------------+
//| Remove position from tracking                                 |
//+------------------------------------------------------------------+
void CPositionManager::RemovePosition(int index)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return;
    
    ArrayRemove(m_positions, index, 1);
}

//+------------------------------------------------------------------+
//| Cleanup closed positions                                      |
//+------------------------------------------------------------------+
void CPositionManager::CleanupClosedPositions()
{
    for(int i = ArraySize(m_positions) - 1; i >= 0; i--)
    {
        if(!IsPositionValid(i) || !m_positions[i].isActive)
        {
            LogPositionUpdate(i, "POSITION_CLOSED", "Position removed from tracking");
            RemovePosition(i);
        }
    }
}

//+------------------------------------------------------------------+
//| Validate TP/SL levels                                         |
//+------------------------------------------------------------------+
bool CPositionManager::ValidateTPSLLevels(double entry, double sl, double tp1, double tp2, double tp3, ENUM_SIGNAL_DIRECTION direction)
{
    if(direction == SIGNAL_BUY)
    {
        if(sl >= entry || tp1 <= entry || tp2 <= tp1)
            return false;
        if(m_useTP3 && tp3 <= tp2)
            return false;
    }
    else
    {
        if(sl <= entry || tp1 >= entry || tp2 >= tp1)
            return false;
        if(m_useTP3 && tp3 >= tp2)
            return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Calculate risk reward ratio                                   |
//+------------------------------------------------------------------+
double CPositionManager::CalculateRiskRewardRatio(double entry, double sl, double tp)
{
    double risk = MathAbs(entry - sl);
    double reward = MathAbs(tp - entry);
    
    return (risk > 0) ? reward / risk : 0;
}

//+------------------------------------------------------------------+
//| Generate positions report                                     |
//+------------------------------------------------------------------+
string CPositionManager::GetPositionsReport()
{
    string report = "\n=== POSITION MANAGER REPORT ===\n";
    report += "Active Positions: " + IntegerToString(GetActivePositionsCount()) + "\n";
    report += "Total Unrealized P&L: " + DoubleToString(GetTotalUnrealizedPnL(), 2) + "\n";
    report += "Total Realized P&L: " + DoubleToString(GetTotalRealizedPnL(), 2) + "\n";
    report += "Volatility Ratio: " + DoubleToString(m_volatility.volatilityRatio, 2) + "\n";
    report += "High Volatility: " + (m_volatility.isHighVolatility ? "YES" : "NO") + "\n";
    
    for(int i = 0; i < ArraySize(m_positions); i++)
    {
        if(m_positions[i].isActive)
        {
            report += "\nPosition " + IntegerToString(i + 1) + ":\n";
            report += "  Ticket: " + IntegerToString(m_positions[i].ticket) + "\n";
            report += "  Model: " + m_positions[i].model + "\n";
            report += "  Direction: " + EnumToString((ENUM_POSITION_TYPE)m_positions[i].direction) + "\n";
            report += "  Volume: " + DoubleToString(m_positions[i].volume, 2) + "\n";
            report += "  Unrealized P&L: " + DoubleToString(m_positions[i].unrealizedPnL, 2) + "\n";
            report += "  TP1/TP2/TP3: " + (m_positions[i].tp1Hit ? "HIT" : "PENDING") + "/" +
                                           (m_positions[i].tp2Hit ? "HIT" : "PENDING") + "/" +
                                           (m_positions[i].tp3Hit ? "HIT" : "PENDING") + "\n";
        }
    }
    
    report += "===============================\n";
    return report;
}

//+------------------------------------------------------------------+
//| Get active positions count                                    |
//+------------------------------------------------------------------+
int CPositionManager::GetActivePositionsCount()
{
    int count = 0;
    for(int i = 0; i < ArraySize(m_positions); i++)
    {
        if(m_positions[i].isActive)
            count++;
    }
    return count;
}

//+------------------------------------------------------------------+
//| Get total unrealized P&L                                     |
//+------------------------------------------------------------------+
double CPositionManager::GetTotalUnrealizedPnL()
{
    double total = 0;
    for(int i = 0; i < ArraySize(m_positions); i++)
    {
        if(m_positions[i].isActive)
            total += m_positions[i].unrealizedPnL;
    }
    return total;
}

//+------------------------------------------------------------------+
//| Get total realized P&L                                       |
//+------------------------------------------------------------------+
double CPositionManager::GetTotalRealizedPnL()
{
    double total = 0;
    for(int i = 0; i < ArraySize(m_positions); i++)
    {
        total += m_positions[i].realizedPnL;
    }
    return total;
}

//+------------------------------------------------------------------+
//| Modify position SL/TP                                        |
//+------------------------------------------------------------------+
bool CPositionManager::ModifyPosition(ulong ticket, double sl, double tp)
{
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.sl = sl;
    request.tp = tp;
    
    return OrderSend(request, result);
}

//+------------------------------------------------------------------+
//| Close position (partial or full)                             |
//+------------------------------------------------------------------+
bool CPositionManager::ClosePosition(ulong ticket, double volume)
{
    if(!PositionSelectByTicket(ticket))
        return false;
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.position = ticket;
    request.symbol = PositionGetString(POSITION_SYMBOL);
    request.volume = volume;
    request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
    request.price = (request.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(Symbol(), SYMBOL_BID) : SymbolInfoDouble(Symbol(), SYMBOL_ASK);
    
    return OrderSend(request, result);
}

//+------------------------------------------------------------------+
//| Get current market price for direction                       |
//+------------------------------------------------------------------+
double CPositionManager::GetCurrentPrice(ENUM_SIGNAL_DIRECTION direction)
{
    if(direction == SIGNAL_BUY)
        return SymbolInfoDouble(Symbol(), SYMBOL_BID);
    else
        return SymbolInfoDouble(Symbol(), SYMBOL_ASK);
}

//+------------------------------------------------------------------+
//| Log position update                                          |
//+------------------------------------------------------------------+
void CPositionManager::LogPositionUpdate(int index, string action, string details)
{
    if(index < 0 || index >= ArraySize(m_positions))
        return;
    
    Print("POSITION MANAGER [", m_positions[index].ticket, "]: ", action, " - ", details);
}