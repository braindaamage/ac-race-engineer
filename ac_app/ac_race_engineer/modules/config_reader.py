"""Configuration reader for AC Race Engineer.

Parses config.ini with defaults and validation. Python 3.3 compatible.
"""
import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


DEFAULTS = {
    "output_dir": os.path.join(os.path.expanduser("~"), "Documents", "ac-race-engineer", "sessions"),
    "sample_rate_hz": 25,
    "buffer_size": 1000,
    "flush_interval_s": 30.0,
    "log_level": "info",
}

VALID_LOG_LEVELS = ("debug", "info", "warn", "error")


def _clamp(value, min_val, max_val):
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def read_config(config_path):
    """Read and validate config.ini. Returns dict with all settings.

    If file is missing or malformed, returns defaults for all values.
    Out-of-range numeric values are clamped to valid ranges.
    """
    config = dict(DEFAULTS)

    if not os.path.isfile(config_path):
        return config

    parser = configparser.ConfigParser()
    try:
        parser.read(config_path)
    except Exception:
        return config

    if not parser.has_section("SETTINGS"):
        return config

    # output_dir
    raw_dir = parser.get("SETTINGS", "output_dir", fallback="").strip()
    if raw_dir:
        config["output_dir"] = os.path.expanduser(raw_dir)

    # sample_rate_hz
    try:
        val = int(parser.get("SETTINGS", "sample_rate_hz", fallback="25"))
        config["sample_rate_hz"] = _clamp(val, 20, 30)
    except (ValueError, TypeError):
        pass

    # buffer_size
    try:
        val = int(parser.get("SETTINGS", "buffer_size", fallback="1000"))
        config["buffer_size"] = _clamp(val, 100, 5000)
    except (ValueError, TypeError):
        pass

    # flush_interval_s
    try:
        val = float(parser.get("SETTINGS", "flush_interval_s", fallback="30"))
        config["flush_interval_s"] = _clamp(val, 5.0, 120.0)
    except (ValueError, TypeError):
        pass

    # log_level
    raw_level = parser.get("SETTINGS", "log_level", fallback="info").strip().lower()
    if raw_level in VALID_LOG_LEVELS:
        config["log_level"] = raw_level

    return config
