//+------------------------------------------------------------------+
//|                                              ReportManager.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

#include "Utils.mqh"

//--- Statistics structures
struct STradingStatistics
{
    //--- General statistics
    int totalTrades;
    int winningTrades;
    int losingTrades;
    double winRate;
    
    //--- Financial statistics
    double totalProfit;
    double totalLoss;
    double netProfit;
    double profitFactor;
    double averageWin;
    double averageLoss;
    double averageTrade;
    
    //--- Risk statistics
    double maxDrawdown;
    double maxDrawdownPercent;
    double currentDrawdown;
    double maxConsecutiveLosses;
    double currentConsecutiveLosses;
    double maxConsecutiveWins;
    double currentConsecutiveWins;
    
    //--- Performance statistics
    double sharpeRatio;
    double sortinoRatio;
    double calmarRatio;
    double expectedPayoff;
    
    //--- Daily statistics
    int tradesToday;
    double profitToday;
    datetime lastResetDate;
    
    //--- Model performance
    double liquidityModelProfit;
    double fibonacciModelProfit;
    double fractalModelProfit;
    double orderBlockModelProfit;
    int liquidityModelTrades;
    int fibonacciModelTrades;
    int fractalModelTrades;
    int orderBlockModelTrades;
};

struct SDrawdownData
{
    double peak;
    double valley;
    double drawdown;
    datetime peakTime;
    datetime valleyTime;
    bool isActive;
};

struct STradeRecord
{
    ulong ticket;
    datetime openTime;
    datetime closeTime;
    double entryPrice;
    double exitPrice;
    double volume;
    double profit;
    string model;
    ENUM_SIGNAL_DIRECTION direction;
    string comment;
    bool isWin;
    double riskReward;
};

//+------------------------------------------------------------------+
//| Report Manager class                                           |
//+------------------------------------------------------------------+
class CReportManager
{
private:
    bool m_enableNotifications;
    bool m_enableEmailReports;
    
    //--- Statistics
    STradingStatistics m_stats;
    SDrawdownData m_drawdown;
    STradeRecord m_tradeHistory[];
    
    //--- Report scheduling
    datetime m_lastDailyReport;
    datetime m_lastWeeklyReport;
    datetime m_lastMonthlyReport;
    
    //--- Performance tracking
    double m_accountStartBalance;
    double m_accountPeakBalance;
    double m_dailyReturns[];
    
    //--- File handles
    string m_logFileName;
    string m_reportFileName;
    
public:
    //--- Constructor/Destructor
    CReportManager();
    ~CReportManager() {}
    
    //--- Initialization
    bool Init(bool enableNotifications, bool enableEmailReports);
    
    //--- Trade logging
    void LogTrade(const SEntrySignal &signal, ulong ticket, double volume);
    void LogTradeClose(ulong ticket, double exitPrice, double profit);
    void LogError(string errorMsg, int errorCode);
    
    //--- Statistics updates
    void UpdateStatistics();
    void UpdateDrawdown();
    void UpdateDailyStatistics();
    void UpdateModelStatistics(string model, double profit);
    
    //--- Report generation
    void GenerateInitReport();
    void GenerateFinalReport();
    void GenerateDailyReport();
    void GenerateWeeklyReport();
    void GenerateMonthlyReport();
    string GeneratePerformanceReport();
    string GenerateRiskReport();
    string GenerateModelReport();
    
    //--- Periodic tasks
    void UpdatePeriodicReports();
    void CheckScheduledReports();
    
    //--- Notifications
    void SendTradeNotification(string message);
    void SendPerformanceAlert(string message);
    void SendRiskAlert(string message);
    
    //--- File operations
    bool WriteToLogFile(string message);
    bool WriteReportToFile(string content, string fileName);
    void CreateBackupReport();
    
    //--- Getters
    STradingStatistics GetStatistics() const { return m_stats; }
    double GetCurrentDrawdown() const { return m_drawdown.drawdown; }
    double GetWinRate() const { return m_stats.winRate; }
    double GetProfitFactor() const { return m_stats.profitFactor; }
    int GetTradesToday() const { return m_stats.tradesToday; }
    
private:
    //--- Helper methods
    void InitializeStatistics();
    void CalculatePerformanceMetrics();
    void CalculateRiskMetrics();
    double CalculateSharpeRatio();
    double CalculateSortinoRatio();
    double CalculateCalmarRatio();
    string FormatDateTime(datetime dt);
    string FormatCurrency(double amount);
    void ResetDailyStatistics();
    bool ShouldSendNotification(string type);
};

