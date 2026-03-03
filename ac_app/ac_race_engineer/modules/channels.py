"""Channel definitions and telemetry reading for AC Race Engineer.

Defines all telemetry channels and provides a function to read all
channels in a single call. Includes graceful degradation for missing
channels, reduced mode, and tyre temp zone validation.
Python 3.3 compatible.
"""

import time
import math

_NAN = float("nan")

# Reduced mode: set to True if sim_info fails to load
reduced_mode = False

# Tyre temp zone validation
tyre_temp_zones_validated = False
_tyre_zone_check_done = False

# Channel availability tracking
channels_available = []
channels_unavailable = []
_availability_checked = False

# Track which channels have already logged a failure (avoid log spam)
_failed_channels = set()

# Logger callback (set by entry point to use ac.log)
_log_func = None


def set_log_func(func):
    """Set the logging function (called by entry point)."""
    global _log_func
    _log_func = func


def _log(msg):
    """Log a message via the configured log function."""
    if _log_func is not None:
        _log_func(msg)


def init_reduced_mode(sim_info_obj):
    """Initialize reduced mode based on sim_info availability."""
    global reduced_mode
    reduced_mode = (sim_info_obj is None)
    if reduced_mode:
        _log("WARNING: sim_info not available - running in reduced mode (29 channels will return NaN)")
        # Log which channels are unavailable in reduced mode
        unavailable = [ch["name"] for ch in CHANNEL_DEFINITIONS if ch["source"] == "sim_info"]
        _log("Unavailable channels in reduced mode: %s" % ", ".join(unavailable))


def reset_session_state():
    """Reset per-session state (channel tracking, zone validation, etc.)."""
    global _tyre_zone_check_done, _availability_checked
    global channels_available, channels_unavailable, tyre_temp_zones_validated
    _failed_channels.clear()
    _tyre_zone_check_done = False
    _availability_checked = False
    channels_available = []
    channels_unavailable = []
    tyre_temp_zones_validated = False

