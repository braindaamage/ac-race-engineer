"""AC Race Engineer - Telemetry Capture App for Assetto Corsa.

Entry point for the AC in-game app. This is the ONLY file that imports
ac and acsys modules. Python 3.3 compatible.
"""
import sys
import os
import time
import traceback

# Add modules directory to path
_app_dir = os.path.dirname(os.path.realpath(__file__))
_modules_dir = os.path.join(_app_dir, "modules")
if _modules_dir not in sys.path:
    sys.path.insert(0, _modules_dir)

import ac
import acsys

from config_reader import read_config
from channels import (
    HEADER, CHANNEL_DEFINITIONS, read_all_channels, set_session_start_time,
    reset_session_state, init_reduced_mode, set_log_func,
)
import channels as channels_mod
from buffer import SampleBuffer
from writer import (
    generate_filename, ensure_output_dir, write_csv_header,
    append_csv_rows, write_early_metadata, write_final_metadata,
)
from session import (
    SessionManager, STATE_IDLE, STATE_RECORDING, STATE_FINALIZING,
    AC_STATUS_LIVE,
)
from setup_reader import find_active_setup
from status import STATUS_IDLE, STATUS_RECORDING, STATUS_FLUSHING, STATUS_ERROR, get_status_display

APP_VERSION = "0.1.0"
APP_NAME = "AC Race Engineer"

# Session type mapping from shared memory value to string
SESSION_TYPE_MAP = {
    -1: "unknown",
    0: "practice",
    1: "qualify",
    2: "race",
    3: "hotlap",
    4: "time_attack",
    5: "drift",
    6: "drag",
}

# Globals
_config = None
_sim_info = None
_session_mgr = None
_buffer = None
_app_window = None
_status_label = None
_current_status = STATUS_IDLE

# Recording state
_csv_filepath = None
_meta_filepath = None
_base_filename = None
_session_start_time = 0.0
_total_samples_written = 0
_last_sample_time = 0.0
_sample_interval = 0.04  # 1/25 Hz default
_session_metadata = None

# Logging
_log_level_map = {"debug": 0, "info": 1, "warn": 2, "error": 3}
_current_log_level = 1

# Error state
_error_flag = False


def _log(level, msg):
    """Log a message if the level is at or above the configured level."""
    if _log_level_map.get(level, 1) >= _current_log_level:
        ac.log("[ACRaceEngineer] [%s] %s" % (level.upper(), msg))


def _set_status(status_code):
    """Update the UI status indicator."""
    global _current_status
    _current_status = status_code
    if _status_label is not None:
        display = get_status_display(status_code)
        ac.setText(_status_label, display[0])
        ac.setBackgroundColor(_status_label, display[1], display[2], display[3])


def _get_session_status():
    """Get the current AC session status."""
    if _sim_info is not None:
        try:
            return _sim_info.graphics.status
        except Exception:
            pass
    return 0


def _get_session_type():
    """Get the current AC session type as a string."""
    if _sim_info is not None:
        try:
            session_val = _sim_info.graphics.session
            return SESSION_TYPE_MAP.get(session_val, "unknown")
        except Exception:
            pass
    return "unknown"