//+------------------------------------------------------------------+
//| Constructor                                                     |
//+------------------------------------------------------------------+
CReportManager::CReportManager()
{
    m_enableNotifications = true;
    m_enableEmailReports = false;
    
    InitializeStatistics();
    
    m_lastDailyReport = 0;
    m_lastWeeklyReport = 0;
    m_lastMonthlyReport = 0;
    
    m_accountStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    m_accountPeakBalance = m_accountStartBalance;
    
    //--- Initialize drawdown tracking
    m_drawdown.peak = m_accountStartBalance;
    m_drawdown.valley = m_accountStartBalance;
    m_drawdown.drawdown = 0;
    m_drawdown.peakTime = TimeCurrent();
    m_drawdown.valleyTime = TimeCurrent();
    m_drawdown.isActive = false;
    
    //--- File names
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    string dateStr = StringFormat("%04d%02d%02d", dt.year, dt.mon, dt.day);
    m_logFileName = "KAIZEN_Log_" + dateStr + ".txt";
    m_reportFileName = "KAIZEN_Report_" + dateStr + ".txt";
    
    ArrayResize(m_tradeHistory, 0);
    ArrayResize(m_dailyReturns, 0);
}

//+------------------------------------------------------------------+
//| Initialize report manager                                      |
//+------------------------------------------------------------------+
bool CReportManager::Init(bool enableNotifications, bool enableEmailReports)
{
    m_enableNotifications = enableNotifications;
    m_enableEmailReports = enableEmailReports;
    
    //--- Create initial log entry
    WriteToLogFile("=== KAIZEN Professional Trading Bot Started ===");
    WriteToLogFile("Start Balance: " + FormatCurrency(m_accountStartBalance));
    WriteToLogFile("Notifications: " + (m_enableNotifications ? "ENABLED" : "DISABLED"));
    WriteToLogFile("Email Reports: " + (m_enableEmailReports ? "ENABLED" : "DISABLED"));
    
    Print("Report Manager initialized - Notifications: ", m_enableNotifications, " Email: ", m_enableEmailReports);
    return true;
}

//+------------------------------------------------------------------+
//| Log new trade                                                  |
//+------------------------------------------------------------------+
void CReportManager::LogTrade(const SEntrySignal &signal, ulong ticket, double volume)
{
    //--- Create trade record
    STradeRecord trade = {};
    trade.ticket = ticket;
    trade.openTime = TimeCurrent();
    trade.closeTime = 0;
    trade.entryPrice = signal.entryPrice;
    trade.exitPrice = 0;
    trade.volume = volume;
    trade.profit = 0;
    trade.model = signal.model;
    trade.direction = signal.direction;
    trade.comment = "Trade opened";
    trade.isWin = false;
    trade.riskReward = 0;
    
    //--- Add to history
    int size = ArraySize(m_tradeHistory);
    ArrayResize(m_tradeHistory, size + 1);
    m_tradeHistory[size] = trade;
    
    //--- Log to file
    string logMsg = StringFormat("TRADE OPENED: Ticket=%d, Model=%s, Direction=%s, Volume=%.2f, Entry=%.5f",
                                ticket, signal.model, EnumToString((ENUM_POSITION_TYPE)signal.direction), volume, signal.entryPrice);
    WriteToLogFile(logMsg);
    
    //--- Update statistics
    m_stats.totalTrades++;
    m_stats.tradesToday++;
    
    //--- Send notification
    if(m_enableNotifications)
    {
        string notification = StringFormat("Trade Opened: %s %s %.2f lots at %.5f", 
                                         signal.model, (signal.direction == SIGNAL_BUY ? "BUY" : "SELL"), volume, signal.entryPrice);
        SendTradeNotification(notification);
    }
}

