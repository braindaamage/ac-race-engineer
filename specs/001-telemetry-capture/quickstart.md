# Quickstart: Telemetry Capture App

## Installation

1. Copy the `ac_race_engineer` folder into your Assetto Corsa installation:
   ```
   {AC_install}/apps/python/ac_race_engineer/
   ```

2. The app includes `_ctypes.pyd` for both 32-bit and 64-bit Python (`DLLs/Lib/` and `DLLs/Lib64/`). Full channel support (82 channels) is enabled automatically. No manual DLL setup is required.
   - If sim_info fails to load despite bundled DLLs, the app falls back to **reduced mode** (54 of 82 channels) and session detection uses speed/position heuristics instead of shared memory.

3. Launch Assetto Corsa. Enable the "AC Race Engineer" app from the sidebar app list.

## Usage

The app runs automatically. No interaction required.

1. Start any session (practice, qualify, race)
2. A small widget shows recording status:
   - **Green**: recording normally
   - **Yellow**: flushing data to disk
   - **Red**: error (check logs)
3. Drive normally. Telemetry is captured at 25Hz.
4. End the session. Files are saved automatically.

## Output Files

Default location: `Documents/ac-race-engineer/sessions/`

Each session produces two files:
- `2026-03-02_1430_ks_ferrari_488_gt3_monza.csv` — telemetry data
- `2026-03-02_1430_ks_ferrari_488_gt3_monza.meta.json` — session metadata + setup

## Configuration

Edit `apps/python/ac_race_engineer/config.ini` to change:
- **output_dir**: where session files are saved
- **sample_rate_hz**: capture frequency (20-30, default 25)
- **buffer_size**: samples before forced flush (default 1000)
- **flush_interval_s**: seconds between disk writes (default 30)

## Development Setup (for contributors)

```bash
# Create conda environment
conda create -n ac-race-engineer python=3.11 -y
conda activate ac-race-engineer

# Install dev dependencies
pip install pytest

# Run tests
pytest tests/
```

## Project Layout

```
ac_app/
└── ac_race_engineer/           # AC app (copy this folder to AC)
    ├── ac_race_engineer.py     # Entry point
    ├── config.ini              # Configuration
    ├── sim_info.py             # Shared memory access
    ├── DLLs/                   # Bundled DLLs (auto-detected)
    │   ├── Lib/                # 32-bit _ctypes.pyd
    │   └── Lib64/              # 64-bit _ctypes.pyd
    └── modules/                # Core logic
        ├── channels.py         # Channel definitions
        ├── buffer.py           # Sample buffer
        ├── writer.py           # CSV/JSON file output
        ├── config_reader.py    # Config parsing
        ├── session.py          # Session lifecycle
        ├── setup_reader.py     # Setup .ini discovery
        ├── sanitize.py         # Filename sanitization
        └── status.py           # UI status indicator

tests/
└── telemetry_capture/          # Tests (run in conda env)
    ├── conftest.py
    ├── mocks/                  # ac/acsys module mocks
    │   ├── ac.py
    │   └── acsys.py
    └── unit/
        ├── test_buffer.py
        ├── test_writer.py
        ├── test_channels.py
        ├── test_config_reader.py
        ├── test_session.py
        ├── test_setup_reader.py
        └── test_sanitize.py
```
