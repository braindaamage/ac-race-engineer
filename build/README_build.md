# Building AC Race Engineer Backend

Package the FastAPI backend as a standalone Windows executable for use as a Tauri sidecar.

## Prerequisites

1. **conda environment** with Python 3.11+:
   ```bash
   conda activate ac-race-engineer
   ```

2. **PyInstaller** installed in the environment:
   ```bash
   pip install pyinstaller
   ```

3. All backend dependencies already installed (FastAPI, uvicorn, pydantic-ai, etc.)

## Build Commands

### One-directory mode (recommended)

Faster startup, easier to debug missing files:

```bash
cd <repo-root>
pyinstaller build/ac_engineer.spec
```

Output: `dist/ac_engineer/` directory containing `ac_engineer.exe` + supporting files.

### One-file mode

Single executable (slower startup due to temp extraction):

```bash
cd <repo-root>
pyinstaller build/ac_engineer.spec --onefile
```

Output: `dist/ac_engineer.exe`

## Expected Output Structure (onedir)

```
dist/
  ac_engineer/
    ac_engineer.exe              # Entry point
    data/                        # Created at runtime (db, config, sessions)
    ac_engineer/
      knowledge/docs/            # Bundled knowledge base documents
      engineer/skills/           # Bundled skill prompts
    ...                          # Python runtime + dependencies
```

## How Tauri Launches the Sidecar

Tauri's sidecar configuration in `tauri.conf.json` points to the built executable. The backend listens on `127.0.0.1:57832` by default. Tauri spawns it as a child process and communicates via HTTP.

The `data/` directory is resolved relative to the executable location when running in frozen (PyInstaller) mode, thanks to the path resolution in `backend/api/paths.py`.

## Runtime Data Directory

In packaged mode, the server creates/uses a `data/` directory next to the executable:
- `data/ac_engineer.db` — SQLite database
- `data/config.json` — User configuration
- `data/sessions/` — Telemetry session files

## Troubleshooting

### Missing hidden imports

If you see `ModuleNotFoundError` at runtime, add the module to `hiddenimports` in `ac_engineer.spec` and rebuild.

Common candidates:
- LLM provider SDKs: `anthropic`, `openai`, `google.generativeai`
- `pydantic_ai` submodules
- `watchdog.observers`

### Data files not found

If knowledge documents or skill prompts are missing at runtime:
1. Check that `datas` entries in the spec file point to the correct source paths
2. Verify the files exist in the `dist/ac_engineer/ac_engineer/` subdirectory after build
3. Ensure `api/paths.py` correctly resolves paths in frozen mode (`sys.frozen == True`)

### Antivirus false positives

PyInstaller executables may trigger Windows Defender. Options:
- Use `--onedir` mode (less likely to trigger)
- Sign the executable with a code signing certificate
- Add an exclusion in Windows Security settings

### Large output size

The executable bundles the entire Python runtime + all dependencies. To reduce size:
- Use `--exclude-module` in the spec for unnecessary packages
- Enable UPX compression (already configured in the spec)
- Consider using a minimal conda environment with only required packages
