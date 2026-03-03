# Contract: App Configuration (config.ini)

**Feature**: 001-telemetry-capture
**Version**: 1.0

## Format

- **Format**: INI (Windows-style, parsed by Python's `configparser`)
- **Location**: `apps/python/ac_race_engineer/config.ini`
- **Encoding**: UTF-8

## Default Contents

```ini
[SETTINGS]
; Output directory for session files
; Use forward slashes or double backslashes for paths
; Default: ~/Documents/ac-race-engineer/sessions/
output_dir =

; Target sample rate in Hz (20-30)
; Default: 25
sample_rate_hz = 25

; Maximum samples in buffer before forced flush
; Default: 1000
buffer_size = 1000

; Seconds between periodic disk flushes
; Default: 30
flush_interval_s = 30

; Logging level: debug, info, warn, error
; Default: info
log_level = info
```

## Behavior

- Empty `output_dir` → uses default: `~/Documents/ac-race-engineer/sessions/`
- `~` in paths is expanded to the user's home directory via `os.path.expanduser()`
- Missing `config.ini` → all defaults are used, no error
- Malformed values → defaults are used, warning logged
- Out-of-range `sample_rate_hz` → clamped to 20-30

## Validation Ranges

| Setting | Min | Max | Default |
|---|---|---|---|
| sample_rate_hz | 20 | 30 | 25 |
| buffer_size | 100 | 5000 | 1000 |
| flush_interval_s | 5 | 120 | 30 |