CHANNEL_DEFINITIONS = [
    # Timing
    {"name": "timestamp", "source": "computed", "reader_key": "timestamp", "index": None, "fallback": 0.0},
    {"name": "session_time_ms", "source": "computed", "reader_key": "session_time_ms", "index": None, "fallback": 0.0},
    {"name": "normalized_position", "source": "ac_state", "reader_key": "NormalizedSplinePosition", "index": None, "fallback": _NAN},
    {"name": "lap_count", "source": "ac_state", "reader_key": "LapCount", "index": None, "fallback": 0},
    {"name": "lap_time_ms", "source": "ac_state", "reader_key": "LapTime", "index": None, "fallback": _NAN},
    # Inputs
    {"name": "throttle", "source": "ac_state", "reader_key": "Gas", "index": None, "fallback": _NAN},
    {"name": "brake", "source": "ac_state", "reader_key": "Brake", "index": None, "fallback": _NAN},
    {"name": "steering", "source": "ac_state", "reader_key": "Steer", "index": None, "fallback": _NAN},
    {"name": "gear", "source": "ac_state", "reader_key": "Gear", "index": None, "fallback": 0},
    {"name": "clutch", "source": "ac_state", "reader_key": "Clutch", "index": None, "fallback": _NAN},
    {"name": "handbrake", "source": "none", "reader_key": None, "index": None, "fallback": _NAN},
    # Dynamics
    {"name": "speed_kmh", "source": "ac_state", "reader_key": "SpeedKMH", "index": None, "fallback": _NAN},
    {"name": "rpm", "source": "ac_state", "reader_key": "RPM", "index": None, "fallback": _NAN},
    {"name": "g_lat", "source": "ac_state", "reader_key": "AccG", "index": 0, "fallback": _NAN},
    {"name": "g_lon", "source": "ac_state", "reader_key": "AccG", "index": 2, "fallback": _NAN},
    {"name": "g_vert", "source": "ac_state", "reader_key": "AccG", "index": 1, "fallback": _NAN},
    {"name": "yaw_rate", "source": "ac_state", "reader_key": "LocalAngularVelocity", "index": 1, "fallback": _NAN},
    {"name": "local_vel_x", "source": "ac_state", "reader_key": "LocalVelocity", "index": 0, "fallback": _NAN},
    {"name": "local_vel_y", "source": "ac_state", "reader_key": "LocalVelocity", "index": 1, "fallback": _NAN},
    {"name": "local_vel_z", "source": "ac_state", "reader_key": "LocalVelocity", "index": 2, "fallback": _NAN},
    # Tyre temp core (4)
    {"name": "tyre_temp_core_fl", "source": "ac_state", "reader_key": "CurrentTyresCoreTemp", "index": 0, "fallback": _NAN},
    {"name": "tyre_temp_core_fr", "source": "ac_state", "reader_key": "CurrentTyresCoreTemp", "index": 1, "fallback": _NAN},
    {"name": "tyre_temp_core_rl", "source": "ac_state", "reader_key": "CurrentTyresCoreTemp", "index": 2, "fallback": _NAN},
    {"name": "tyre_temp_core_rr", "source": "ac_state", "reader_key": "CurrentTyresCoreTemp", "index": 3, "fallback": _NAN},
    # Tyre temp inner (4) - sim_info only
    {"name": "tyre_temp_inner_fl", "source": "sim_info", "reader_key": "physics.tyreTempI", "index": 0, "fallback": _NAN},
    {"name": "tyre_temp_inner_fr", "source": "sim_info", "reader_key": "physics.tyreTempI", "index": 1, "fallback": _NAN},
    {"name": "tyre_temp_inner_rl", "source": "sim_info", "reader_key": "physics.tyreTempI", "index": 2, "fallback": _NAN},
    {"name": "tyre_temp_inner_rr", "source": "sim_info", "reader_key": "physics.tyreTempI", "index": 3, "fallback": _NAN},
    # Tyre temp mid (4) - sim_info only
    {"name": "tyre_temp_mid_fl", "source": "sim_info", "reader_key": "physics.tyreTempM", "index": 0, "fallback": _NAN},
    {"name": "tyre_temp_mid_fr", "source": "sim_info", "reader_key": "physics.tyreTempM", "index": 1, "fallback": _NAN},
    {"name": "tyre_temp_mid_rl", "source": "sim_info", "reader_key": "physics.tyreTempM", "index": 2, "fallback": _NAN},
    {"name": "tyre_temp_mid_rr", "source": "sim_info", "reader_key": "physics.tyreTempM", "index": 3, "fallback": _NAN},
    # Tyre temp outer (4) - sim_info only
    {"name": "tyre_temp_outer_fl", "source": "sim_info", "reader_key": "physics.tyreTempO", "index": 0, "fallback": _NAN},
    {"name": "tyre_temp_outer_fr", "source": "sim_info", "reader_key": "physics.tyreTempO", "index": 1, "fallback": _NAN},
    {"name": "tyre_temp_outer_rl", "source": "sim_info", "reader_key": "physics.tyreTempO", "index": 2, "fallback": _NAN},
    {"name": "tyre_temp_outer_rr", "source": "sim_info", "reader_key": "physics.tyreTempO", "index": 3, "fallback": _NAN},
    # Tyre pressure (4)
    {"name": "tyre_pressure_fl", "source": "ac_state", "reader_key": "DynamicPressure", "index": 0, "fallback": _NAN},
    {"name": "tyre_pressure_fr", "source": "ac_state", "reader_key": "DynamicPressure", "index": 1, "fallback": _NAN},
    {"name": "tyre_pressure_rl", "source": "ac_state", "reader_key": "DynamicPressure", "index": 2, "fallback": _NAN},
    {"name": "tyre_pressure_rr", "source": "ac_state", "reader_key": "DynamicPressure", "index": 3, "fallback": _NAN},
    # Slip angle (4)
    {"name": "slip_angle_fl", "source": "ac_state", "reader_key": "SlipAngle", "index": 0, "fallback": _NAN},
    {"name": "slip_angle_fr", "source": "ac_state", "reader_key": "SlipAngle", "index": 1, "fallback": _NAN},
    {"name": "slip_angle_rl", "source": "ac_state", "reader_key": "SlipAngle", "index": 2, "fallback": _NAN},
    {"name": "slip_angle_rr", "source": "ac_state", "reader_key": "SlipAngle", "index": 3, "fallback": _NAN},
    # Slip ratio (4)
    {"name": "slip_ratio_fl", "source": "ac_state", "reader_key": "SlipRatio", "index": 0, "fallback": _NAN},
    {"name": "slip_ratio_fr", "source": "ac_state", "reader_key": "SlipRatio", "index": 1, "fallback": _NAN},
    {"name": "slip_ratio_rl", "source": "ac_state", "reader_key": "SlipRatio", "index": 2, "fallback": _NAN},
    {"name": "slip_ratio_rr", "source": "ac_state", "reader_key": "SlipRatio", "index": 3, "fallback": _NAN},
    # Tyre wear (4) - sim_info only
    {"name": "tyre_wear_fl", "source": "sim_info", "reader_key": "physics.tyreWear", "index": 0, "fallback": _NAN},
    {"name": "tyre_wear_fr", "source": "sim_info", "reader_key": "physics.tyreWear", "index": 1, "fallback": _NAN},
    {"name": "tyre_wear_rl", "source": "sim_info", "reader_key": "physics.tyreWear", "index": 2, "fallback": _NAN},
    {"name": "tyre_wear_rr", "source": "sim_info", "reader_key": "physics.tyreWear", "index": 3, "fallback": _NAN},
    # Tyre dirty (4)
    {"name": "tyre_dirty_fl", "source": "ac_state", "reader_key": "TyreDirtyLevel", "index": 0, "fallback": _NAN},
    {"name": "tyre_dirty_fr", "source": "ac_state", "reader_key": "TyreDirtyLevel", "index": 1, "fallback": _NAN},
    {"name": "tyre_dirty_rl", "source": "ac_state", "reader_key": "TyreDirtyLevel", "index": 2, "fallback": _NAN},
    {"name": "tyre_dirty_rr", "source": "ac_state", "reader_key": "TyreDirtyLevel", "index": 3, "fallback": _NAN},
    # Wheel speed (4)
    {"name": "wheel_speed_fl", "source": "ac_state", "reader_key": "WheelAngularSpeed", "index": 0, "fallback": _NAN},
    {"name": "wheel_speed_fr", "source": "ac_state", "reader_key": "WheelAngularSpeed", "index": 1, "fallback": _NAN},
    {"name": "wheel_speed_rl", "source": "ac_state", "reader_key": "WheelAngularSpeed", "index": 2, "fallback": _NAN},
    {"name": "wheel_speed_rr", "source": "ac_state", "reader_key": "WheelAngularSpeed", "index": 3, "fallback": _NAN},
    # Suspension travel (4)
    {"name": "susp_travel_fl", "source": "ac_state", "reader_key": "SuspensionTravel", "index": 0, "fallback": _NAN},
    {"name": "susp_travel_fr", "source": "ac_state", "reader_key": "SuspensionTravel", "index": 1, "fallback": _NAN},
    {"name": "susp_travel_rl", "source": "ac_state", "reader_key": "SuspensionTravel", "index": 2, "fallback": _NAN},
    {"name": "susp_travel_rr", "source": "ac_state", "reader_key": "SuspensionTravel", "index": 3, "fallback": _NAN},
    # Wheel load (4) - sim_info only
    {"name": "wheel_load_fl", "source": "sim_info", "reader_key": "physics.wheelLoad", "index": 0, "fallback": _NAN},
    {"name": "wheel_load_fr", "source": "sim_info", "reader_key": "physics.wheelLoad", "index": 1, "fallback": _NAN},
    {"name": "wheel_load_rl", "source": "sim_info", "reader_key": "physics.wheelLoad", "index": 2, "fallback": _NAN},
    {"name": "wheel_load_rr", "source": "sim_info", "reader_key": "physics.wheelLoad", "index": 3, "fallback": _NAN},
    # World position (3)
    {"name": "world_pos_x", "source": "ac_state", "reader_key": "WorldPosition", "index": 0, "fallback": _NAN},
    {"name": "world_pos_y", "source": "ac_state", "reader_key": "WorldPosition", "index": 1, "fallback": _NAN},
    {"name": "world_pos_z", "source": "ac_state", "reader_key": "WorldPosition", "index": 2, "fallback": _NAN},
    # Car state
    {"name": "turbo_boost", "source": "ac_state", "reader_key": "TurboBoost", "index": None, "fallback": _NAN},
    {"name": "drs", "source": "sim_info", "reader_key": "physics.drs", "index": None, "fallback": _NAN},
    {"name": "ers_charge", "source": "sim_info", "reader_key": "physics.kersCharge", "index": None, "fallback": _NAN},
    {"name": "fuel", "source": "sim_info", "reader_key": "physics.fuel", "index": None, "fallback": _NAN},
    {"name": "damage_front", "source": "sim_info", "reader_key": "physics.carDamage", "index": 0, "fallback": _NAN},
    {"name": "damage_rear", "source": "sim_info", "reader_key": "physics.carDamage", "index": 1, "fallback": _NAN},
    {"name": "damage_left", "source": "sim_info", "reader_key": "physics.carDamage", "index": 2, "fallback": _NAN},
    {"name": "damage_right", "source": "sim_info", "reader_key": "physics.carDamage", "index": 3, "fallback": _NAN},
    {"name": "damage_center", "source": "sim_info", "reader_key": "physics.carDamage", "index": 4, "fallback": _NAN},
    # Flags
    {"name": "in_pit_lane", "source": "ac_func", "reader_key": "isCarInPitlane", "index": None, "fallback": 0},
    {"name": "lap_invalid", "source": "ac_state", "reader_key": "LapInvalidated", "index": None, "fallback": 0},
]

