# Quickstart: Telemetry Capture App

## Installation

1. Copy the `ac_race_engineer` folder into your Assetto Corsa installation:
   ```
   {AC_install}/apps/python/ac_race_engineer/
   ```

2. (Optional) For full channel support, ensure `_ctypes.pyd` is available:
   - Check if `{AC_install}/apps/python/system/DLLs/_ctypes.pyd` exists
   - If so, copy it to `ac_race_engineer/DLLs/` (create the folder if needed)
   - Without this, the app runs in **reduced mode** (47 of 76 channels). The 29 affected channels are:
     - fuel (1)
     - tyre_wear_fl/fr/rl/rr (4)
     - wheel_load_fl/fr/rl/rr (4)
     - damage_front/rear/left/right/center (5)
     - session_type (falls back to "unknown")
     - drs (1)
     - ers_charge (1)
     - tyre_temp_inner_fl/fr/rl/rr (4)
     - tyre_temp_mid_fl/fr/rl/rr (4)
     - tyre_temp_outer_fl/fr/rl/rr (4)
   - These channels will be written as empty (NaN). All other channels work normally via the `ac` module.

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
    ├── DLLs/                   # _ctypes.pyd (user-provided)
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
