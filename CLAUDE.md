# AC Race Engineer AI

## Qué es este proyecto
Ingeniero de carreras con IA para Assetto Corsa (original). Lee telemetría post-sesión, analiza el estilo de manejo del piloto, y genera/modifica archivos de setup (.ini) automáticamente. Explica cada cambio en lenguaje simple.

## Arquitectura
- ac_app/ → App in-game para AC: captura telemetría a CSV (20-30Hz), Python ~3.3 embebido, Fases 1-1.5 COMPLETADAS
- backend/ac_engineer/ → Paquete Python core con submódulos: parser/, analyzer/, knowledge/, engineer/, config/, storage/, acd_reader/, resolver/
  - config/   → ACConfig model + read_config / write_config / update_config
  - storage/  → SQLite init + CRUD functions para sessions, recommendations, setup_changes, messages, llm_events
  - engineer/ → summarizer, setup_reader/writer, agents (Pydantic AI specialists), tools, skills/ (markdown prompts), trace (diagnostic traces), conversion (storage↔physical domain translation)
  - acd_reader/ → Descifrado de archivos data.acd (propietario AC), zero-dependency
  - resolver/ → Resolución de parámetros en 3 tiers (open data → ACD → session fallback), caché SQLite
- backend/api/ → Servidor FastAPI que expone los módulos de ac_engineer como endpoints HTTP
  - routes/ → 8 routers: health, jobs, sessions, analysis, engineer, config, knowledge, cars
  - jobs/ → JobManager in-memory + async worker + WebSocket streaming
  - engineer/ → pipeline (engineer+chat jobs), cache, serializers
- backend/tests/ → Tests pytest para todos los módulos del backend
- frontend/src/ → App React (TypeScript)
  - components/ui/ → 10 design system components (Button, Card, Badge, Modal, etc.)
  - components/layout/ → AppShell, Sidebar, SplashScreen, ToastContainer
  - components/onboarding/ → OnboardingWizard, PathInput, Step* components
  - hooks/ → 11 hooks (useTheme, useSessions, useLaps, useMessages, useRecommendations, useCars, useTrace, etc.)
  - store/ → 5 Zustand stores (ui, session, theme, notification, job)
  - lib/ → api.ts, types.ts, constants.ts, validation.ts, wsManager.ts
  - views/ → 5 vistas: sessions, analysis, compare, engineer, settings
- frontend/src-tauri/ → Shell Tauri (Rust, solo configuración mínima)
- frontend/tests/ → Tests Vitest + Testing Library (mirror de src/)
- data/sessions/ → Archivos de telemetría (.csv) y metadata (.meta.json) por sesión
- data/setups/ → Archivos de setup .ini
- data/config.json → Configuración de usuario (ac_install_path, llm_provider, llm_model, api_key, diagnostic_mode)
- data/ac_engineer.db → Base de datos SQLite (7 tablas: sessions, recommendations, setup_changes, messages, parameter_cache, llm_events, llm_tool_calls)
- data/traces/ → Archivos de traza diagnóstica (.md) generados cuando diagnostic_mode está activo

## Stack
- Python 3.11+ (backend, conda env `ac-race-engineer`)
- FastAPI para el servidor HTTP
- pandas, numpy, scipy para análisis de telemetría
- Pydantic AI como framework de agentes LLM (provider-agnostic: Anthropic Claude, OpenAI, Google Gemini — seleccionable via configuración)
- Tauri v2 (Rust) para el shell nativo Windows del desktop app
- React 18 con TypeScript strict para la UI del desktop app
- TanStack Query v5 para server state, Zustand v5 para client state
- Recharts v3 para visualización de telemetría
- Vitest + Testing Library para tests del frontend
- CSV para captura in-game, Parquet para post-procesamiento

## Imports públicos
- `from ac_engineer.config import read_config, write_config, update_config, ACConfig`
- `from ac_engineer.storage import init_db, save_session, list_sessions, save_recommendation, update_recommendation_status, save_message, get_messages, save_llm_event, get_llm_events, LlmEvent, LlmToolCall`
- `from ac_engineer.engineer import summarize_session, read_parameter_ranges, validate_changes, apply_changes, analyze_with_engineer, apply_recommendation, build_model, extract_tool_calls, classify_parameter, to_physical, to_storage, SCALE_FACTORS`
- `from ac_engineer.acd_reader import read_acd, AcdResult`
- `from ac_engineer.resolver import resolve_parameters, list_cars, get_cached_parameters, invalidate_cache, invalidate_all_caches, ResolvedParameters, ResolutionTier, CarStatus`