# CSV header in exact column order
HEADER = [ch["name"] for ch in CHANNEL_DEFINITIONS]

# Session start time, set by entry point
_session_start_time = [0.0]


def set_session_start_time(t):
    """Set the session start time for session_time_ms computation."""
    _session_start_time[0] = t


def _read_ac_state(ac_module, acsys_module, reader_key, index):
    """Read a value from ac.getCarState()."""
    cs_const = getattr(acsys_module.CS, reader_key)
    value = ac_module.getCarState(0, cs_const)
    if index is not None:
        return value[index]
    return value


def _read_sim_info(sim_info_obj, reader_key, index):
    """Read a value from sim_info shared memory."""
    if sim_info_obj is None:
        return _NAN
    # reader_key format: "physics.fieldName" or "graphics.fieldName"
    parts = reader_key.split(".")
    obj = sim_info_obj
    for part in parts:
        obj = getattr(obj, part)
    if index is not None:
        return obj[index]
    return obj


def _read_ac_func(ac_module, reader_key):
    """Read a value from an ac module function."""
    func = getattr(ac_module, reader_key)
    return func(0)


def _check_tyre_temp_zones(values):
    """Validate tyre temp zone readings after first sample.

    If all 12 inner/mid/outer temps are exactly 0.0, zones are unavailable.
    """
    global tyre_temp_zones_validated, _tyre_zone_check_done
    if _tyre_zone_check_done:
        return
    _tyre_zone_check_done = True

    # Indices for tyre_temp_inner/mid/outer channels (12 total)
    zone_names = []
    zone_indices = []
    for i, ch in enumerate(CHANNEL_DEFINITIONS):
        if ch["name"].startswith("tyre_temp_inner_") or \
           ch["name"].startswith("tyre_temp_mid_") or \
           ch["name"].startswith("tyre_temp_outer_"):
            zone_names.append(ch["name"])
            zone_indices.append(i)

    zone_values = [values[i] for i in zone_indices]

    # Check if all are exactly 0.0 (not NaN)
    all_zero = all(v == 0.0 for v in zone_values)
    any_nan = any(isinstance(v, float) and math.isnan(v) for v in zone_values)

    if all_zero and not any_nan:
        tyre_temp_zones_validated = False
        _log("Tyre temp zones all read 0.0 - zone data unavailable, using NaN")
        # Replace zone values with NaN
        for i in zone_indices:
            values[i] = _NAN
    elif any_nan:
        tyre_temp_zones_validated = False
    else:
        tyre_temp_zones_validated = True


