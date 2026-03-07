# AC Race Engineer AI

## Qué es este proyecto
Ingeniero de carreras con IA para Assetto Corsa (original). Lee telemetría post-sesión, analiza el estilo de manejo del piloto, y genera/modifica archivos de setup (.ini) automáticamente. Explica cada cambio en lenguaje simple.

## Arquitectura
- ac_app/ → App in-game para AC: captura telemetría a CSV (20-30Hz), Python ~3.3 embebido, Fases 1-1.5 COMPLETADAS
- backend/ac_engineer/ → Paquete Python core con submódulos: parser/, analyzer/, knowledge/, engineer/, config/, storage/
  - config/   → ACConfig model + read_config / write_config / update_config
  - storage/  → SQLite init + CRUD functions para sessions, recommendations, setup_changes, messages
  - engineer/ → summarizer, setup_reader/writer, agents (Pydantic AI specialists), tools, skills/ (markdown prompts)
- backend/api/ → Servidor FastAPI que expone los módulos de ac_engineer como endpoints HTTP
  - routes/ → 7 routers: health, jobs, sessions, analysis, engineer, config, knowledge
  - jobs/ → JobManager in-memory + async worker + WebSocket streaming
  - engineer/ → pipeline (engineer+chat jobs), cache, serializers
- backend/tests/ → Tests pytest para todos los módulos del backend
- frontend/src/ → App React (TypeScript)
  - components/ui/ → 10 design system components (Button, Card, Badge, Modal, etc.)
  - components/layout/ → AppShell, Sidebar, SplashScreen, ToastContainer
  - components/onboarding/ → OnboardingWizard, PathInput, Step* components
  - hooks/ → 9 hooks (useTheme, useSessions, useLaps, useMessages, useRecommendations, etc.)
  - store/ → 5 Zustand stores (ui, session, theme, notification, job)
  - lib/ → api.ts, types.ts, constants.ts, validation.ts, wsManager.ts
  - views/ → 5 vistas: sessions, analysis, compare, engineer, settings
- frontend/src-tauri/ → Shell Tauri (Rust, solo configuración mínima)
- frontend/tests/ → Tests Vitest + Testing Library (mirror de src/)
- data/sessions/ → Archivos de telemetría (.csv) y metadata (.meta.json) por sesión
- data/setups/ → Archivos de setup .ini
- data/config.json → Configuración de usuario (ac_install_path, llm_provider, llm_model, api_key)
- data/ac_engineer.db → Base de datos SQLite (4 tablas: sessions, recommendations, setup_changes, messages)

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
- `from ac_engineer.storage import init_db, save_session, list_sessions, save_recommendation, update_recommendation_status, save_message, get_messages`
- `from ac_engineer.engineer import summarize_session, read_parameter_ranges, validate_changes, apply_changes, analyze_with_engineer, apply_recommendation, build_model`

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

## Reglas de desarrollo
- Todo tipo de coche debe funcionar (vanilla y mods), no hardcodear por coche
- El parser de setups .ini debe ser genérico (los mods tienen parámetros variables)
- El LLM NO hace cálculos numéricos, recibe métricas ya procesadas
- Los cambios de setup del LLM vienen via Pydantic AI tools (function calling), no texto libre
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
Fases 1 a 7 completadas (1128 tests totales: parser 143, analyzer 141, knowledge 48, config 34, storage 28, engineer core 68, engineer agents 81, API 201, frontend 329). El proyecto tiene funcionalidad end-to-end completa.