## Fases del proyecto
- Fase 1 ✅ Captura de telemetría (app in-game AC)
- Fase 1.5 ✅ Setup stint tracking
- Fase 2 ✅ Parser (segmentar CSV por vueltas/curvas, parsear .ini) — 143 tests
- Fase 3 ✅ Analyzer (métricas por vuelta: slip angles, temps, balance, trazada) — 141 tests
- Fase 4 ✅ Knowledge Base (dinámica vehicular en markdown + loader) — 48 tests
- Fase 5.1 ✅ Config + Storage (ACConfig, SQLite CRUD) — 62 tests
- Fase 5.2 ✅ Engineer Core (summarizer, setup reader/writer) — 68 tests
- Fase 5.3 ✅ Engineer Agents (Pydantic AI specialists, tools, conflict resolution) — 81 tests
- Fase 6 ✅ Backend API (FastAPI: 26 endpoints + 1 WebSocket, job system, file watcher) — 201 tests
- Fase 7 ✅ Desktop App (Tauri + React: sessions, analysis, compare, engineer chat, settings) — 329 tests
- Fase 8.1 ✅ ACD File Reader (descifrado de archivos data.acd propietarios de AC) — 20 tests
- Fase 8.2 ✅ Setup Resolver (resolución de parámetros en 3 tiers, caché, API, UI) — 93 tests
- Fase 9 ✅ LLM Usage Tracking & Optimization (storage, capture, UI, token/prompt optimization, tool scoping, tracking redesign) — 104 tests
- Fase 10 ✅ Domain-Scoped Setup Context (filtrado de parámetros de setup por dominio en prompts de agentes especialistas) — 11 tests
- Fase 11.1 ✅ Cache Token Tracking (cache_read/write tokens en pipeline de uso LLM, UI condicional) — ~66 tests
- Fase 11.2 ✅ Agent Diagnostic Traces (trazas Markdown de conversaciones multi-turn, toggle en Settings, API + modal) — ~60 tests
- Fase 12 ✅ Principal Narrated Analysis (síntesis narrativa del agente principal: summary ejecutivo + explanation detallado, persistencia en DB, sección expandible en frontend) — 18 tests
- Fase 13 ✅ Fix Setup Value Domains (conversión storage↔physical para INDEX/SCALED/DIRECT, clasificación por SHOW_CLICKS, invalidación lazy de caché, columna Setup File en UI) — 39 tests

## Reglas de desarrollo
- Todo tipo de coche debe funcionar (vanilla y mods), no hardcodear por coche
- El parser de setups .ini debe ser genérico (los mods tienen parámetros variables)
- El LLM NO hace cálculos numéricos, recibe métricas ya procesadas
- Los cambios de setup del LLM vienen via Pydantic AI tools (function calling), no texto libre
- Validar siempre que los cambios estén en rangos posibles antes de escribir el .ini
- Los valores de setup tienen 3 dominios de almacenamiento (INDEX/SCALED/DIRECT según SHOW_CLICKS); el LLM siempre trabaja en unidades físicas y la conversión a storage es determinística en engineer/conversion.py
- Las explicaciones al usuario deben ser claras para alguien que sabe poco de setup
- Detectar datos inconsistentes de mods con físicas rotas y avisar

## Entorno Python
- Este proyecto usa conda. El environment se llama `ac-race-engineer` (Python 3.11+)
- SIEMPRE ejecutar `conda activate ac-race-engineer` antes de cualquier comando Python
- Si el env no existe, crearlo: `conda create -n ac-race-engineer python=3.11 -y`
- EXCEPCIÓN: el código de la app in-game de AC usa el Python embebido de AC, no conda
- NUNCA instalar paquetes ni ejecutar scripts en el env base de conda o en system Python

## Fase actual
Fases 1 a 13 completadas (1449 tests totales: backend 1055, frontend 394). El proyecto tiene funcionalidad end-to-end completa con observabilidad de consumo LLM, filtrado de contexto por dominio, cache token tracking, trazas diagnósticas de agentes, narrativa coherente del agente principal y conversión correcta de dominios de valores de setup.