def _update_availability(values):
    """Track which channels returned valid data vs NaN after first sample."""
    global channels_available, channels_unavailable, _availability_checked
    if _availability_checked:
        return
    _availability_checked = True

    channels_available = []
    channels_unavailable = []
    for i, ch in enumerate(CHANNEL_DEFINITIONS):
        val = values[i]
        if isinstance(val, float) and math.isnan(val):
            channels_unavailable.append(ch["name"])
        else:
            channels_available.append(ch["name"])


def read_all_channels(ac_module, acsys_module, sim_info_obj):
    """Read all channels and return a list of values in header order.

    Each channel read is wrapped in try/except. Failures return the
    channel's fallback value (typically NaN). First failure per channel
    is logged to avoid log spam.

    Args:
        ac_module: the ac module (or mock)
        acsys_module: the acsys module (or mock)
        sim_info_obj: sim_info.info object (or None)

    Returns:
        list of values in HEADER order
    """
    now = time.time()
    values = []

    for ch in CHANNEL_DEFINITIONS:
        source = ch["source"]
        name = ch["name"]
        reader_key = ch["reader_key"]
        index = ch["index"]
        fallback = ch["fallback"]

        try:
            if source == "computed":
                if reader_key == "timestamp":
                    values.append(now)
                elif reader_key == "session_time_ms":
                    values.append((now - _session_start_time[0]) * 1000.0)
                else:
                    values.append(fallback)
            elif source == "ac_state":
                values.append(_read_ac_state(ac_module, acsys_module, reader_key, index))
            elif source == "sim_info":
                values.append(_read_sim_info(sim_info_obj, reader_key, index))
            elif source == "ac_func":
                values.append(_read_ac_func(ac_module, reader_key))
            elif source == "none":
                values.append(fallback)
            else:
                values.append(fallback)
        except Exception as e:
            # Log first failure per channel
            if name not in _failed_channels:
                _failed_channels.add(name)
                _log("Channel '%s' read failed: %s" % (name, str(e)))
            values.append(fallback)

    # Post-read validations (first sample only)
    _check_tyre_temp_zones(values)
    _update_availability(values)

    return values
