//+------------------------------------------------------------------+
//|                                              Configuration.mqh |
//|                             Copyright 2024, KAIZEN Trading Systems |
//+------------------------------------------------------------------+

#property copyright "Copyright 2024, KAIZEN Trading Systems"

//+------------------------------------------------------------------+
//| KAIZEN Professional Trading Bot Configuration                   |
//+------------------------------------------------------------------+

//--- Version Information
#define BOT_VERSION "1.00"
#define BOT_NAME "KAIZEN Professional Trading Bot"
#define BOT_COPYRIGHT "Copyright 2024, KAIZEN Trading Systems"

//--- Default Risk Settings
#define DEFAULT_INITIAL_RISK 10.0
#define DEFAULT_MIN_RISK 1.0
#define DEFAULT_MAX_RISK 20.0

//--- Default Timeframe Settings
#define DEFAULT_CONTEXT_TF1 PERIOD_H4
#define DEFAULT_CONTEXT_TF2 PERIOD_D1
#define DEFAULT_ENTRY_TF1 PERIOD_M1
#define DEFAULT_ENTRY_TF2 PERIOD_M5

//--- Default TP/SL Ratios
#define DEFAULT_TP1_RATIO 1.0
#define DEFAULT_TP2_RATIO 2.0
#define DEFAULT_TP3_RATIO 3.0

//--- Trading Model Settings
#define FIBONACCI_KEY_LEVELS {0.5, 0.618} // Focus on 50% and 61.8% levels
#define FRACTAL_TIMEFRAMES {PERIOD_M1, PERIOD_M5, PERIOD_M15}
#define MAX_LIQUIDITY_LEVELS 50
#define MAX_ORDER_BLOCKS 20

//--- Risk Limits
#define MAX_CONCURRENT_TRADES 5
#define MAX_DAILY_TRADES 20
#define MAX_DRAWDOWN_PERCENT 15.0
#define EMERGENCY_STOP_DRAWDOWN 20.0

//--- Volatility Settings
#define VOLATILITY_THRESHOLD 1.5
#define HIGH_VOLATILITY_MULTIPLIER 2.0
#define ATR_PERIOD 14

//--- Position Management
#define PARTIAL_CLOSE_TP1 33.0 // 33% at TP1
#define PARTIAL_CLOSE_TP2 50.0 // 50% of remaining at TP2
#define BREAKEVEN_BUFFER_POINTS 5
#define TP2_BUFFER_POINTS 10

//--- Notification Settings
#define NOTIFICATION_COOLDOWN 3600 // 1 hour between similar notifications
#define MAX_NOTIFICATIONS_PER_HOUR 10

//--- File Settings
#define LOG_FILE_MAX_SIZE 10485760 // 10MB
#define BACKUP_INTERVAL 604800 // 1 week
#define REPORT_RETENTION_DAYS 90

//--- Trading Session Settings (GMT hours)
#define TRADING_START_HOUR 8
#define TRADING_END_HOUR 22

//--- Magic Number Base (YYYYMMDD format)
#define MAGIC_NUMBER_BASE 20241203

//--- Error Handling
#define MAX_RETRIES 3
#define RETRY_DELAY 1000 // 1 second

//--- Performance Optimization
#define PATTERN_UPDATE_INTERVAL 300 // 5 minutes
#define STATISTICS_UPDATE_INTERVAL 60 // 1 minute
#define VOLATILITY_UPDATE_INTERVAL 3600 // 1 hour

//--- Symbol Validation
#define MIN_SYMBOL_SPREAD 20 // Maximum spread in points
#define MIN_SYMBOL_VOLUME 0.01 // Minimum lot size

//--- Color Scheme for Visual Indicators
#define COLOR_BUY_ARROW clrBlue
#define COLOR_SELL_ARROW clrRed
#define COLOR_SL_LINE clrRed
#define COLOR_TP1_LINE clrGreen
#define COLOR_TP2_LINE clrLimeGreen
#define COLOR_TP3_LINE clrForestGreen
#define COLOR_TEXT_LABEL clrWhite

//--- Line Styles
#define STYLE_SL STYLE_DASH
#define STYLE_TP1 STYLE_DASH
#define STYLE_TP2 STYLE_DOT
#define STYLE_TP3 STYLE_DASHDOT
#define LINE_WIDTH 1

//--- Arrow Codes
#define ARROW_BUY 233
#define ARROW_SELL 234

//--- Font Settings
#define LABEL_FONT "Arial"
#define LABEL_FONT_SIZE 8

//--- Transparency
#define LINE_TRANSPARENCY 128 // 50% transparency (0-255 scale)

//--- Model Names
#define MODEL_LIQUIDITY "LIQUIDITY_SWEEP"
#define MODEL_FIBONACCI "FIBONACCI"
#define MODEL_FRACTAL "FRACTAL"
#define MODEL_ORDER_BLOCK "ORDER_BLOCK"
#define MODEL_MTF_ANALYSIS "MTF_ANALYSIS"

//--- Report Template Headers
#define REPORT_HEADER_PERFORMANCE "=== PERFORMANCE REPORT ==="
#define REPORT_HEADER_RISK "=== RISK ANALYSIS REPORT ==="
#define REPORT_HEADER_MODELS "=== MODEL PERFORMANCE REPORT ==="
#define REPORT_HEADER_DAILY "=== DAILY TRADING REPORT ==="
#define REPORT_HEADER_WEEKLY "=== WEEKLY SUMMARY ==="
#define REPORT_HEADER_MONTHLY "=== MONTHLY SUMMARY ==="

//--- Validation Macros
#define IS_VALID_RISK(risk) (risk > 0 && risk <= DEFAULT_MAX_RISK)
#define IS_VALID_RATIO(ratio) (ratio > 0 && ratio <= 10.0)
#define IS_VALID_TIMEFRAME(tf) (tf >= PERIOD_M1 && tf <= PERIOD_MN1)

//--- Utility Functions
bool IsMarketHours()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    return (dt.hour >= TRADING_START_HOUR && dt.hour <= TRADING_END_HOUR);
}

string GetBotVersion()
{
    return BOT_VERSION;
}

string GetBotName()
{
    return BOT_NAME;
}

int GetMagicNumber()
{
    return MAGIC_NUMBER_BASE;
}

//--- Debug and Development Settings
#ifdef _DEBUG
    #define DEBUG_PRINT(msg) Print("[DEBUG] ", msg)
    #define VERBOSE_LOGGING true
#else
    #define DEBUG_PRINT(msg)
    #define VERBOSE_LOGGING false
#endif

//--- Optimization Settings for Different Account Types
struct SAccountSettings
{
    double minBalance;
    double maxRisk;
    int maxTrades;
    bool allowHighFrequency;
};

// Conservative settings for small accounts
const SAccountSettings CONSERVATIVE_SETTINGS = {1000, 5.0, 3, false};

// Standard settings for medium accounts  
const SAccountSettings STANDARD_SETTINGS = {10000, 10.0, 5, true};

// Aggressive settings for large accounts
const SAccountSettings AGGRESSIVE_SETTINGS = {100000, 15.0, 10, true};

SAccountSettings GetRecommendedSettings()
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    
    if(balance < 10000)
        return CONSERVATIVE_SETTINGS;
    else if(balance < 100000)
        return STANDARD_SETTINGS;
    else
        return AGGRESSIVE_SETTINGS;
}