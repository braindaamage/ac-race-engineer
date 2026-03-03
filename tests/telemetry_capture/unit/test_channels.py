"""Unit tests for channels module."""
import math
import sys

from channels import (
    HEADER, CHANNEL_DEFINITIONS, read_all_channels, set_session_start_time,
    reset_session_state, init_reduced_mode, reduced_mode,
    channels_available, channels_unavailable, tyre_temp_zones_validated,
)
import channels as channels_mod


# Expected CSV column order from contracts/csv-output.md
EXPECTED_HEADER = [
    "timestamp", "session_time_ms", "normalized_position", "lap_count", "lap_time_ms",
    "throttle", "brake", "steering", "gear", "clutch", "handbrake",
    "speed_kmh", "rpm", "g_lat", "g_lon", "g_vert", "yaw_rate",
    "local_vel_x", "local_vel_y", "local_vel_z",
    "tyre_temp_core_fl", "tyre_temp_core_fr", "tyre_temp_core_rl", "tyre_temp_core_rr",
    "tyre_temp_inner_fl", "tyre_temp_inner_fr", "tyre_temp_inner_rl", "tyre_temp_inner_rr",
    "tyre_temp_mid_fl", "tyre_temp_mid_fr", "tyre_temp_mid_rl", "tyre_temp_mid_rr",
    "tyre_temp_outer_fl", "tyre_temp_outer_fr", "tyre_temp_outer_rl", "tyre_temp_outer_rr",
    "tyre_pressure_fl", "tyre_pressure_fr", "tyre_pressure_rl", "tyre_pressure_rr",
    "slip_angle_fl", "slip_angle_fr", "slip_angle_rl", "slip_angle_rr",
    "slip_ratio_fl", "slip_ratio_fr", "slip_ratio_rl", "slip_ratio_rr",
    "tyre_wear_fl", "tyre_wear_fr", "tyre_wear_rl", "tyre_wear_rr",
    "tyre_dirty_fl", "tyre_dirty_fr", "tyre_dirty_rl", "tyre_dirty_rr",
    "wheel_speed_fl", "wheel_speed_fr", "wheel_speed_rl", "wheel_speed_rr",
    "susp_travel_fl", "susp_travel_fr", "susp_travel_rl", "susp_travel_rr",
    "wheel_load_fl", "wheel_load_fr", "wheel_load_rl", "wheel_load_rr",
    "world_pos_x", "world_pos_y", "world_pos_z",
    "turbo_boost", "drs", "ers_charge", "fuel",
    "damage_front", "damage_rear", "damage_left", "damage_right", "damage_center",
    "in_pit_lane", "lap_invalid",
]


class TestChannelDefinitions:
    def test_header_count_matches_definitions(self):
        # Contract CSV header has 82 columns (spec text said 76 but the
        # detailed contract/data-model enumerates 82 individual channels)
        assert len(HEADER) == len(EXPECTED_HEADER)
        assert len(HEADER) == len(CHANNEL_DEFINITIONS)

    def test_header_matches_contract_order(self):
        assert HEADER == EXPECTED_HEADER

    def test_definitions_cover_all_channels(self):
        assert len(CHANNEL_DEFINITIONS) == len(EXPECTED_HEADER)

    def test_all_definitions_have_required_keys(self):
        required_keys = {"name", "source", "reader_key", "index", "fallback"}
        for ch in CHANNEL_DEFINITIONS:
            assert required_keys.issubset(set(ch.keys())), "Missing keys in %s" % ch["name"]


class TestReadAllChannels:
    def test_returns_correct_length(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        set_session_start_time(0.0)
        values = read_all_channels(ac_mod, acsys_mod, None)
        assert len(values) == len(HEADER)

    def test_timestamp_is_set(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        set_session_start_time(0.0)
        values = read_all_channels(ac_mod, acsys_mod, None)
        # timestamp should be a positive number (unix epoch)
        assert values[0] > 0

    def test_sim_info_none_returns_nan_for_sim_info_channels(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        set_session_start_time(0.0)
        values = read_all_channels(ac_mod, acsys_mod, None)
        # Check sim_info-only channels return NaN when sim_info is None
        # tyre_temp_inner_fl is index 24
        assert math.isnan(values[24])
        # fuel is index 73
        assert math.isnan(values[73])

    def test_scalar_channel_read(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        ac_mod.configure_car_state(acsys_mod.CS.SpeedKMH, 185.5)
        set_session_start_time(0.0)
        values = read_all_channels(ac_mod, acsys_mod, None)
        # speed_kmh is at index 11
        assert values[11] == 185.5
        ac_mod.reset()

    def test_indexed_channel_read(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        ac_mod.configure_car_state(acsys_mod.CS.AccG, (0.5, 1.0, -0.3))
        set_session_start_time(0.0)
        reset_session_state()
        values = read_all_channels(ac_mod, acsys_mod, None)
        # g_lat = AccG[0] at index 13
        assert values[13] == 0.5
        # g_lon = AccG[2] at index 14
        assert values[14] == -0.3
        # g_vert = AccG[1] at index 15
        assert values[15] == 1.0
        ac_mod.reset()


class TestChannelExceptionHandling:
    """T022/T026: Channel read failures produce NaN fallback."""

    def test_channel_exception_produces_nan(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]

        # Make getCarState raise an exception for a specific channel
        original = ac_mod.getCarState
        def raising_getCarState(carIndex, channel):
            if channel == acsys_mod.CS.SpeedKMH:
                raise RuntimeError("Simulated failure")
            return original(carIndex, channel)

        ac_mod.getCarState = raising_getCarState
        set_session_start_time(0.0)
        reset_session_state()
        values = read_all_channels(ac_mod, acsys_mod, None)
        # speed_kmh at index 11 should be NaN (its fallback)
        assert math.isnan(values[11])
        ac_mod.getCarState = original
        ac_mod.reset()


class TestReducedMode:
    """T023/T026: Reduced mode when sim_info is None."""

    def test_reduced_mode_sets_sim_info_channels_to_nan(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        set_session_start_time(0.0)
        reset_session_state()
        init_reduced_mode(None)
        assert channels_mod.reduced_mode is True

        values = read_all_channels(ac_mod, acsys_mod, None)
        # Count sim_info channels that should be NaN
        sim_info_indices = [
            i for i, ch in enumerate(CHANNEL_DEFINITIONS)
            if ch["source"] == "sim_info"
        ]
        for idx in sim_info_indices:
            assert math.isnan(values[idx]), "sim_info channel at index %d should be NaN" % idx

        # Non-sim_info channels should still work
        # e.g., speed_kmh at index 11 (ac_state source)
        assert not math.isnan(values[11]) or values[11] == 0.0


class TestTyreTempZoneValidation:
    """T024/T026: Tyre temp zone validation."""

    def test_availability_tracking(self):
        ac_mod = sys.modules["ac"]
        acsys_mod = sys.modules["acsys"]
        set_session_start_time(0.0)
        reset_session_state()
        read_all_channels(ac_mod, acsys_mod, None)
        # After first read, availability should be tracked
        assert len(channels_mod.channels_available) > 0 or len(channels_mod.channels_unavailable) > 0
        # handbrake should always be unavailable (source="none", fallback=NaN)
        assert "handbrake" in channels_mod.channels_unavailable
