//+------------------------------------------------------------------+
//|                                               RiskManager.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

#include "Utils.mqh"

//+------------------------------------------------------------------+
//| Risk Management class                                           |
//+------------------------------------------------------------------+
class CRiskManager
{
private:
    double   m_initialRisk;        // Initial risk percentage
    double   m_currentRisk;        // Current risk percentage
    double   m_minRisk;           // Minimum risk percentage
    bool     m_autoAdjust;        // Auto adjust risk flag
    double   m_riskLevels[4];     // Risk levels: 10%, 5%, 2%, 1%
    
    //--- Account information
    double   m_accountBalance;
    double   m_accountEquity;
    double   m_freeMargin;
    double   m_marginLevel;
    
public:
    //--- Constructor/Destructor
    CRiskManager();
    ~CRiskManager() {}
    
    //--- Initialization
    bool Init(double initialRisk, double minRisk, bool autoAdjust);
    
    //--- Risk calculation methods
    double CalculateLotSize(double stopLossPrice);
    double CalculateRiskAmount();
    bool AdjustRiskOnMarginIssues();
    
    //--- Validation methods
    bool ValidateMarginRequirements(double lotSize);
    bool IsRiskAcceptable(double lotSize, double stopLossPrice);
    
    //--- Account monitoring
    void UpdateAccountInfo();
    double GetCurrentRisk() const { return m_currentRisk; }
    double GetMarginLevel() const { return m_marginLevel; }
    double GetFreeMargin() const { return m_freeMargin; }
    
    //--- Notification methods
    void NotifyRiskAdjustment(double oldRisk, double newRisk);
    void NotifyMarginIssue();
    void NotifyCannotTrade();
    
    //--- Utility methods
    string GetRiskReport();
    void ResetRisk();
};

//+------------------------------------------------------------------+
//| Constructor                                                     |
//+------------------------------------------------------------------+
CRiskManager::CRiskManager()
{
    m_initialRisk = 10.0;
    m_currentRisk = 10.0;
    m_minRisk = 1.0;
    m_autoAdjust = true;
    
    //--- Initialize risk levels
    m_riskLevels[0] = 10.0;
    m_riskLevels[1] = 5.0;
    m_riskLevels[2] = 2.0;
    m_riskLevels[3] = 1.0;
    
    //--- Initialize account info
    m_accountBalance = 0;
    m_accountEquity = 0;
    m_freeMargin = 0;
    m_marginLevel = 0;
}

