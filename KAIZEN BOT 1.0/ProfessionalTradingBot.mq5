//+------------------------------------------------------------------+
//|                                        ProfessionalTradingBot.mq5 |
//|                             Copyright 2024, KAIZEN Trading Systems |
//|                                              https://kaizen-trading.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, KAIZEN Trading Systems"
#property link      "https://kaizen-trading.com"
#property version   "1.00"
#property description "Professional MetaTrader 5 Trading Bot with Advanced Risk Management"

//--- Include necessary modules
#include "Includes/Configuration.mqh"
#include "Includes/RiskManager.mqh"
#include "Includes/TimeframeAnalysis.mqh"
#include "Includes/TradingModels.mqh"
#include "Includes/PositionManager.mqh"
#include "Includes/ReportManager.mqh"
#include "Includes/Utils.mqh"

//--- Input parameters
input group "=== RISK MANAGEMENT ==="
input double   InpInitialRisk = 10.0;        // Initial Risk Percentage
input double   InpMinRisk = 1.0;             // Minimum Risk Percentage
input bool     InpAutoAdjustRisk = true;     // Auto Adjust Risk on Margin Issues

input group "=== TIMEFRAME SETTINGS ==="
input ENUM_TIMEFRAMES InpContextTF1 = PERIOD_H4;   // Primary Context Timeframe
input ENUM_TIMEFRAMES InpContextTF2 = PERIOD_D1;   // Secondary Context Timeframe
input ENUM_TIMEFRAMES InpEntryTF1 = PERIOD_M1;     // Primary Entry Timeframe
input ENUM_TIMEFRAMES InpEntryTF2 = PERIOD_M5;     // Secondary Entry Timeframe

input group "=== TRADING MODELS ==="
input bool     InpUseLiquiditySweeps = true;    // Use Liquidity Sweep Model
input bool     InpUseFibonacci = true;          // Use Fibonacci Retracement Model
input bool     InpUseFractals = true;           // Use Fractal Model
input bool     InpUseOrderBlocks = true;        // Use Order Block Model

input group "=== POSITION MANAGEMENT ==="
input bool     InpUseTP3 = true;                // Use Triple Take Profit
input double   InpTP1Ratio = 1.0;               // TP1 Risk:Reward Ratio
input double   InpTP2Ratio = 2.0;               // TP2 Risk:Reward Ratio
input double   InpTP3Ratio = 3.0;               // TP3 Risk:Reward Ratio
input bool     InpMoveSLToTP2 = true;           // Move SL to TP2 when TP2 hit

input group "=== VALIDATION SETTINGS ==="
input double   InpVolatilityMultiplier = 1.5;   // SL Volatility Multiplier
input int      InpConfirmationBars = 2;         // Confirmation Bars Required

input group "=== REPORTING ==="
input bool     InpEnableNotifications = true;   // Enable Push Notifications
input bool     InpEnableEmailReports = false;   // Enable Email Reports
input bool     InpDrawVisualIndicators = true;  // Draw Visual Indicators

//--- Global variables
CRiskManager      g_riskManager;
CTimeframeAnalysis g_tfAnalysis;
CTradingModels    g_tradingModels;
CPositionManager  g_positionManager;
CReportManager    g_reportManager;
CUtils            g_utils;

//--- EA identification
const string EA_NAME = "ProfessionalTradingBot";
const string EA_VERSION = "1.00";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== KAIZEN Professional Trading Bot v" + EA_VERSION + " ===");
    Print("Initializing Professional Trading Bot...");
    
    //--- Initialize all modules
    if(!InitializeModules())
    {
        Print("ERROR: Failed to initialize modules");
        return INIT_FAILED;
    }
    
    //--- Set up visual indicators if enabled
    if(InpDrawVisualIndicators)
    {
        SetupVisualIndicators();
    }
    
    //--- Generate initialization report
    g_reportManager.GenerateInitReport();
    
    Print("Professional Trading Bot initialized successfully!");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("Deinitializing Professional Trading Bot...");
    
    //--- Generate final report
    g_reportManager.GenerateFinalReport();
    
    //--- Cleanup visual indicators
    if(InpDrawVisualIndicators)
    {
        CleanupVisualIndicators();
    }
    
    Print("Professional Trading Bot deinitialized. Reason: " + IntegerToString(reason));
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    //--- Update current market data
    g_utils.UpdateMarketData();
    
    //--- Check for new signals only on new bar
    if(!g_utils.IsNewBar())
        return;
    
    //--- Update position management for existing positions
    g_positionManager.UpdatePositions();
    
    //--- Analyze market conditions
    if(!AnalyzeMarketConditions())
        return;
    
    //--- Look for trading opportunities
    SearchTradingOpportunities();
    
    //--- Update reports and statistics
    g_reportManager.UpdateStatistics();
}

