# KAIZEN - Advanced Trading Strategy para TradingView

## Descripción

Este script de Pine Script implementa una estrategia de trading avanzada basada en el análisis de patrones de precio y acción del precio, diseñada para reflejar las estrategias de trading de MetaTrader 5. El script identifica múltiples patrones de mercado y proporciona señales de entrada y salida precisas.

## Características Principales

### 🔺 Patrones Reconocidos

1. **Sacadas de Liquidez (Liquidity Sweeps)**
   - Detecta breakouts falsos que atrapan a traders
   - Identifica reversiones después de la sacada de liquidez
   - Configurable mediante sensibilidad de porcentaje

2. **Retrocesos de Fibonacci (50%-100%)**
   - Niveles configurables: 38.2%, 50%, 61.8%, 78.6%
   - Cálculo automático basado en fractales recientes
   - Alertas cuando el precio se acerca a niveles clave

3. **Fractales Menores (1-15 min)**
   - Identificación automática de puntos de giro
   - Longitud configurable del fractal
   - Timeframe personalizable para análisis

4. **Order Blocks Vírgenes**
   - Detecta zonas de alto volumen no re-testeadas
   - Filtra por volumen mínimo configurable
   - Identifica tanto order blocks alcistas como bajistas

### 🎨 Visualización

- **Líneas y Zonas**: Retrocesos de Fibonacci claramente marcados
- **Cajas de Order Blocks**: Zonas destacadas con transparencia
- **Marcadores de Fractales**: Símbolos ▲▼ para puntos de giro
- **Etiquetas de Patrones**: Identificación clara de cada patrón
- **Señales de Entrada**: Indicadores 🟢 COMPRA / 🔴 VENTA
- **Modelo Operativo**: Estado actual del mercado mostrado

### 🔔 Sistema de Alertas

- Alertas automáticas para señales de entrada/salida
- Notificaciones cuando se detectan sacadas de liquidez
- Alertas para niveles de Fibonacci alcanzados
- Alertas para formación de nuevos patrones

### ⚙️ Configuración Dinámica

#### Configuración General
- Activar/desactivar patrones individuales
- Control de visualización de estadísticas
- Activación de alertas

#### Parámetros de Fibonacci
- Niveles personalizables (38.2%, 50%, 61.8%, 78.6%)
- Lookback period ajustable
- Tolerancia de precios configurable

#### Configuración de Fractales
- Longitud del fractal (3-15 períodos)
- Timeframe de análisis personalizable
- Sensibilidad de detección

#### Order Blocks
- Período de búsqueda (lookback)
- Multiplicador de volumen mínimo
- Filtros de validación

#### Sacadas de Liquidez
- Sensibilidad de detección (%)
- Período de análisis
- Tolerancia de breakout

### 📊 Estadísticas en Tiempo Real

El script muestra una tabla con:
- Total de patrones identificados
- Contador de fractales detectados
- Número de señales de Fibonacci
- Order blocks identificados
- Sacadas de liquidez detectadas

## Instalación y Uso

### 1. Instalación en TradingView

1. Abre TradingView en tu navegador
2. Ve al editor de Pine Script (Alt + E)
3. Copia y pega el código del archivo `kaizen_trading_strategy.pine`
4. Haz clic en "Guardar" y luego "Añadir al gráfico"

### 2. Configuración Inicial

1. **Configuración General**:
   - Activa `Mostrar Patrones` para ver las visualizaciones
   - Activa `Mostrar Estadísticas` para ver contadores
   - Activa `Activar Alertas` para recibir notificaciones

2. **Ajuste de Fibonacci**:
   - Mantén los niveles por defecto o personalízalos
   - Ajusta el `Lookback` según tu timeframe (20 para gráficos de 5min-1h)

3. **Configuración de Fractales**:
   - Usa longitud 5 para timeframes cortos (1-15min)
   - Usa longitud 7-10 para timeframes más largos

4. **Order Blocks**:
   - Ajusta el multiplicador de volumen (1.5-2.0 recomendado)
   - Aumenta el lookback para gráficos de timeframes largos

### 3. Interpretación de Señales

#### Señales de Entrada
- **🟢 COMPRA**: Confluencia de patrones alcistas
  - Precio cerca de Fibonacci 50%
  - Fractal bajo reciente
  - Sin sacadas de liquidez recientes

