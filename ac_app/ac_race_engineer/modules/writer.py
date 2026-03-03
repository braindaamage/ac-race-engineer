"""CSV and JSON writer for AC Race Engineer.

Handles writing telemetry data to CSV files and metadata to JSON sidecar files.
Python 3.3 compatible.
"""
import csv
import json
import os
import time

from sanitize import sanitize_name


def generate_filename(car, track, timestamp=None):
    """Generate a session filename from car/track names and timestamp.

    Pattern: {date}_{time}_{car}_{track}
    Example: 2026-03-02_1430_ks_ferrari_488_gt3_monza

    Args:
        car: raw car name from AC
        track: raw track name from AC
        timestamp: optional time.time() value (defaults to now)

    Returns:
        base filename without extension
    """
    if timestamp is None:
        timestamp = time.time()

    time_struct = time.localtime(timestamp)
    date_str = time.strftime("%Y-%m-%d", time_struct)
    time_str = time.strftime("%H%M", time_struct)

    car_clean = sanitize_name(car) if car else "unknown"
    track_clean = sanitize_name(track) if track else "unknown"

    if not car_clean:
        car_clean = "unknown"
    if not track_clean:
        track_clean = "unknown"

    # Truncate long names
    if len(car_clean) > 50:
        car_clean = car_clean[:50].rstrip("_")
    if len(track_clean) > 50:
        track_clean = track_clean[:50].rstrip("_")

    return "%s_%s_%s_%s" % (date_str, time_str, car_clean, track_clean)


def ensure_output_dir(path):
    """Create the output directory if it doesn't exist."""
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def write_csv_header(filepath, header_list):
    """Write the CSV header row to a new file."""
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f, lineterminator="\r\n")
        writer.writerow(header_list)


def append_csv_rows(filepath, rows):
    """Append data rows to an existing CSV file."""
    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f, lineterminator="\r\n")
        writer.writerows(rows)


def write_metadata(filepath, metadata_dict):
    """Write session metadata to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(metadata_dict, f, indent=2)


def write_early_metadata(filepath, metadata_dict):
    """Write early metadata at session start (deferred fields set to null)."""
    early = dict(metadata_dict)
    early["session_end"] = None
    early["laps_completed"] = None
    early["total_samples"] = None
    early["sample_rate_hz"] = None
    write_metadata(filepath, early)


def write_final_metadata(filepath, metadata_dict):
    """Write final metadata at session end (all fields populated)."""
    write_metadata(filepath, metadata_dict)
