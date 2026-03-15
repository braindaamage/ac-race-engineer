"""AC asset metadata reader — car/track display names, badges, previews."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel


class CarInfo(BaseModel):
    """Human-readable car metadata from ui_car.json."""

    display_name: str
    brand: str = ""
    car_class: str = ""


class TrackInfo(BaseModel):
    """Human-readable track metadata from ui_track.json."""

    display_name: str
    country: str = ""
    length_m: float | None = None


def _validate_identifier(name: str) -> None:
    """Reject identifiers that contain path traversal sequences."""
    if not name or ".." in name or "/" in name or "\\" in name:
        raise ValueError(f"Invalid identifier: {name!r}")


def _format_name(raw_id: str) -> str:
    """Format a raw folder name into a human-readable string."""
    formatted = raw_id
    for prefix in ("ks_", "ac_"):
        if formatted.startswith(prefix):
            formatted = formatted[len(prefix):]
            break
    return formatted.replace("_", " ")


def _parse_length(value: str) -> float | None:
    """Parse a length string like '5793 m' or '5.793 km' into meters."""
    match = re.match(r"([\d.]+)\s*(.*)", value.strip())
    if not match:
        return None
    try:
        num = float(match.group(1))
    except ValueError:
        return None
    unit = match.group(2).strip().lower()
    if unit == "km":
        return num * 1000
    return num


def read_car_info(ac_cars_path: str | Path | None, car_name: str) -> CarInfo:
    """Read car metadata from ui_car.json. Falls back to formatted name on any error."""
    if ac_cars_path is None:
        return CarInfo(display_name=_format_name(car_name))
    try:
        _validate_identifier(car_name)
        json_path = Path(ac_cars_path) / car_name / "ui" / "ui_car.json"
        with open(json_path, encoding="utf-8-sig") as f:
            data = json.load(f)
        return CarInfo(
            display_name=data.get("name", _format_name(car_name)),
            brand=data.get("brand", ""),
            car_class=data.get("class", ""),
        )
    except Exception:
        return CarInfo(display_name=_format_name(car_name))


def read_track_info(
    ac_tracks_path: str | Path | None,
    track_name: str,
    track_config: str = "",
) -> TrackInfo:
    """Read track metadata from ui_track.json. Layout-aware."""
    if ac_tracks_path is None:
        return TrackInfo(display_name=_format_name(track_name))
    try:
        _validate_identifier(track_name)
        if track_config:
            _validate_identifier(track_config)
        base = Path(ac_tracks_path) / track_name / "ui"
        if track_config:
            json_path = base / f"layout_{track_config}" / "ui_track.json"
        else:
            json_path = base / "ui_track.json"
        with open(json_path, encoding="utf-8-sig") as f:
            data = json.load(f)
        length_m = None
        if "length" in data:
            length_m = _parse_length(str(data["length"]))
        return TrackInfo(
            display_name=data.get("name", _format_name(track_name)),
            country=data.get("country", ""),
            length_m=length_m,
        )
    except Exception:
        return TrackInfo(display_name=_format_name(track_name))


def car_badge_path(ac_cars_path: str | Path | None, car_name: str) -> Path | None:
    """Return path to badge.png if it exists, else None."""
    if ac_cars_path is None:
        return None
    try:
        _validate_identifier(car_name)
    except ValueError:
        return None
    p = Path(ac_cars_path) / car_name / "ui" / "badge.png"
    return p if p.is_file() else None


def track_preview_path(
    ac_tracks_path: str | Path | None,
    track_name: str,
    track_config: str = "",
) -> Path | None:
    """Return path to preview.png if it exists. Layout-aware."""
    if ac_tracks_path is None:
        return None
    try:
        _validate_identifier(track_name)
        if track_config:
            _validate_identifier(track_config)
    except ValueError:
        return None
    base = Path(ac_tracks_path) / track_name / "ui"
    if track_config:
        p = base / f"layout_{track_config}" / "preview.png"
    else:
        p = base / "preview.png"
    return p if p.is_file() else None