//+------------------------------------------------------------------+
//| Initialize all trading modules                                   |
//+------------------------------------------------------------------+
bool InitializeModules()
{
    //--- Initialize Risk Manager
    if(!g_riskManager.Init(InpInitialRisk, InpMinRisk, InpAutoAdjustRisk))
    {
        Print("Failed to initialize Risk Manager");
        return false;
    }
    
    //--- Initialize Timeframe Analysis
    if(!g_tfAnalysis.Init(InpContextTF1, InpContextTF2, InpEntryTF1, InpEntryTF2))
    {
        Print("Failed to initialize Timeframe Analysis");
        return false;
    }
    
    //--- Initialize Trading Models
    if(!g_tradingModels.Init(InpUseLiquiditySweeps, InpUseFibonacci, InpUseFractals, InpUseOrderBlocks))
    {
        Print("Failed to initialize Trading Models");
        return false;
    }
    
    //--- Initialize Position Manager
    if(!g_positionManager.Init(InpUseTP3, InpTP1Ratio, InpTP2Ratio, InpTP3Ratio, InpMoveSLToTP2))
    {
        Print("Failed to initialize Position Manager");
        return false;
    }
    
    //--- Initialize Report Manager
    if(!g_reportManager.Init(InpEnableNotifications, InpEnableEmailReports))
    {
        Print("Failed to initialize Report Manager");
        return false;
    }
    
    //--- Initialize Utils
    if(!g_utils.Init())
    {
        Print("Failed to initialize Utils");
        return false;
    }
    
    //--- Set utils reference for all modules
    g_tfAnalysis.SetUtils(&g_utils);
    g_tradingModels.SetUtils(&g_utils);
    g_positionManager.SetUtils(&g_utils);
    g_positionManager.SetVolatilityMultiplier(InpVolatilityMultiplier);
    
    return true;
}

//+------------------------------------------------------------------+
//| Analyze current market conditions                               |
//+------------------------------------------------------------------+
bool AnalyzeMarketConditions()
{
    //--- Check if market is open
    if(!g_utils.IsMarketOpen())
        return false;
    
    //--- Analyze higher timeframes for context
    SMarketContext context = g_tfAnalysis.AnalyzeContext();
    
    //--- Check if context is favorable for trading
    if(context.trend == TREND_UNDEFINED || context.strength < 0.5)
        return false;
    
    //--- Check volatility conditions
    if(!g_utils.IsVolatilityFavorable(InpVolatilityMultiplier))
        return false;
    
    return true;
}

