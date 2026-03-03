"""Setup file reader for AC Race Engineer.

Discovers and reads the active setup .ini file for a car/track combination.
Python 3.3 compatible.
"""
import os
import time
import glob as glob_module


def _get_setups_base_dir():
    """Get the base directory for AC setups."""
    return os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "Assetto Corsa",
        "setups"
    )


def find_active_setup(car_name, track_name):
    """Find the most likely active setup file for a car/track.

    Searches track-specific directory first, then generic car directory.

    Returns:
        tuple: (filename, contents, confidence) or (None, None, None)
        confidence: "high", "medium", "low", or None
    """
    base_dir = _get_setups_base_dir()
    now = time.time()

    # Search track-specific directory first
    track_dir = os.path.join(base_dir, car_name, track_name)
    result = _search_directory(track_dir, now, is_track_specific=True)
    if result[0] is not None:
        return result

    # Fall back to generic car directory
    car_dir = os.path.join(base_dir, car_name)
    result = _search_directory(car_dir, now, is_track_specific=False)
    if result[0] is not None:
        return result

    return (None, None, None)


def _search_directory(directory, now, is_track_specific):
    """Search a directory for setup .ini files.

    Returns (filename, contents, confidence) or (None, None, None).
    """
    if not os.path.isdir(directory):
        return (None, None, None)

    pattern = os.path.join(directory, "*.ini")
    ini_files = glob_module.glob(pattern)

    if not ini_files:
        return (None, None, None)

    # Sort by modification time, most recent first
    try:
        ini_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    except OSError:
        return (None, None, None)

    best_file = ini_files[0]
    try:
        mtime = os.path.getmtime(best_file)
    except OSError:
        return (None, None, None)

    age_seconds = now - mtime

    # Read the file contents
    try:
        with open(best_file, "r") as f:
            contents = f.read()
    except IOError:
        return (None, None, None)

    filename = os.path.basename(best_file)

    # Determine confidence
    if is_track_specific:
        if len(ini_files) == 1 and age_seconds <= 60:
            confidence = "high"
        elif age_seconds <= 600:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = "low"

    return (filename, contents, confidence)