def _start_recording(car_name, track_name):
    """Initialize a new recording session."""
    global _csv_filepath, _meta_filepath, _base_filename
    global _session_start_time, _total_samples_written, _last_sample_time
    global _session_metadata, _error_flag

    _error_flag = False
    _session_start_time = time.time()
    _total_samples_written = 0
    _last_sample_time = 0.0

    set_session_start_time(_session_start_time)
    reset_session_state()
    init_reduced_mode(_sim_info)

    _log("debug", "Recording init: car=%s track=%s" % (car_name, track_name))

    # Generate filenames
    _base_filename = generate_filename(car_name, track_name, _session_start_time)
    output_dir = _config["output_dir"]

    try:
        ensure_output_dir(output_dir)
    except Exception as e:
        _log("error", "Cannot create output dir: %s" % str(e))
        _set_status(STATUS_ERROR)
        _error_flag = True
        return

    _csv_filepath = os.path.join(output_dir, _base_filename + ".csv")
    _meta_filepath = os.path.join(output_dir, _base_filename + ".meta.json")

    # File preservation: append suffix if files already exist
    suffix = 1
    while os.path.exists(_csv_filepath) or os.path.exists(_meta_filepath):
        suffix += 1
        suffixed_name = "%s_%d" % (_base_filename, suffix)
        _csv_filepath = os.path.join(output_dir, suffixed_name + ".csv")
        _meta_filepath = os.path.join(output_dir, suffixed_name + ".meta.json")

    # Write CSV header
    try:
        write_csv_header(_csv_filepath, HEADER)
    except IOError as e:
        _log("error", "Cannot write CSV header: %s" % str(e))
        _set_status(STATUS_ERROR)
        _error_flag = True
        return

    # Discover active setup
    setup_filename, setup_contents, setup_confidence = find_active_setup(car_name, track_name)
    if setup_filename:
        _log("info", "Setup found: %s (confidence: %s)" % (setup_filename, setup_confidence))
    else:
        _log("info", "No setup file found")

    # Get track info
    track_config = ac.getTrackConfiguration(0)
    track_length = ac.getTrackLength(0)
    tyre_compound = ac.getCarTyreCompound(0)
    driver_name = ac.getDriverName(0)

    # Temperatures
    air_temp = None
    road_temp = None
    if _sim_info is not None:
        try:
            air_temp = _sim_info.static.airTemp
            road_temp = _sim_info.static.roadTemp
        except Exception:
            pass

    # Build metadata
    _session_metadata = {
        "app_version": APP_VERSION,
        "session_start": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(_session_start_time)),
        "session_end": None,
        "car_name": car_name,
        "track_name": track_name,
        "track_config": track_config if track_config else "",
        "track_length_m": track_length,
        "session_type": _get_session_type(),
        "tyre_compound": tyre_compound if tyre_compound else "",
        "laps_completed": None,
        "total_samples": None,
        "sample_rate_hz": None,
        "air_temp_c": air_temp,
        "road_temp_c": road_temp,
        "driver_name": driver_name if driver_name else "",
        "setup_filename": setup_filename,
        "setup_contents": setup_contents,
        "setup_confidence": setup_confidence,
        "channels_available": [],
        "channels_unavailable": [],
        "sim_info_available": _sim_info is not None,
        "reduced_mode": channels_mod.reduced_mode,
        "tyre_temp_zones_validated": False,
        "csv_filename": os.path.basename(_csv_filepath),
    }

    # Write early metadata
    try:
        write_early_metadata(_meta_filepath, _session_metadata)
    except IOError as e:
        _log("error", "Cannot write metadata: %s" % str(e))
        _set_status(STATUS_ERROR)
        _error_flag = True
        return

    # Reset buffer
    _buffer.clear()
    _buffer.mark_flushed()

    _set_status(STATUS_RECORDING)
    _log("info", "Recording started: %s" % os.path.basename(_csv_filepath))


def _flush_buffer():
    """Flush the sample buffer to the CSV file."""
    global _total_samples_written

    if _buffer.count == 0:
        return

    rows = _buffer.get_all()
    try:
        _set_status(STATUS_FLUSHING)
        append_csv_rows(_csv_filepath, rows)
        _total_samples_written += len(rows)
        _buffer.mark_flushed()
        _log("debug", "Flushed %d samples (total: %d)" % (len(rows), _total_samples_written))
        _set_status(STATUS_RECORDING)
    except IOError as e:
        _log("error", "Flush failed: %s" % str(e))
        _set_status(STATUS_ERROR)
        global _error_flag
        _error_flag = True


