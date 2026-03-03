AC Race Engineer - Telemetry Capture App
========================================

INSTALLATION
------------
1. Copy the entire "ac_race_engineer" folder to:
   [AC install folder]\apps\python\

   Example:
   C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\ac_race_engineer\

2. Launch Assetto Corsa.

3. In any session, open the app sidebar (right side of screen)
   and enable "AC Race Engineer".

FULL CHANNEL SUPPORT
--------------------
The app bundles _ctypes.pyd for both 32-bit and 64-bit AC
configurations (DLLs/Lib/ and DLLs/Lib64/). The correct version
is loaded automatically. No manual DLL setup is required.

If _ctypes.pyd fails to load despite the bundled DLLs, the app
runs in "reduced mode" - it still records all sessions normally,
but 28 channels will show as empty (NaN). The remaining 54
channels work fine.

OUTPUT FILES
------------
Sessions are saved to:
  Documents\ac-race-engineer\sessions\

Each session creates two files:
  - .csv file: telemetry data (one row per sample at 25Hz)
  - .meta.json file: session info, car, track, setup, etc.

Example filenames:
  2026-03-02_1430_ks_ferrari_488_gt3_monza.csv
  2026-03-02_1430_ks_ferrari_488_gt3_monza.meta.json

CONFIGURATION
-------------
Edit config.ini in this folder to change settings:

  output_dir       - Where to save files (default: Documents folder)
  sample_rate_hz   - Samples per second, 20-30 (default: 25)
  buffer_size      - Buffer before flush, 100-5000 (default: 1000)
  flush_interval_s - Seconds between disk writes (default: 30)
  log_level        - debug, info, warn, error (default: info)

STATUS INDICATOR
----------------
The small app widget shows:
  Green  = Recording normally
  Yellow = Writing data to disk
  Red    = Error (check AC log: Documents\Assetto Corsa\logs\py_log.txt)
  Grey   = Idle (waiting for session)

TROUBLESHOOTING
---------------
- Check AC's Python log: Documents\Assetto Corsa\logs\py_log.txt
- Look for lines starting with [ACRaceEngineer]
- If the app does not appear, verify the folder structure is correct
- If no files are created, check that the output directory is writable
