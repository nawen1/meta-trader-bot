# 🚀 Guía de Instalación Rápida - KAIZEN Trading Strategy

## ⏱️ Instalación en 5 Minutos

### Paso 1: Acceder a TradingView
1. Ve a [TradingView.com](https://tradingview.com)
2. Inicia sesión en tu cuenta (gratis o premium)
3. Abre cualquier gráfico de trading

### Paso 2: Abrir Pine Editor
1. Presiona las teclas `Alt + E` (Windows/Linux) o `Cmd + E` (Mac)
2. Se abrirá el editor de Pine Script en la parte inferior

### Paso 3: Cargar el Script
1. **Descargar**: Descarga el archivo `kaizen_trading_strategy.pine` desde este repositorio
2. **Copiar**: Abre el archivo y copia todo el contenido (Ctrl+A, Ctrl+C)
3. **Pegar**: En el Pine Editor, borra el código por defecto y pega el código KAIZEN
4. **Guardar**: Haz clic en el botón "Guardar" (💾)

### Paso 4: Añadir al Gráfico
1. Haz clic en "Añadir al gráfico" después de guardar
2. El script aparecerá en tu gráfico con todas las funcionalidades

### Paso 5: Configuración Básica
1. Haz clic en el **ícono de configuración** (⚙️) del script en el gráfico
2. En la pestaña "Entradas":
   - ✅ Activa "Mostrar Patrones"
   - ✅ Activa "Mostrar Estadísticas"  
   - ✅ Activa "Activar Alertas"
3. Haz clic "OK"

## 🔔 Configurar Alertas (Opcional)

### Para recibir notificaciones:
1. Haz clic derecho en el gráfico
2. Selecciona "Añadir alerta"
3. En "Condición", selecciona tu script "KAIZEN"
4. Configura el tipo de alerta (email, push, etc.)
5. Haz clic "Crear"

## ⚙️ Configuración Rápida por Estilo

### 📊 Para Day Trading (Recomendado)
```
Timeframe del gráfico: 15min o 1h
Configuración:
- Longitud de Fractal: 5
- Fibonacci habilitado: ✅
- Order Blocks habilitado: ✅
- Sacadas de Liquidez: ✅
- Sensibilidad Liquidez: 0.5%
```

### ⚡ Para Scalping
```
Timeframe del gráfico: 1min o 5min
Configuración:
- Longitud de Fractal: 3
- Sensibilidad Liquidez: 0.3%
- Lookback Order Blocks: 30
- Todas las alertas activadas
```

### 📈 Para Swing Trading
```
Timeframe del gráfico: 4h o 1D
Configuración:
- Longitud de Fractal: 7
- Lookback Fibonacci: 30
- Lookback Order Blocks: 100
- Sensibilidad Liquidez: 1.0%
```

## 🎯 ¿Qué Verás en el Gráfico?

### Símbolos y Etiquetas:
- **▲ ▼**: Fractales (puntos de giro)
- **💧 LIQUIDEZ**: Sacadas de liquidez detectadas
- **FIB 50%**: Niveles de Fibonacci alcanzados
- **🟢 COMPRA**: Señal de entrada alcista
- **🔴 VENTA**: Señal de entrada bajista
- **📊 MODELO**: Estado actual del mercado

### Zonas y Líneas:
- **Cajas naranjas**: Order blocks identificados
- **Líneas azules**: Niveles de Fibonacci
- **Zonas sombreadas**: Áreas de interés

### Estadísticas (Esquina superior derecha):
- Total de patrones detectados
- Contadores por tipo de patrón
- Frecuencia de señales

## 🔧 Solución de Problemas Rápidos

### ❌ "No veo ningún patrón"
**Solución**: 
1. Verifica que "Mostrar Patrones" esté activado
2. Cambia a un timeframe de 15min o 1h
3. Espera unas velas para que se formen patrones

### ❌ "Demasiadas señales"
**Solución**:
1. Aumenta la "Longitud de Fractal" a 7
2. Reduce la "Sensibilidad de Liquidez" a 0.3%
3. Aumenta el lookback de Fibonacci

### ❌ "No recibo alertas"
**Solución**:
1. Verifica que "Activar Alertas" esté en ✅
2. Configura alertas manualmente en TradingView
3. Revisa la configuración de notificaciones de tu cuenta

## 📱 Acceso Móvil

El script funciona perfectamente en la app móvil de TradingView:
1. Instala la app TradingView
2. Inicia sesión con la misma cuenta
3. Los scripts aparecerán automáticamente en tus gráficos

## 🎓 Primeros Pasos para Aprender

### 1. Observa Sin Operar (1 semana)
- Mira cómo se forman los patrones
- Observa la precisión de las señales
- Familiarízate con los símbolos

### 2. Trading en Demo (2 semanas)
- Usa una cuenta demo para practicar
- Sigue solo las señales 🟢🔴 principales
- Anota tus resultados

### 3. Trading Real (Gradual)
- Empieza con posiciones pequeñas
- Usa stop loss basado en fractales contrarios
- Gestiona el riesgo apropiadamente

## 📞 Soporte Rápido

**¿Problemas de instalación?**
- Copia exactamente el código sin modificar
- Asegúrate de tener una cuenta TradingView válida
- Prueba en modo incógnito si hay problemas de caché

**¿Quieres personalizar?**
- Lee la documentación completa en `README_PineScript.md`
- Modifica colores en la sección "CONFIGURACIÓN VISUAL"
- Ajusta parámetros según tu estilo

---

### 🎉 ¡Listo! Ya tienes KAIZEN funcionando en tu TradingView

**Tiempo total de instalación: 5 minutos**
**Próximo paso**: Lee la documentación completa para dominar todas las características.