- **🔴 VENTA**: Confluencia de patrones bajistas
  - Precio cerca de Fibonacci 50%
  - Fractal alto reciente
  - Sin sacadas de liquidez recientes

#### Patrones de Confirmación
- **💧 LIQUIDEZ**: Sacada de liquidez detectada - esperar reversión
- **FIB 50%**: Precio en nivel clave de Fibonacci
- **OB Alcista/Bajista**: Order block identificado

#### Modelo Operativo
- **ALCISTA**: Condiciones favorables para compras
- **BAJISTA**: Condiciones favorables para ventas
- **TENDENCIA ALCISTA/BAJISTA**: Dirección general del mercado
- **NEUTRO**: Sin sesgo direccional claro

## Mejores Prácticas

### 1. Timeframes Recomendados
- **Scalping**: 1min-5min con fractales de longitud 3-5
- **Intraday**: 15min-1h con fractales de longitud 5-7
- **Swing**: 4h-1D con fractales de longitud 7-10

### 2. Gestión de Riesgo
- Usa stop loss basado en fractales contrarios
- Targets en próximos niveles de Fibonacci
- Risk:Reward mínimo 1:2

### 3. Confluencias
- Busca múltiples patrones confirmándose
- Prioriza señales con 3+ confirmaciones
- Evita operar contra la tendencia principal

### 4. Configuración de Alertas
- Configura alertas específicas para tu estrategia
- Usa alertas de "Once Per Bar" para evitar spam
- Revisa siempre el gráfico antes de operar

## Ejemplos de Uso

### Escenario 1: Entrada Alcista
1. Precio rechaza nivel Fibonacci 61.8%
2. Se forma fractal bajo
3. Order block alcista virginal cercano
4. Script genera señal 🟢 COMPRA

### Escenario 2: Sacada de Liquidez
1. Precio rompe máximo anterior
2. Reversa inmediatamente
3. Script marca 💧 LIQUIDEZ
4. Buscar entrada en dirección de la reversión

### Escenario 3: Confluencia Bajista
1. Precio rechaza Fibonacci 50%
2. Fractal alto formado
3. No hay sacadas recientes
4. Script genera señal 🔴 VENTA

## Personalización Avanzada

### Colores y Estilos
- Modifica los colores en la sección "CONFIGURACIÓN VISUAL"
- Ajusta transparencias cambiando los valores (0-100)
- Personaliza tamaños de labels y estilos

### Algoritmos
- Ajusta las funciones de detección según tu estilo
- Modifica tolerancias y sensibilidades
- Añade filtros adicionales en las condiciones

### Estadísticas
- Añade métricas personalizadas en la tabla
- Calcula ratios de éxito históricos
- Implementa tracking de performance

## Troubleshooting

### Problemas Comunes

1. **Script no muestra patrones**:
   - Verifica que "Mostrar Patrones" esté activado
   - Ajusta el lookback period
   - Comprueba que hay suficiente historial de datos

2. **Muchas señales falsas**:
   - Aumenta la sensibilidad de filtros
   - Reduce el número de patrones activos
   - Ajusta los períodos de lookback

3. **No hay alertas**:
   - Activa "Activar Alertas" en configuración
   - Configura alertas en TradingView
   - Verifica condiciones de alerta

4. **Performance lenta**:
   - Reduce el número máximo de líneas/labels
   - Disminuye períodos de lookback
   - Desactiva patrones no utilizados

## Soporte y Actualizaciones

Este script es parte del proyecto KAIZEN Meta Trader Bot. Para soporte, mejoras o reportar bugs:

1. Revisa la documentación completa
2. Verifica configuraciones antes de reportar issues
3. Proporciona screenshots para problemas visuales
4. Especifica timeframe y mercado cuando reportes problemas

## Versión y Changelog

**v1.0** - Lanzamiento inicial
- Implementación de todos los patrones principales
- Sistema completo de alertas
- Interface de configuración dinámica
- Estadísticas en tiempo real
- Documentación completa

---

*Script desarrollado para maximizar la precisión de trading mediante análisis técnico avanzado y reconocimiento de patrones institucionales.*