//+------------------------------------------------------------------+
//| Initialize risk manager                                         |
//+------------------------------------------------------------------+
bool CRiskManager::Init(double initialRisk, double minRisk, bool autoAdjust)
{
    if(initialRisk <= 0 || initialRisk > 50)
    {
        Print("ERROR: Invalid initial risk percentage: ", initialRisk);
        return false;
    }
    
    if(minRisk <= 0 || minRisk > initialRisk)
    {
        Print("ERROR: Invalid minimum risk percentage: ", minRisk);
        return false;
    }
    
    m_initialRisk = initialRisk;
    m_currentRisk = initialRisk;
    m_minRisk = minRisk;
    m_autoAdjust = autoAdjust;
    
    //--- Update account information
    UpdateAccountInfo();
    
    Print("Risk Manager initialized - Initial Risk: ", m_initialRisk, "%, Min Risk: ", m_minRisk, "%, Auto Adjust: ", m_autoAdjust);
    return true;
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk percentage and stop loss      |
//+------------------------------------------------------------------+
double CRiskManager::CalculateLotSize(double stopLossPrice)
{
    UpdateAccountInfo();
    
    //--- Calculate risk amount in account currency
    double riskAmount = CalculateRiskAmount();
    if(riskAmount <= 0)
        return 0;
    
    //--- Get current price
    double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
    if(currentPrice <= 0)
        return 0;
    
    //--- Calculate distance to stop loss in points
    double slDistance = MathAbs(currentPrice - stopLossPrice);
    if(slDistance <= 0)
        return 0;
    
    //--- Calculate pip value
    double pipValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
    double pipSize = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
    
    if(pipValue <= 0 || pipSize <= 0)
        return 0;
    
    //--- Calculate lot size
    double lotSize = riskAmount / (slDistance * pipValue / pipSize);
    
    //--- Normalize to minimum lot size
    double minLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
    
    if(lotStep > 0)
        lotSize = MathFloor(lotSize / lotStep) * lotStep;
    
    //--- Ensure lot size is within bounds
    if(lotSize < minLot)
        lotSize = 0; // Cannot trade with this risk
    else if(lotSize > maxLot)
        lotSize = maxLot;
    
    //--- Validate margin requirements
    if(!ValidateMarginRequirements(lotSize))
    {
        if(m_autoAdjust)
        {
            if(AdjustRiskOnMarginIssues())
                return CalculateLotSize(stopLossPrice); // Recursive call with adjusted risk
        }
        return 0; // Cannot trade
    }
    
    return lotSize;
}

//+------------------------------------------------------------------+
//| Calculate risk amount in account currency                      |
//+------------------------------------------------------------------+
double CRiskManager::CalculateRiskAmount()
{
    return (m_accountBalance * m_currentRisk) / 100.0;
}

//+------------------------------------------------------------------+
//| Adjust risk when margin issues occur                           |
//+------------------------------------------------------------------+
bool CRiskManager::AdjustRiskOnMarginIssues()
{
    double oldRisk = m_currentRisk;
    
    //--- Try lower risk levels
    for(int i = 0; i < 4; i++)
    {
        if(m_riskLevels[i] < m_currentRisk && m_riskLevels[i] >= m_minRisk)
        {
            m_currentRisk = m_riskLevels[i];
            NotifyRiskAdjustment(oldRisk, m_currentRisk);
            return true;
        }
    }
    
    //--- Cannot adjust further
    NotifyCannotTrade();
    return false;
}

//+------------------------------------------------------------------+
//| Validate margin requirements for lot size                      |
//+------------------------------------------------------------------+
bool CRiskManager::ValidateMarginRequirements(double lotSize)
{
    if(lotSize <= 0)
        return false;
    
    //--- Calculate required margin
    double requiredMargin = 0;
    if(!OrderCalcMargin(ORDER_TYPE_BUY, Symbol(), lotSize, SymbolInfoDouble(Symbol(), SYMBOL_ASK), requiredMargin))
        return false;
    
    //--- Check if we have enough free margin
    UpdateAccountInfo();
    
    //--- Require at least 200% margin level after trade
    double marginAfterTrade = (m_accountEquity) / (AccountInfoDouble(ACCOUNT_MARGIN) + requiredMargin) * 100;
    
    return (marginAfterTrade >= 200.0 && requiredMargin <= m_freeMargin * 0.8);
}

//+------------------------------------------------------------------+
//| Check if risk is acceptable for the trade                      |
//+------------------------------------------------------------------+
bool CRiskManager::IsRiskAcceptable(double lotSize, double stopLossPrice)
{
    double currentPrice = SymbolInfoDouble(Symbol(), SYMBOL_BID);
    double slDistance = MathAbs(currentPrice - stopLossPrice);
    double pipValue = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
    double pipSize = SymbolInfoDouble(Symbol(), SYMBOL_POINT);
    
    //--- Calculate potential loss
    double potentialLoss = (slDistance * pipValue * lotSize) / pipSize;
    double riskPercentage = (potentialLoss / m_accountBalance) * 100;
    
    return (riskPercentage <= m_currentRisk * 1.1); // Allow 10% tolerance
}

//+------------------------------------------------------------------+
//| Update account information                                      |
//+------------------------------------------------------------------+
void CRiskManager::UpdateAccountInfo()
{
    m_accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    m_accountEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    m_freeMargin = AccountInfoDouble(ACCOUNT_FREEMARGIN);
    
    double usedMargin = AccountInfoDouble(ACCOUNT_MARGIN);
    if(usedMargin > 0)
        m_marginLevel = (m_accountEquity / usedMargin) * 100;
    else
        m_marginLevel = 0;
}

//+------------------------------------------------------------------+
//| Notify about risk adjustment                                   |
//+------------------------------------------------------------------+
void CRiskManager::NotifyRiskAdjustment(double oldRisk, double newRisk)
{
    string message = StringFormat("Risk adjusted from %.1f%% to %.1f%% due to margin constraints", oldRisk, newRisk);
    Print("RISK MANAGER: ", message);
    
    //--- Send push notification if enabled
    SendNotification("KAIZEN Bot: " + message);
}

//+------------------------------------------------------------------+
//| Notify about margin issues                                     |
//+------------------------------------------------------------------+
void CRiskManager::NotifyMarginIssue()
{
    string message = "Margin level is low: " + DoubleToString(m_marginLevel, 1) + "%";
    Print("RISK MANAGER: ", message);
    
    if(m_marginLevel < 150)
    {
        SendNotification("KAIZEN Bot: WARNING - " + message);
    }
}

//+------------------------------------------------------------------+
//| Notify when cannot trade                                       |
//+------------------------------------------------------------------+
void CRiskManager::NotifyCannotTrade()
{
    string message = "Cannot execute trade - insufficient margin even with minimum risk";
    Print("RISK MANAGER: ", message);
    SendNotification("KAIZEN Bot: " + message);
}

//+------------------------------------------------------------------+
//| Generate risk report                                           |
//+------------------------------------------------------------------+
string CRiskManager::GetRiskReport()
{
    UpdateAccountInfo();
    
    string report = "\n=== RISK MANAGER REPORT ===\n";
    report += "Account Balance: " + DoubleToString(m_accountBalance, 2) + "\n";
    report += "Account Equity: " + DoubleToString(m_accountEquity, 2) + "\n";
    report += "Free Margin: " + DoubleToString(m_freeMargin, 2) + "\n";
    report += "Margin Level: " + DoubleToString(m_marginLevel, 1) + "%\n";
    report += "Current Risk: " + DoubleToString(m_currentRisk, 1) + "%\n";
    report += "Risk Amount: " + DoubleToString(CalculateRiskAmount(), 2) + "\n";
    report += "Auto Adjust: " + (m_autoAdjust ? "YES" : "NO") + "\n";
    report += "============================\n";
    
    return report;
}

//+------------------------------------------------------------------+
//| Reset risk to initial value                                    |
//+------------------------------------------------------------------+
void CRiskManager::ResetRisk()
{
    double oldRisk = m_currentRisk;
    m_currentRisk = m_initialRisk;
    
    if(oldRisk != m_currentRisk)
    {
        Print("Risk reset from ", oldRisk, "% to ", m_currentRisk, "%");
    }
}