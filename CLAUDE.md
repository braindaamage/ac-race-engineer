# AC Race Engineer AI

## Qué es este proyecto
Ingeniero de carreras con IA para Assetto Corsa (original). Lee telemetría post-sesión, analiza el estilo de manejo del piloto, y genera/modifica archivos de setup (.ini) automáticamente. Explica cada cambio en lenguaje simple.

## Arquitectura
- src/telemetry_capture/ → App Python in-game para AC que captura telemetría a CSV (20-30Hz)
- src/parser/ → Segmentación por vuelta y curva, parser de setups .ini
- src/analyzer/ → Motor de métricas (temps, slip angles, balance, trazada)
- src/knowledge/ → Knowledge base de dinámica vehicular (markdown)
- src/engineer/ → Integración Claude API con function calling para generar cambios de setup
- src/cli/ → Interfaz CLI (analyze, suggest, apply, compare, chat)
- ac_app/ → Archivos de la app para instalar en Assetto Corsa
- data/sessions/ → Archivos de telemetría (.csv) y metadata (.meta.json) por sesión
- data/setups/ → Archivos de setup .ini

## Stack
- Python 3.11+
- pandas, numpy, scipy para análisis
- Claude API (Sonnet para análisis rápido, Opus para setup complejo)
- Click o Typer para CLI
- CSV para captura in-game, Parquet para post-procesamiento

## Reglas de desarrollo
- Todo tipo de coche debe funcionar (vanilla y mods), no hardcodear por coche
- El parser de setups .ini debe ser genérico (los mods tienen parámetros variables)
- El LLM NO hace cálculos numéricos, recibe métricas ya procesadas
- Los cambios de setup del LLM vienen via function calling, no texto libre
- Validar siempre que los cambios estén en rangos posibles antes de escribir el .ini
- Las explicaciones al usuario deben ser claras para alguien que sabe poco de setup
- Detectar datos inconsistentes de mods con físicas rotas y avisar

## Entorno Python
- Este proyecto usa conda. El environment se llama `ac-race-engineer` (Python 3.11+)
- SIEMPRE ejecutar `conda activate ac-race-engineer` antes de cualquier comando Python
- Si el env no existe, crearlo: `conda create -n ac-race-engineer python=3.11 -y`
- EXCEPCIÓN: el código de la app in-game de AC usa el Python embebido de AC, no conda
- NUNCA instalar paquetes ni ejecutar scripts en el env base de conda o en system Python

## Fase actual
Fase 1 - Captura de telemetría (app in-game para AC)
