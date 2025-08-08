# KAIZEN BOT 1.0 (MetaTrader 5)

Este paquete contiene el EA principal y todos los módulos necesarios para compilar y usar el bot en MT5.

## Estructura
- ProfessionalTradingBot.mq5
- Test.mq5
- Includes/
  - Configuration.mqh
  - Utils.mqh
  - RiskManager.mqh
  - TimeframeAnalysis.mqh
  - TradingModels.mqh
  - PositionManager.mqh
  - ReportManager.mqh

Los includes se referencian con rutas relativas ("Includes/...") y deben mantenerse dentro de esta carpeta.

## Instalación
1. En MetaTrader 5: File > Open Data Folder.
2. Copia la carpeta "KAIZEN BOT 1.0" en MQL5/Experts/.
3. Abre MetaEditor y compila "KAIZEN BOT 1.0/ProfessionalTradingBot.mq5".
4. (Opcional) Ejecuta "KAIZEN BOT 1.0/Test.mq5" como script para validar módulos.

## Inputs principales del EA
- Gestión de Riesgo: InpInitialRisk, InpMinRisk, InpAutoAdjustRisk
- Timeframes: InpContextTF1/2, InpEntryTF1/2
- Modelos: InpUseLiquiditySweeps, InpUseFibonacci, InpUseFractals, InpUseOrderBlocks
- Gestión de Posiciones: InpUseTP3, InpTP1Ratio/2/3, InpMoveSLToTP2
- Validación: InpVolatilityMultiplier, InpConfirmationBars
- Reporting: InpEnableNotifications, InpEnableEmailReports, InpDrawVisualIndicators

## Notas
- Compilar siempre ProfessionalTradingBot.mq5 desde esta carpeta para que los includes relativos funcionen.
- Recomendado probar en demo antes de operar en real.