//+------------------------------------------------------------------+
//| Log trade closure                                             |
//+------------------------------------------------------------------+
void CReportManager::LogTradeClose(ulong ticket, double exitPrice, double profit)
{
    //--- Find trade in history
    int index = -1;
    for(int i = 0; i < ArraySize(m_tradeHistory); i++)
    {
        if(m_tradeHistory[i].ticket == ticket && m_tradeHistory[i].closeTime == 0)
        {
            index = i;
            break;
        }
    }
    
    if(index < 0) return;
    
    //--- Update trade record
    m_tradeHistory[index].closeTime = TimeCurrent();
    m_tradeHistory[index].exitPrice = exitPrice;
    m_tradeHistory[index].profit = profit;
    m_tradeHistory[index].isWin = (profit > 0);
    
    if(m_tradeHistory[index].direction == SIGNAL_BUY)
        m_tradeHistory[index].riskReward = (exitPrice - m_tradeHistory[index].entryPrice) / (m_tradeHistory[index].entryPrice - exitPrice);
    else
        m_tradeHistory[index].riskReward = (m_tradeHistory[index].entryPrice - exitPrice) / (exitPrice - m_tradeHistory[index].entryPrice);
    
    //--- Update statistics
    if(profit > 0)
    {
        m_stats.winningTrades++;
        m_stats.totalProfit += profit;
        m_stats.currentConsecutiveWins++;
        m_stats.currentConsecutiveLosses = 0;
        if(m_stats.currentConsecutiveWins > m_stats.maxConsecutiveWins)
            m_stats.maxConsecutiveWins = m_stats.currentConsecutiveWins;
    }
    else
    {
        m_stats.losingTrades++;
        m_stats.totalLoss += MathAbs(profit);
        m_stats.currentConsecutiveLosses++;
        m_stats.currentConsecutiveWins = 0;
        if(m_stats.currentConsecutiveLosses > m_stats.maxConsecutiveLosses)
            m_stats.maxConsecutiveLosses = m_stats.currentConsecutiveLosses;
    }
    
    m_stats.profitToday += profit;
    UpdateModelStatistics(m_tradeHistory[index].model, profit);
    
    //--- Log to file
    string logMsg = StringFormat("TRADE CLOSED: Ticket=%d, Exit=%.5f, Profit=%.2f, R:R=%.2f",
                                ticket, exitPrice, profit, m_tradeHistory[index].riskReward);
    WriteToLogFile(logMsg);
    
    //--- Send notification
    if(m_enableNotifications)
    {
        string notification = StringFormat("Trade Closed: Ticket %d, P&L: %s%.2f", 
                                         ticket, (profit >= 0 ? "+" : ""), profit);
        SendTradeNotification(notification);
    }
    
    UpdateStatistics();
}

//+------------------------------------------------------------------+
//| Log error                                                     |
//+------------------------------------------------------------------+
void CReportManager::LogError(string errorMsg, int errorCode)
{
    string logMsg = StringFormat("ERROR [%d]: %s", errorCode, errorMsg);
    WriteToLogFile(logMsg);
    Print("REPORT MANAGER ERROR: ", logMsg);
}

//+------------------------------------------------------------------+
//| Update all statistics                                         |
//+------------------------------------------------------------------+
void CReportManager::UpdateStatistics()
{
    //--- Basic calculations
    if(m_stats.totalTrades > 0)
        m_stats.winRate = (double)m_stats.winningTrades / m_stats.totalTrades * 100.0;
    
    m_stats.netProfit = m_stats.totalProfit - m_stats.totalLoss;
    
    if(m_stats.totalLoss > 0)
        m_stats.profitFactor = m_stats.totalProfit / m_stats.totalLoss;
    else
        m_stats.profitFactor = (m_stats.totalProfit > 0) ? 999.99 : 0;
    
    if(m_stats.winningTrades > 0)
        m_stats.averageWin = m_stats.totalProfit / m_stats.winningTrades;
    
    if(m_stats.losingTrades > 0)
        m_stats.averageLoss = m_stats.totalLoss / m_stats.losingTrades;
    
    if(m_stats.totalTrades > 0)
        m_stats.averageTrade = m_stats.netProfit / m_stats.totalTrades;
    
    //--- Update drawdown
    UpdateDrawdown();
    
    //--- Calculate performance metrics
    CalculatePerformanceMetrics();
}