def _finalize_session():
    """Finalize the current recording session."""
    global _session_metadata, _error_flag

    _log("info", "Finalizing session...")

    # Final flush
    _flush_buffer()

    # Update metadata with channel availability from first sample
    if _session_metadata is not None:
        _session_metadata["channels_available"] = list(channels_mod.channels_available)
        _session_metadata["channels_unavailable"] = list(channels_mod.channels_unavailable)
        _session_metadata["tyre_temp_zones_validated"] = channels_mod.tyre_temp_zones_validated

    # Update metadata with final values
    if _session_metadata is not None and not _error_flag:
        now = time.time()
        duration = now - _session_start_time
        _session_metadata["session_end"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
        _session_metadata["total_samples"] = _total_samples_written

        if duration > 0:
            _session_metadata["sample_rate_hz"] = round(_total_samples_written / duration, 2)
        else:
            _session_metadata["sample_rate_hz"] = 0.0

        # Get final lap count
        try:
            laps = ac.getCarState(0, acsys.CS.LapCount)
            _session_metadata["laps_completed"] = int(laps)
        except Exception:
            _session_metadata["laps_completed"] = 0

        try:
            write_final_metadata(_meta_filepath, _session_metadata)
        except IOError as e:
            _log("error", "Cannot write final metadata: %s" % str(e))

    _set_status(STATUS_IDLE)
    _log("info", "Session finalized: %d samples written" % _total_samples_written)


def acMain(ac_version):
    """AC app initialization callback."""
    global _config, _sim_info, _session_mgr, _buffer
    global _app_window, _status_label, _sample_interval, _current_log_level

    # Load config
    config_path = os.path.join(_app_dir, "config.ini")
    _config = read_config(config_path)
    _current_log_level = _log_level_map.get(_config["log_level"], 1)

    _sample_interval = 1.0 / _config["sample_rate_hz"]

    _log("info", "AC Race Engineer v%s starting" % APP_VERSION)

    # Try to load sim_info
    try:
        from sim_info import info, arch_detection_msg
        _sim_info = info
        _log("info", arch_detection_msg)
        if _sim_info is not None:
            _log("info", "sim_info loaded successfully")
        else:
            _log("warn", "sim_info not available (reduced mode)")
    except ImportError as e:
        _sim_info = None
        _log("warn", "sim_info import failed: %s (reduced mode)" % str(e))

    # Initialize components
    _fallback_mode = _sim_info is None
    set_log_func(lambda msg: _log("info", msg))
    _session_mgr = SessionManager(fallback_mode=_fallback_mode)
    if _fallback_mode:
        _log("info", "Session detection: fallback mode (speed/position heuristics)")
    _buffer = SampleBuffer(_config["buffer_size"])

    # Create AC app window
    _app_window = ac.newApp(APP_NAME)
    ac.setSize(_app_window, 200, 60)
    ac.setTitle(_app_window, "")
    ac.drawBackground(_app_window, 1)
    ac.setBackgroundOpacity(_app_window, 0.7)

    # Create status label
    _status_label = ac.addLabel(_app_window, "IDLE")
    ac.setPosition(_status_label, 10, 30)
    ac.setFontSize(_status_label, 18)
    _set_status(STATUS_IDLE)

    _log("info", "Initialization complete")
    return APP_NAME


def acUpdate(deltaT):
    """AC per-frame update callback."""
    global _last_sample_time, _error_flag

    if _error_flag:
        return

    try:
        current_time = time.time()
        car_name = ac.getCarName(0)
        track_name = ac.getTrackName(0)
        session_status = _get_session_status()

        # Gather fallback detection data when sim_info is unavailable
        _fb_kwargs = {}
        if _session_mgr.fallback_mode:
            try:
                _fb_kwargs["speed_kmh"] = ac.getCarState(0, acsys.CS.SpeedKMH)
            except Exception:
                _fb_kwargs["speed_kmh"] = 0.0
            try:
                _fb_kwargs["normalized_position"] = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
            except Exception:
                _fb_kwargs["normalized_position"] = 0.0

        if _session_mgr.state == STATE_IDLE:
            if _session_mgr.check_session_start(car_name, track_name, session_status, **_fb_kwargs):
                if _session_mgr.fallback_mode:
                    _log("info", "Session started via fallback detection (car: %s, track: %s)" % (car_name, track_name))
                else:
                    _log("info", "Session started (car: %s, track: %s)" % (car_name, track_name))
                _start_recording(car_name, track_name)

        elif _session_mgr.state == STATE_RECORDING:
            # Check for session end
            if _session_mgr.check_session_end(car_name, track_name, session_status, **_fb_kwargs):
                _finalize_session()
                _session_mgr.finalize()
                # Check if new session should start immediately
                if not _session_mgr.fallback_mode and session_status == AC_STATUS_LIVE:
                    if _session_mgr.check_session_start(car_name, track_name, session_status):
                        _start_recording(car_name, track_name)
                return

            # Sampling throttle: only read channels at configured rate
            if current_time - _last_sample_time < _sample_interval:
                return

            _last_sample_time = current_time

            # Read all channels
            sample = read_all_channels(ac, acsys, _sim_info)
            buffer_full = _buffer.append(sample)

            # Check if flush is needed
            if buffer_full or _buffer.is_flush_due(_config["flush_interval_s"]):
                _flush_buffer()

        elif _session_mgr.state == STATE_FINALIZING:
            _finalize_session()
            _session_mgr.finalize()

    except Exception:
        _log("error", "acUpdate error: %s" % traceback.format_exc())
        _set_status(STATUS_ERROR)
        _error_flag = True


def acShutdown():
    """AC app shutdown callback."""
    _log("info", "Shutting down...")
    if _session_mgr is not None and _session_mgr.state == STATE_RECORDING:
        _session_mgr.state = STATE_FINALIZING
        _finalize_session()
        _session_mgr.finalize()
    _log("info", "Shutdown complete")
