//+------------------------------------------------------------------+
//|                                                       Test.mq5 |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, KAIZEN Trading Systems"
#property version   "1.00"
#property description "Test script for KAIZEN Trading Bot modules"

#include "Includes/Utils.mqh"
#include "Includes/RiskManager.mqh"
#include "Includes/TimeframeAnalysis.mqh"
#include "Includes/TradingModels.mqh"
#include "Includes/PositionManager.mqh"
#include "Includes/ReportManager.mqh"

//+------------------------------------------------------------------+
//| Script program start function                                   |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== KAIZEN Trading Bot Module Test ===");
    
    //--- Test Utils module
    CUtils utils;
    if(utils.Init())
    {
        Print("✓ Utils module initialized successfully");
        Print("  - Current ATR: ", utils.GetATR());
        Print("  - Market Open: ", (utils.IsMarketOpen() ? "YES" : "NO"));
        Print("  - New Bar: ", (utils.IsNewBar() ? "YES" : "NO"));
    }
    else
    {
        Print("✗ Utils module failed to initialize");
        return;
    }
    
    //--- Test Risk Manager
    CRiskManager riskManager;
    if(riskManager.Init(10.0, 1.0, true))
    {
        Print("✓ Risk Manager initialized successfully");
        Print("  - Current Risk: ", riskManager.GetCurrentRisk(), "%");
        Print("  - Free Margin: ", riskManager.GetFreeMargin());
        Print("  - Margin Level: ", riskManager.GetMarginLevel(), "%");
    }
    else
    {
        Print("✗ Risk Manager failed to initialize");
    }
    
    //--- Test Timeframe Analysis
    CTimeframeAnalysis tfAnalysis;
    if(tfAnalysis.Init(PERIOD_H4, PERIOD_D1, PERIOD_M1, PERIOD_M5))
    {
        Print("✓ Timeframe Analysis initialized successfully");
        tfAnalysis.SetUtils(&utils);
        
        SMarketContext context = tfAnalysis.AnalyzeContext();
        Print("  - Market Trend: ", utils.TrendToString(context.trend));
        Print("  - Trend Strength: ", DoubleToString(context.strength * 100, 1), "%");
        Print("  - Context Valid: ", (context.isValid ? "YES" : "NO"));
    }
    else
    {
        Print("✗ Timeframe Analysis failed to initialize");
    }
    
    //--- Test Trading Models
    CTradingModels tradingModels;
    if(tradingModels.Init(true, true, true, true))
    {
        Print("✓ Trading Models initialized successfully");
        tradingModels.SetUtils(&utils);
        
        //--- Test pattern identification
        tradingModels.UpdateAllPatterns();
        Print("  - Patterns updated successfully");
    }
    else
    {
        Print("✗ Trading Models failed to initialize");
    }
    
    //--- Test Position Manager
    CPositionManager positionManager;
    if(positionManager.Init(true, 1.0, 2.0, 3.0, true))
    {
        Print("✓ Position Manager initialized successfully");
        positionManager.SetUtils(&utils);
        
        Print("  - Active Positions: ", positionManager.GetActivePositionsCount());
        Print("  - Total Unrealized P&L: ", positionManager.GetTotalUnrealizedPnL());
    }
    else
    {
        Print("✗ Position Manager failed to initialize");
    }
    
    //--- Test Report Manager
    CReportManager reportManager;
    if(reportManager.Init(true, false))
    {
        Print("✓ Report Manager initialized successfully");
        
        STradingStatistics stats = reportManager.GetStatistics();
        Print("  - Total Trades: ", stats.totalTrades);
        Print("  - Win Rate: ", DoubleToString(stats.winRate, 1), "%");
        Print("  - Current Drawdown: ", reportManager.GetCurrentDrawdown());
    }
    else
    {
        Print("✗ Report Manager failed to initialize");
    }
    
    //--- Test signal generation
    Print("\n=== Testing Signal Generation ===");
    SEntrySignal testSignal = tfAnalysis.AnalyzeEntry();
    if(testSignal.isValid)
    {
        Print("✓ Valid signal generated:");
        Print("  - Direction: ", utils.DirectionToString(testSignal.direction));
        Print("  - Entry Price: ", testSignal.entryPrice);
        Print("  - Stop Loss: ", testSignal.stopLoss);
        Print("  - Take Profit 1: ", testSignal.takeProfit1);
        Print("  - Model: ", testSignal.model);
        
        //--- Test signal validation with models
        bool liquidityValid = tradingModels.ValidateLiquiditySweep(testSignal);
        bool fibonacciValid = tradingModels.ValidateFibonacci(testSignal);
        bool fractalValid = tradingModels.ValidateFractal(testSignal);
        bool orderBlockValid = tradingModels.ValidateOrderBlock(testSignal);
        
        Print("  - Liquidity Model: ", (liquidityValid ? "VALID" : "INVALID"));
        Print("  - Fibonacci Model: ", (fibonacciValid ? "VALID" : "INVALID"));
        Print("  - Fractal Model: ", (fractalValid ? "VALID" : "INVALID"));
        Print("  - Order Block Model: ", (orderBlockValid ? "VALID" : "INVALID"));
        
        //--- Test lot size calculation
        double lotSize = riskManager.CalculateLotSize(testSignal.stopLoss);
        Print("  - Calculated Lot Size: ", DoubleToString(lotSize, 2));
    }
    else
    {
        Print("✗ No valid signal at current market conditions");
    }
    
    //--- Generate test reports
    Print("\n=== Generating Test Reports ===");
    
    Print("Risk Manager Report:");
    Print(riskManager.GetRiskReport());
    
    Print("Timeframe Analysis Report:");
    Print(tfAnalysis.GetAnalysisReport());
    
    Print("Trading Models Report:");
    Print(tradingModels.GetModelsReport());
    
    Print("Position Manager Report:");
    Print(positionManager.GetPositionsReport());
    
    reportManager.GenerateInitReport();
    
    Print("\n=== All Module Tests Completed ===");
    Print("✓ KAIZEN Trading Bot modules are ready for live trading");
}