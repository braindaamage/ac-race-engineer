"""Track asset endpoints — preview images."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from ac_engineer.config.io import read_config
from ac_engineer.resolver.ac_assets import _validate_identifier, track_preview_path

router = APIRouter()


@router.get("/{track_name}/preview")
def get_track_preview(track_name: str, request: Request, config: str = ""):
    """Serve the track preview image from the AC install directory."""
    try:
        _validate_identifier(track_name)
        if config:
            _validate_identifier(config)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid track name or config: {track_name} (config: {config})",
        )
    cfg = read_config(request.app.state.config_path)
    preview = track_preview_path(cfg.ac_tracks_path, track_name, config)
    if preview is None:
        raise HTTPException(
            status_code=404,
            detail=f"Preview not found for track: {track_name} (config: {config})",
        )
    return FileResponse(
        str(preview),
        media_type="image/png",
        headers={"Cache-Control": "max-age=86400"},
    )