//+------------------------------------------------------------------+
//| Search for trading opportunities                                |
//+------------------------------------------------------------------+
void SearchTradingOpportunities()
{
    //--- Get entry signals from lower timeframes
    SEntrySignal entrySignal = g_tfAnalysis.AnalyzeEntry();
    
    if(entrySignal.isValid)
    {
        //--- Validate signal with trading models
        if(ValidateSignalWithModels(entrySignal))
        {
            //--- Calculate position size based on risk
            double lotSize = g_riskManager.CalculateLotSize(entrySignal.stopLoss);
            
            if(lotSize > 0)
            {
                //--- Execute trade
                ExecuteTrade(entrySignal, lotSize);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Validate signal with trading models                             |
//+------------------------------------------------------------------+
bool ValidateSignalWithModels(const SEntrySignal &signal)
{
    int validationCount = 0;
    
    //--- Check liquidity sweep model
    if(InpUseLiquiditySweeps && g_tradingModels.ValidateLiquiditySweep(signal))
        validationCount++;
    
    //--- Check Fibonacci model
    if(InpUseFibonacci && g_tradingModels.ValidateFibonacci(signal))
        validationCount++;
    
    //--- Check fractal model
    if(InpUseFractals && g_tradingModels.ValidateFractal(signal))
        validationCount++;
    
    //--- Check order block model
    if(InpUseOrderBlocks && g_tradingModels.ValidateOrderBlock(signal))
        validationCount++;
    
    //--- Require at least one model validation
    return validationCount > 0;
}

//+------------------------------------------------------------------+
//| Execute trade based on validated signal                         |
//+------------------------------------------------------------------+
void ExecuteTrade(const SEntrySignal &signal, double lotSize)
{
    //--- Create trade request
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = Symbol();
    request.volume = lotSize;
    request.type = signal.direction == SIGNAL_BUY ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
    request.price = signal.direction == SIGNAL_BUY ? SymbolInfoDouble(Symbol(), SYMBOL_ASK) : SymbolInfoDouble(Symbol(), SYMBOL_BID);
    request.sl = signal.stopLoss;
    request.tp = signal.takeProfit1; // Initial TP
    request.magic = GetMagicNumber();
    request.comment = "KAIZEN_" + signal.model;
    
    //--- Send order
    if(OrderSend(request, result))
    {
        //--- Register position for management
        g_positionManager.RegisterPosition(result.deal, signal);
        
        //--- Draw visual indicators
        if(InpDrawVisualIndicators)
        {
            DrawTradeIndicators(signal, result.deal);
        }
        
        //--- Send notification
        if(InpEnableNotifications)
        {
            SendNotification("New " + signal.model + " trade opened: " + Symbol() + " " + 
                           (signal.direction == SIGNAL_BUY ? "BUY" : "SELL") + " " + 
                           DoubleToString(lotSize, 2) + " lots");
        }
        
        //--- Log trade
        g_reportManager.LogTrade(signal, result.deal, lotSize);
    }
    else
    {
        Print("Trade execution failed. Error: " + IntegerToString(GetLastError()));
        g_reportManager.LogError("Trade execution failed", GetLastError());
    }
}

//+------------------------------------------------------------------+
//| Setup visual indicators                                          |
//+------------------------------------------------------------------+
void SetupVisualIndicators()
{
    //--- Set up chart properties for transparent lines
    ChartSetInteger(0, CHART_FOREGROUND, false);
    ChartRedraw();
}

//+------------------------------------------------------------------+
//| Cleanup visual indicators                                        |
//+------------------------------------------------------------------+
void CleanupVisualIndicators()
{
    //--- Remove all objects created by the EA
    ObjectsDeleteAll(0, EA_NAME);
    ChartRedraw();
}

//+------------------------------------------------------------------+
//| Draw trade indicators on chart                                  |
//+------------------------------------------------------------------+
void DrawTradeIndicators(const SEntrySignal &signal, ulong ticket)
{
    string prefix = EA_NAME + "_" + IntegerToString(ticket) + "_";
    datetime currentTime = TimeCurrent();
    
    //--- Draw entry arrow
    string arrowName = prefix + "Entry";
    ObjectCreate(0, arrowName, OBJ_ARROW, 0, currentTime, signal.entryPrice);
    ObjectSetInteger(0, arrowName, OBJPROP_ARROWCODE, signal.direction == SIGNAL_BUY ? 233 : 234);
    ObjectSetInteger(0, arrowName, OBJPROP_COLOR, signal.direction == SIGNAL_BUY ? clrBlue : clrRed);
    ObjectSetInteger(0, arrowName, OBJPROP_WIDTH, 3);
    
    //--- Draw SL line
    string slName = prefix + "SL";
    ObjectCreate(0, slName, OBJ_HLINE, 0, 0, signal.stopLoss);
    ObjectSetInteger(0, slName, OBJPROP_COLOR, clrRed);
    ObjectSetInteger(0, slName, OBJPROP_STYLE, STYLE_DASH);
    ObjectSetInteger(0, slName, OBJPROP_WIDTH, 1);
    ObjectSetInteger(0, slName, OBJPROP_BACK, false);
    
    //--- Draw TP lines
    string tp1Name = prefix + "TP1";
    ObjectCreate(0, tp1Name, OBJ_HLINE, 0, 0, signal.takeProfit1);
    ObjectSetInteger(0, tp1Name, OBJPROP_COLOR, clrGreen);
    ObjectSetInteger(0, tp1Name, OBJPROP_STYLE, STYLE_DASH);
    ObjectSetInteger(0, tp1Name, OBJPROP_WIDTH, 1);
    ObjectSetInteger(0, tp1Name, OBJPROP_BACK, false);
    
    if(signal.takeProfit2 > 0)
    {
        string tp2Name = prefix + "TP2";
        ObjectCreate(0, tp2Name, OBJ_HLINE, 0, 0, signal.takeProfit2);
        ObjectSetInteger(0, tp2Name, OBJPROP_COLOR, clrGreen);
        ObjectSetInteger(0, tp2Name, OBJPROP_STYLE, STYLE_DOT);
        ObjectSetInteger(0, tp2Name, OBJPROP_WIDTH, 1);
        ObjectSetInteger(0, tp2Name, OBJPROP_BACK, false);
    }
    
    if(signal.takeProfit3 > 0)
    {
        string tp3Name = prefix + "TP3";
        ObjectCreate(0, tp3Name, OBJ_HLINE, 0, 0, signal.takeProfit3);
        ObjectSetInteger(0, tp3Name, OBJPROP_COLOR, clrGreen);
        ObjectSetInteger(0, tp3Name, OBJPROP_STYLE, STYLE_DASHDOT);
        ObjectSetInteger(0, tp3Name, OBJPROP_WIDTH, 1);
        ObjectSetInteger(0, tp3Name, OBJPROP_BACK, false);
    }
    
    //--- Draw model label
    string labelName = prefix + "Label";
    ObjectCreate(0, labelName, OBJ_TEXT, 0, currentTime, signal.entryPrice);
    ObjectSetString(0, labelName, OBJPROP_TEXT, signal.model);
    ObjectSetInteger(0, labelName, OBJPROP_COLOR, clrWhite);
    ObjectSetInteger(0, labelName, OBJPROP_FONTSIZE, 8);
    ObjectSetString(0, labelName, OBJPROP_FONT, "Arial");
    
    ChartRedraw();
}

//+------------------------------------------------------------------+
//| Get magic number for EA identification                          |
//+------------------------------------------------------------------+
int GetMagicNumber()
{
    return 20241203; // YYYYMMDD format
}

//+------------------------------------------------------------------+
//| Timer function for periodic tasks                               |
//+------------------------------------------------------------------+
void OnTimer()
{
    //--- Update reports
    g_reportManager.UpdatePeriodicReports();
    
    //--- Check for weekly/monthly reports
    g_reportManager.CheckScheduledReports();
}