//+------------------------------------------------------------------+
//| Update drawdown statistics                                    |
//+------------------------------------------------------------------+
void CReportManager::UpdateDrawdown()
{
    double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    
    //--- Check for new peak
    if(currentBalance > m_drawdown.peak)
    {
        m_drawdown.peak = currentBalance;
        m_drawdown.peakTime = TimeCurrent();
        m_drawdown.isActive = false;
        
        if(currentBalance > m_accountPeakBalance)
            m_accountPeakBalance = currentBalance;
    }
    
    //--- Calculate current drawdown
    double currentDD = m_drawdown.peak - currentBalance;
    double currentDDPercent = (m_drawdown.peak > 0) ? (currentDD / m_drawdown.peak) * 100.0 : 0;
    
    //--- Update valley if in drawdown
    if(currentDD > 0)
    {
        m_drawdown.isActive = true;
        if(currentBalance < m_drawdown.valley || !m_drawdown.isActive)
        {
            m_drawdown.valley = currentBalance;
            m_drawdown.valleyTime = TimeCurrent();
        }
        
        //--- Update maximum drawdown
        if(currentDD > m_stats.maxDrawdown)
        {
            m_stats.maxDrawdown = currentDD;
            m_stats.maxDrawdownPercent = currentDDPercent;
        }
    }
    
    m_stats.currentDrawdown = currentDD;
    
    //--- Send risk alert if drawdown is significant
    if(currentDDPercent > 10.0 && ShouldSendNotification("RISK"))
    {
        SendRiskAlert(StringFormat("High Drawdown Alert: %.1f%% (%.2f)", currentDDPercent, currentDD));
    }
}

