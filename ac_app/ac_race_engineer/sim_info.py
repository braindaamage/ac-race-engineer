"""Shared memory wrapper for Assetto Corsa telemetry.

Provides access to AC's shared memory pages via ctypes/mmap.
Falls back gracefully if _ctypes.pyd is not available.

Auto-detects 32-bit vs 64-bit Python and loads the correct _ctypes.pyd
from DLLs/Lib/ (32-bit) or DLLs/Lib64/ (64-bit).

Python 3.3 compatible.
"""

import sys
import os
import struct

# Detect Python architecture and resolve correct DLLs subfolder
_app_dir = os.path.dirname(os.path.realpath(__file__))
_ptr_size = struct.calcsize("P")

if _ptr_size == 8:
    _arch_bits = 64
    _dll_subdir = "Lib64"
else:
    _arch_bits = 32
    _dll_subdir = "Lib"

_dll_path = os.path.join(_app_dir, "DLLs", _dll_subdir)

# Module-level detection log message (logged by entry point via ac.log)
arch_detection_msg = "Python architecture: %d-bit, loading DLLs from %s/" % (_arch_bits, _dll_subdir)

if os.path.isdir(_dll_path) and _dll_path not in sys.path:
    sys.path.insert(0, _dll_path)
    os.environ["PATH"] = _dll_path + os.pathsep + os.environ.get("PATH", "")

try:
    import ctypes
    import mmap
    from ctypes import c_int32, c_float, c_wchar, Structure

    class SPageFilePhysics(Structure):
        _pack_ = 4
        _fields_ = [
            # Base fields
            ("packetId", c_int32),
            ("gas", c_float),
            ("brake", c_float),
            ("fuel", c_float),
            ("gear", c_int32),
            ("rpms", c_int32),
            ("steerAngle", c_float),
            ("speedKmh", c_float),
            ("velocity", c_float * 3),
            ("accG", c_float * 3),
            ("wheelSlip", c_float * 4),
            ("wheelLoad", c_float * 4),
            ("wheelsPressure", c_float * 4),
            ("wheelAngularSpeed", c_float * 4),
            ("tyreWear", c_float * 4),
            ("tyreDirtyLevel", c_float * 4),
            ("tyreCoreTemperature", c_float * 4),
            ("camberRAD", c_float * 4),
            ("suspensionTravel", c_float * 4),
            ("drs", c_float),
            ("tc", c_float),
            ("heading", c_float),
            ("pitch", c_float),
            ("roll", c_float),
            ("cgHeight", c_float),
            ("carDamage", c_float * 5),
            ("numberOfTyresOut", c_int32),
            ("pitLimiterOn", c_int32),
            ("abs", c_float),
            ("kersCharge", c_float),
            ("kersInput", c_float),
            ("autoShifterOn", c_int32),
            ("rideHeight", c_float * 2),
            # Extended fields (AC 1.14+)
            ("turboBoost", c_float),
            ("ballast", c_float),
            ("airDensity", c_float),
            ("airTemp", c_float),
            ("roadTemp", c_float),
            ("tyreTempI", c_float * 4),
            ("tyreTempM", c_float * 4),
            ("tyreTempO", c_float * 4),
        ]
        # Expected size: base + extended fields
        # ctypes.sizeof(SPageFilePhysics) should be verified against AC's shared memory

    class SPageFileGraphic(Structure):
        _pack_ = 4
        _fields_ = [
            ("packetId", c_int32),
            ("status", c_int32),
            ("session", c_int32),
            ("currentTime", c_wchar * 15),
            ("lastTime", c_wchar * 15),
            ("bestTime", c_wchar * 15),
            ("split", c_wchar * 15),
            ("completedLaps", c_int32),
            ("position", c_int32),
            ("iCurrentTime", c_int32),
            ("iLastTime", c_int32),
            ("iBestTime", c_int32),
            ("sessionTimeLeft", c_float),
            ("distanceTraveled", c_float),
            ("isInPit", c_int32),
            ("currentSectorIndex", c_int32),
            ("lastSectorTime", c_int32),
            ("numberOfLaps", c_int32),
            ("tyreCompound", c_wchar * 33),
            ("replayTimeMultiplier", c_float),
            ("normalizedCarPosition", c_float),
            ("carCoordinates", c_float * 3),
            ("penaltyTime", c_float),
            ("flag", c_int32),
            ("idealLineOn", c_int32),
        ]

    class SPageFileStatic(Structure):
        _pack_ = 4
        _fields_ = [
            ("_smVersion", c_wchar * 15),
            ("_acVersion", c_wchar * 15),
            ("numberOfSessions", c_int32),
            ("numCars", c_int32),
            ("carModel", c_wchar * 33),
            ("track", c_wchar * 33),
            ("playerName", c_wchar * 33),
            ("playerSurname", c_wchar * 33),
            ("playerNick", c_wchar * 33),
            ("sectorCount", c_int32),
            ("maxTorque", c_float),
            ("maxPower", c_float),
            ("maxRpm", c_int32),
            ("maxFuel", c_float),
            ("suspensionMaxTravel", c_float * 4),
            ("tyreRadius", c_float * 4),
            ("airTemp", c_float),
            ("roadTemp", c_float),
        ]

    class SimInfo(object):
        def __init__(self):
            self._physics_size = ctypes.sizeof(SPageFilePhysics)
            self._graphics_size = ctypes.sizeof(SPageFileGraphic)
            self._static_size = ctypes.sizeof(SPageFileStatic)

            self._physics_map = mmap.mmap(0, self._physics_size, "acpmf_physics")
            self._graphics_map = mmap.mmap(0, self._graphics_size, "acpmf_graphics")
            self._static_map = mmap.mmap(0, self._static_size, "acpmf_static")

            self.physics = SPageFilePhysics.from_buffer(self._physics_map)
            self.graphics = SPageFileGraphic.from_buffer(self._graphics_map)
            self.static = SPageFileStatic.from_buffer(self._static_map)

        def close(self):
            self._physics_map.close()
            self._graphics_map.close()
            self._static_map.close()

        def __del__(self):
            self.close()

    info = SimInfo()

except ImportError:
    info = None
except Exception:
    # mmap may fail outside of AC (e.g., during development/testing)
    info = None