//+------------------------------------------------------------------+
//| Update daily statistics                                       |
//+------------------------------------------------------------------+
void CReportManager::UpdateDailyStatistics()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    MqlDateTime lastResetDt;
    TimeToStruct(m_stats.lastResetDate, lastResetDt);
    
    //--- Reset daily stats if new day
    if(dt.day != lastResetDt.day || dt.mon != lastResetDt.mon || dt.year != lastResetDt.year)
    {
        ResetDailyStatistics();
        m_stats.lastResetDate = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Update model statistics                                       |
//+------------------------------------------------------------------+
void CReportManager::UpdateModelStatistics(string model, double profit)
{
    if(model == "LIQUIDITY_SWEEP")
    {
        m_stats.liquidityModelProfit += profit;
        m_stats.liquidityModelTrades++;
    }
    else if(model == "FIBONACCI")
    {
        m_stats.fibonacciModelProfit += profit;
        m_stats.fibonacciModelTrades++;
    }
    else if(model == "FRACTAL")
    {
        m_stats.fractalModelProfit += profit;
        m_stats.fractalModelTrades++;
    }
    else if(model == "ORDER_BLOCK")
    {
        m_stats.orderBlockModelProfit += profit;
        m_stats.orderBlockModelTrades++;
    }
}

//+------------------------------------------------------------------+
//| Generate initialization report                                |
//+------------------------------------------------------------------+
void CReportManager::GenerateInitReport()
{
    string report = "\n=== KAIZEN TRADING BOT INITIALIZATION REPORT ===\n";
    report += "Date: " + FormatDateTime(TimeCurrent()) + "\n";
    report += "Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "\n";
    report += "Server: " + AccountInfoString(ACCOUNT_SERVER) + "\n";
    report += "Currency: " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
    report += "Starting Balance: " + FormatCurrency(m_accountStartBalance) + "\n";
    report += "Free Margin: " + FormatCurrency(AccountInfoDouble(ACCOUNT_FREEMARGIN)) + "\n";
    report += "Leverage: 1:" + IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + "\n";
    report += "Symbol: " + Symbol() + "\n";
    report += "Spread: " + DoubleToString(SymbolInfoInteger(Symbol(), SYMBOL_SPREAD), 1) + " points\n";
    report += "================================================\n";
    
    WriteToLogFile(report);
    Print(report);
}

//+------------------------------------------------------------------+
//| Generate final report                                         |
//+------------------------------------------------------------------+
void CReportManager::GenerateFinalReport()
{
    UpdateStatistics();
    
    string report = GeneratePerformanceReport();
    report += GenerateRiskReport();
    report += GenerateModelReport();
    
    WriteReportToFile(report, "KAIZEN_Final_Report_" + IntegerToString(TimeCurrent()) + ".txt");
    
    if(m_enableNotifications)
    {
        string summary = StringFormat("Bot Stopped. Total Trades: %d, Win Rate: %.1f%%, Net P&L: %s%.2f",
                                    m_stats.totalTrades, m_stats.winRate, (m_stats.netProfit >= 0 ? "+" : ""), m_stats.netProfit);
        SendPerformanceAlert(summary);
    }
}

//+------------------------------------------------------------------+
//| Generate daily report                                         |
//+------------------------------------------------------------------+
void CReportManager::GenerateDailyReport()
{
    UpdateStatistics();
    
    string report = "\n=== DAILY TRADING REPORT ===\n";
    report += "Date: " + FormatDateTime(TimeCurrent()) + "\n";
    report += "Trades Today: " + IntegerToString(m_stats.tradesToday) + "\n";
    report += "Profit Today: " + FormatCurrency(m_stats.profitToday) + "\n";
    report += "Current Balance: " + FormatCurrency(AccountInfoDouble(ACCOUNT_BALANCE)) + "\n";
    report += "Current Drawdown: " + FormatCurrency(m_stats.currentDrawdown) + "\n";
    report += "Total Trades: " + IntegerToString(m_stats.totalTrades) + "\n";
    report += "Win Rate: " + DoubleToString(m_stats.winRate, 1) + "%\n";
    report += "Profit Factor: " + DoubleToString(m_stats.profitFactor, 2) + "\n";
    report += "===========================\n";
    
    WriteToLogFile(report);
    
    if(m_enableNotifications && m_stats.tradesToday > 0)
    {
        string summary = StringFormat("Daily Summary: %d trades, P&L: %s%.2f, Win Rate: %.1f%%",
                                    m_stats.tradesToday, (m_stats.profitToday >= 0 ? "+" : ""), m_stats.profitToday, m_stats.winRate);
        SendPerformanceAlert(summary);
    }
}

//+------------------------------------------------------------------+
//| Generate weekly report                                        |
//+------------------------------------------------------------------+
void CReportManager::GenerateWeeklyReport()
{
    UpdateStatistics();
    
    string report = GeneratePerformanceReport();
    report += "\n=== WEEKLY SUMMARY ===\n";
    report += "Report Period: 7 days ending " + FormatDateTime(TimeCurrent()) + "\n";
    
    WriteReportToFile(report, "KAIZEN_Weekly_Report_" + IntegerToString(TimeCurrent()) + ".txt");
    
    if(m_enableEmailReports)
    {
        // Email functionality would be implemented here
        Print("Weekly report generated and ready for email");
    }
}

//+------------------------------------------------------------------+
//| Generate monthly report                                       |
//+------------------------------------------------------------------+
void CReportManager::GenerateMonthlyReport()
{
    UpdateStatistics();
    
    string report = GeneratePerformanceReport();
    report += GenerateRiskReport();
    report += GenerateModelReport();
    report += "\n=== MONTHLY SUMMARY ===\n";
    report += "Report Period: 30 days ending " + FormatDateTime(TimeCurrent()) + "\n";
    
    WriteReportToFile(report, "KAIZEN_Monthly_Report_" + IntegerToString(TimeCurrent()) + ".txt");
    
    if(m_enableEmailReports)
    {
        // Email functionality would be implemented here
        Print("Monthly report generated and ready for email");
    }
    
    CreateBackupReport();
}

//+------------------------------------------------------------------+
//| Generate performance report                                   |
//+------------------------------------------------------------------+
string CReportManager::GeneratePerformanceReport()
{
    UpdateStatistics();
    
    string report = "\n=== PERFORMANCE REPORT ===\n";
    report += "Total Trades: " + IntegerToString(m_stats.totalTrades) + "\n";
    report += "Winning Trades: " + IntegerToString(m_stats.winningTrades) + "\n";
    report += "Losing Trades: " + IntegerToString(m_stats.losingTrades) + "\n";
    report += "Win Rate: " + DoubleToString(m_stats.winRate, 1) + "%\n";
    report += "\nFinancial Performance:\n";
    report += "Total Profit: " + FormatCurrency(m_stats.totalProfit) + "\n";
    report += "Total Loss: " + FormatCurrency(m_stats.totalLoss) + "\n";
    report += "Net Profit: " + FormatCurrency(m_stats.netProfit) + "\n";
    report += "Profit Factor: " + DoubleToString(m_stats.profitFactor, 2) + "\n";
    report += "Average Win: " + FormatCurrency(m_stats.averageWin) + "\n";
    report += "Average Loss: " + FormatCurrency(m_stats.averageLoss) + "\n";
    report += "Average Trade: " + FormatCurrency(m_stats.averageTrade) + "\n";
    report += "\nPerformance Metrics:\n";
    report += "Sharpe Ratio: " + DoubleToString(m_stats.sharpeRatio, 2) + "\n";
    report += "Sortino Ratio: " + DoubleToString(m_stats.sortinoRatio, 2) + "\n";
    report += "Calmar Ratio: " + DoubleToString(m_stats.calmarRatio, 2) + "\n";
    report += "Expected Payoff: " + FormatCurrency(m_stats.expectedPayoff) + "\n";
    report += "==========================\n";
    
    return report;
}

//+------------------------------------------------------------------+
//| Generate risk report                                          |
//+------------------------------------------------------------------+
string CReportManager::GenerateRiskReport()
{
    string report = "\n=== RISK ANALYSIS REPORT ===\n";
    report += "Maximum Drawdown: " + FormatCurrency(m_stats.maxDrawdown) + " (" + DoubleToString(m_stats.maxDrawdownPercent, 1) + "%)\n";
    report += "Current Drawdown: " + FormatCurrency(m_stats.currentDrawdown) + "\n";
    report += "Maximum Consecutive Losses: " + IntegerToString((int)m_stats.maxConsecutiveLosses) + "\n";
    report += "Maximum Consecutive Wins: " + IntegerToString((int)m_stats.maxConsecutiveWins) + "\n";
    report += "Current Consecutive Losses: " + IntegerToString((int)m_stats.currentConsecutiveLosses) + "\n";
    report += "Current Consecutive Wins: " + IntegerToString((int)m_stats.currentConsecutiveWins) + "\n";
    report += "Account Peak Balance: " + FormatCurrency(m_accountPeakBalance) + "\n";
    report += "Current Balance: " + FormatCurrency(AccountInfoDouble(ACCOUNT_BALANCE)) + "\n";
    report += "Return from Start: " + DoubleToString(((AccountInfoDouble(ACCOUNT_BALANCE) - m_accountStartBalance) / m_accountStartBalance) * 100, 1) + "%\n";
    report += "===========================\n";
    
    return report;
}

//+------------------------------------------------------------------+
//| Generate model performance report                             |
//+------------------------------------------------------------------+
string CReportManager::GenerateModelReport()
{
    string report = "\n=== MODEL PERFORMANCE REPORT ===\n";
    
    if(m_stats.liquidityModelTrades > 0)
    {
        double avgProfit = m_stats.liquidityModelProfit / m_stats.liquidityModelTrades;
        report += "Liquidity Sweep Model:\n";
        report += "  Trades: " + IntegerToString(m_stats.liquidityModelTrades) + "\n";
        report += "  Total P&L: " + FormatCurrency(m_stats.liquidityModelProfit) + "\n";
        report += "  Average P&L: " + FormatCurrency(avgProfit) + "\n\n";
    }
    
    if(m_stats.fibonacciModelTrades > 0)
    {
        double avgProfit = m_stats.fibonacciModelProfit / m_stats.fibonacciModelTrades;
        report += "Fibonacci Model:\n";
        report += "  Trades: " + IntegerToString(m_stats.fibonacciModelTrades) + "\n";
        report += "  Total P&L: " + FormatCurrency(m_stats.fibonacciModelProfit) + "\n";
        report += "  Average P&L: " + FormatCurrency(avgProfit) + "\n\n";
    }
    
    if(m_stats.fractalModelTrades > 0)
    {
        double avgProfit = m_stats.fractalModelProfit / m_stats.fractalModelTrades;
        report += "Fractal Model:\n";
        report += "  Trades: " + IntegerToString(m_stats.fractalModelTrades) + "\n";
        report += "  Total P&L: " + FormatCurrency(m_stats.fractalModelProfit) + "\n";
        report += "  Average P&L: " + FormatCurrency(avgProfit) + "\n\n";
    }
    
    if(m_stats.orderBlockModelTrades > 0)
    {
        double avgProfit = m_stats.orderBlockModelProfit / m_stats.orderBlockModelTrades;
        report += "Order Block Model:\n";
        report += "  Trades: " + IntegerToString(m_stats.orderBlockModelTrades) + "\n";
        report += "  Total P&L: " + FormatCurrency(m_stats.orderBlockModelProfit) + "\n";
        report += "  Average P&L: " + FormatCurrency(avgProfit) + "\n\n";
    }
    
    report += "===============================\n";
    return report;
}

//+------------------------------------------------------------------+
//| Update periodic reports                                       |
//+------------------------------------------------------------------+
void CReportManager::UpdatePeriodicReports()
{
    UpdateDailyStatistics();
    UpdateDrawdown();
}

//+------------------------------------------------------------------+
//| Check for scheduled reports                                   |
//+------------------------------------------------------------------+
void CReportManager::CheckScheduledReports()
{
    datetime currentTime = TimeCurrent();
    MqlDateTime dt;
    TimeToStruct(currentTime, dt);
    
    //--- Daily report at 23:59
    if(dt.hour == 23 && dt.min >= 59 && currentTime - m_lastDailyReport > 3600)
    {
        GenerateDailyReport();
        m_lastDailyReport = currentTime;
    }
    
    //--- Weekly report on Sundays
    if(dt.day_of_week == 0 && dt.hour == 23 && currentTime - m_lastWeeklyReport > 86400 * 6)
    {
        GenerateWeeklyReport();
        m_lastWeeklyReport = currentTime;
    }
    
    //--- Monthly report on first day of month
    if(dt.day == 1 && dt.hour == 23 && currentTime - m_lastMonthlyReport > 86400 * 25)
    {
        GenerateMonthlyReport();
        m_lastMonthlyReport = currentTime;
    }
}

//+------------------------------------------------------------------+
//| Send trade notification                                       |
//+------------------------------------------------------------------+
void CReportManager::SendTradeNotification(string message)
{
    if(!m_enableNotifications) return;
    
    string fullMessage = "KAIZEN Bot: " + message;
    SendNotification(fullMessage);
}

//+------------------------------------------------------------------+
//| Send performance alert                                        |
//+------------------------------------------------------------------+
void CReportManager::SendPerformanceAlert(string message)
{
    if(!m_enableNotifications) return;
    
    string fullMessage = "KAIZEN Performance: " + message;
    SendNotification(fullMessage);
}

//+------------------------------------------------------------------+
//| Send risk alert                                              |
//+------------------------------------------------------------------+
void CReportManager::SendRiskAlert(string message)
{
    if(!m_enableNotifications) return;
    
    string fullMessage = "KAIZEN Risk Alert: " + message;
    SendNotification(fullMessage);
}

//+------------------------------------------------------------------+
//| Write message to log file                                    |
//+------------------------------------------------------------------+
bool CReportManager::WriteToLogFile(string message)
{
    int fileHandle = FileOpen(m_logFileName, FILE_WRITE | FILE_TXT | FILE_ANSI);
    if(fileHandle == INVALID_HANDLE)
        return false;
    
    FileSeek(fileHandle, 0, SEEK_END);
    FileWrite(fileHandle, FormatDateTime(TimeCurrent()) + " - " + message);
    FileClose(fileHandle);
    
    return true;
}

//+------------------------------------------------------------------+
//| Write report to file                                         |
//+------------------------------------------------------------------+
bool CReportManager::WriteReportToFile(string content, string fileName)
{
    int fileHandle = FileOpen(fileName, FILE_WRITE | FILE_TXT | FILE_ANSI);
    if(fileHandle == INVALID_HANDLE)
        return false;
    
    FileWrite(fileHandle, content);
    FileClose(fileHandle);
    
    return true;
}

//+------------------------------------------------------------------+
//| Create backup report                                         |
//+------------------------------------------------------------------+
void CReportManager::CreateBackupReport()
{
    string backupContent = GeneratePerformanceReport() + GenerateRiskReport() + GenerateModelReport();
    string backupFileName = "KAIZEN_Backup_" + IntegerToString(TimeCurrent()) + ".txt";
    WriteReportToFile(backupContent, backupFileName);
}

//+------------------------------------------------------------------+
//| Initialize statistics                                         |
//+------------------------------------------------------------------+
void CReportManager::InitializeStatistics()
{
    ZeroMemory(m_stats);
    m_stats.lastResetDate = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Calculate performance metrics                                 |
//+------------------------------------------------------------------+
void CReportManager::CalculatePerformanceMetrics()
{
    m_stats.sharpeRatio = CalculateSharpeRatio();
    m_stats.sortinoRatio = CalculateSortinoRatio();
    m_stats.calmarRatio = CalculateCalmarRatio();
    
    if(m_stats.totalTrades > 0)
    {
        double winProbability = (double)m_stats.winningTrades / m_stats.totalTrades;
        double lossProbability = (double)m_stats.losingTrades / m_stats.totalTrades;
        m_stats.expectedPayoff = (winProbability * m_stats.averageWin) - (lossProbability * m_stats.averageLoss);
    }
}

//+------------------------------------------------------------------+
//| Calculate Sharpe ratio                                       |
//+------------------------------------------------------------------+
double CReportManager::CalculateSharpeRatio()
{
    if(ArraySize(m_dailyReturns) < 2) return 0;
    
    //--- Calculate average return and standard deviation
    double sum = 0, sumSquares = 0;
    int count = ArraySize(m_dailyReturns);
    
    for(int i = 0; i < count; i++)
    {
        sum += m_dailyReturns[i];
        sumSquares += m_dailyReturns[i] * m_dailyReturns[i];
    }
    
    double avgReturn = sum / count;
    double variance = (sumSquares / count) - (avgReturn * avgReturn);
    double stdDev = MathSqrt(variance);
    
    return (stdDev > 0) ? avgReturn / stdDev : 0;
}

//+------------------------------------------------------------------+
//| Calculate Sortino ratio                                      |
//+------------------------------------------------------------------+
double CReportManager::CalculateSortinoRatio()
{
    if(ArraySize(m_dailyReturns) < 2) return 0;
    
    //--- Calculate downside deviation
    double sum = 0, downsideSum = 0;
    int count = ArraySize(m_dailyReturns);
    
    for(int i = 0; i < count; i++)
    {
        sum += m_dailyReturns[i];
        if(m_dailyReturns[i] < 0)
            downsideSum += m_dailyReturns[i] * m_dailyReturns[i];
    }
    
    double avgReturn = sum / count;
    double downsideDeviation = MathSqrt(downsideSum / count);
    
    return (downsideDeviation > 0) ? avgReturn / downsideDeviation : 0;
}

//+------------------------------------------------------------------+
//| Calculate Calmar ratio                                       |
//+------------------------------------------------------------------+
double CReportManager::CalculateCalmarRatio()
{
    if(m_stats.maxDrawdownPercent <= 0) return 0;
    
    double annualReturn = ((AccountInfoDouble(ACCOUNT_BALANCE) - m_accountStartBalance) / m_accountStartBalance) * 100;
    return annualReturn / m_stats.maxDrawdownPercent;
}

//+------------------------------------------------------------------+
//| Format datetime                                              |
//+------------------------------------------------------------------+
string CReportManager::FormatDateTime(datetime dt)
{
    MqlDateTime mdt;
    TimeToStruct(dt, mdt);
    return StringFormat("%04d.%02d.%02d %02d:%02d:%02d", mdt.year, mdt.mon, mdt.day, mdt.hour, mdt.min, mdt.sec);
}

//+------------------------------------------------------------------+
//| Format currency amount                                       |
//+------------------------------------------------------------------+
string CReportManager::FormatCurrency(double amount)
{
    string currency = AccountInfoString(ACCOUNT_CURRENCY);
    return DoubleToString(amount, 2) + " " + currency;
}

//+------------------------------------------------------------------+
//| Reset daily statistics                                       |
//+------------------------------------------------------------------+
void CReportManager::ResetDailyStatistics()
{
    //--- Store yesterday's return
    double yesterdayReturn = m_stats.profitToday;
    int size = ArraySize(m_dailyReturns);
    ArrayResize(m_dailyReturns, size + 1);
    m_dailyReturns[size] = yesterdayReturn;
    
    //--- Keep only last 252 days (trading year)
    if(ArraySize(m_dailyReturns) > 252)
        ArrayRemove(m_dailyReturns, 0, 1);
    
    //--- Reset daily counters
    m_stats.tradesToday = 0;
    m_stats.profitToday = 0;
}

//+------------------------------------------------------------------+
//| Check if should send notification of specific type           |
//+------------------------------------------------------------------+
bool CReportManager::ShouldSendNotification(string type)
{
    static datetime lastNotifications[];
    static string notificationTypes[];
    
    //--- Find notification type
    int index = -1;
    for(int i = 0; i < ArraySize(notificationTypes); i++)
    {
        if(notificationTypes[i] == type)
        {
            index = i;
            break;
        }
    }
    
    //--- Add new type if not found
    if(index == -1)
    {
        index = ArraySize(notificationTypes);
        ArrayResize(notificationTypes, index + 1);
        ArrayResize(lastNotifications, index + 1);
        notificationTypes[index] = type;
        lastNotifications[index] = 0;
    }
    
    //--- Check if enough time has passed (prevent spam)
    datetime currentTime = TimeCurrent();
    if(currentTime - lastNotifications[index] < 3600) // 1 hour minimum
        return false;
    
    lastNotifications[index] = currentTime;
    return true;
}