"""Core tier evaluation and orchestration for parameter resolution."""

from __future__ import annotations

import configparser
import io
import logging
from datetime import datetime, timezone
from pathlib import Path

from ac_engineer.engineer.models import ParameterRange

from .defaults import extract_defaults
from .models import CarStatus, ResolvedParameters, ResolutionTier

logger = logging.getLogger(__name__)


def _parse_setup_ini(content: str) -> dict[str, ParameterRange]:
    """Parse setup.ini content into parameter ranges."""
    cp = configparser.ConfigParser(comment_prefixes=(";", "#", "/"))
    cp.optionxform = str
    cp.read_file(io.StringIO(content))

    ranges: dict[str, ParameterRange] = {}
    for section in cp.sections():
        try:
            min_val = float(cp.get(section, "MIN"))
            max_val = float(cp.get(section, "MAX"))
            step_val = float(cp.get(section, "STEP"))
        except (configparser.NoOptionError, ValueError):
            continue

        if step_val <= 0 or min_val > max_val:
            continue

        default_val = None
        try:
            default_val = float(cp.get(section, "DEFAULT"))
        except (configparser.NoOptionError, ValueError):
            pass

        ranges[section] = ParameterRange(
            section=section,
            parameter="VALUE",
            min_value=min_val,
            max_value=max_val,
            step=step_val,
            default_value=default_val,
        )

    return ranges


def _resolve_tier1(
    ac_install_path: Path, car_name: str
) -> dict[str, ParameterRange] | None:
    """Tier 1: Read from open data/ folder."""
    data_dir = ac_install_path / "content" / "cars" / car_name / "data"
    setup_ini = data_dir / "setup.ini"

    if not setup_ini.is_file():
        return None

    try:
        content = setup_ini.read_text(encoding="utf-8")
    except OSError:
        logger.debug("Failed to read %s", setup_ini)
        return None

    ranges = _parse_setup_ini(content)
    if not ranges:
        return None

    # Read config files for defaults
    config_files: dict[str, str] = {}
    for fname in ("suspensions.ini", "tyres.ini", "aero.ini", "drivetrain.ini", "brakes.ini"):
        fpath = data_dir / fname
        if fpath.is_file():
            try:
                config_files[fname] = fpath.read_text(encoding="utf-8")
            except OSError:
                pass

    defaults = extract_defaults(config_files, list(ranges.keys()))
    for section, default_val in defaults.items():
        if default_val is not None and section in ranges:
            rng = ranges[section]
            ranges[section] = rng.model_copy(update={"default_value": default_val})

    return ranges


def _resolve_tier2(
    ac_install_path: Path, car_name: str
) -> dict[str, ParameterRange] | None:
    """Tier 2: Extract from encrypted data.acd archive."""
    acd_path = ac_install_path / "content" / "cars" / car_name / "data.acd"

    if not acd_path.is_file():
        return None

    try:
        from ac_engineer.acd_reader import read_acd

        result = read_acd(acd_path, car_name)
    except Exception:
        logger.debug("ACD reader failed for %s", car_name, exc_info=True)
        return None

    if not result.ok:
        return None

    # Extract setup.ini from archive
    setup_bytes = result.files.get("setup.ini")
    if setup_bytes is None:
        return None

    try:
        setup_content = setup_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None

    ranges = _parse_setup_ini(setup_content)
    if not ranges:
        return None

    # Extract config files for defaults
    config_files: dict[str, str] = {}
    for fname in ("suspensions.ini", "tyres.ini", "aero.ini", "drivetrain.ini", "brakes.ini"):
        file_bytes = result.files.get(fname)
        if file_bytes is not None:
            try:
                config_files[fname] = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                pass

    defaults = extract_defaults(config_files, list(ranges.keys()))
    for section, default_val in defaults.items():
        if default_val is not None and section in ranges:
            rng = ranges[section]
            ranges[section] = rng.model_copy(update={"default_value": default_val})

    return ranges


def _resolve_tier3(
    session_setup: dict[str, dict[str, float | str]] | None,
) -> dict[str, ParameterRange]:
    """Tier 3: Infer ranges from session's active setup values."""
    if session_setup is None:
        return {}

    ranges: dict[str, ParameterRange] = {}
    for section, params in session_setup.items():
        value = params.get("VALUE")
        if value is None:
            continue
        if not isinstance(value, (int, float)):
            continue
        val = float(value)
        ranges[section] = ParameterRange(
            section=section,
            parameter="VALUE",
            min_value=val,
            max_value=val,
            step=1,
            default_value=None,
        )

    return ranges


def resolve_parameters(
    ac_install_path: Path | None,
    car_name: str,
    db_path: Path,
    session_setup: dict[str, dict[str, float | str]] | None = None,
) -> ResolvedParameters:
    """Resolve parameter ranges and defaults for a car using 3-tier strategy.

    Tier 1: Open data/ folder -> setup.ini + config files
    Tier 2: Encrypted data.acd -> decrypted setup.ini + config files
    Tier 3: Session setup fallback (if session_setup provided)

    Never raises — always returns a valid ResolvedParameters.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Check cache first (if available)
    try:
        from .cache import get_cached_parameters

        cached = get_cached_parameters(db_path, car_name)
        if cached is not None:
            return cached
    except Exception:
        logger.debug("Cache lookup failed for %s", car_name, exc_info=True)

    # Tier 1: Open data
    if ac_install_path is not None:
        try:
            result = _resolve_tier1(Path(ac_install_path), car_name)
            if result is not None:
                has_defaults = any(r.default_value is not None for r in result.values())
                resolved = ResolvedParameters(
                    car_name=car_name,
                    tier=ResolutionTier.OPEN_DATA,
                    parameters=result,
                    has_defaults=has_defaults,
                    resolved_at=now,
                )
                try:
                    from .cache import save_to_cache

                    save_to_cache(db_path, resolved)
                except Exception:
                    logger.debug("Cache save failed for %s", car_name, exc_info=True)
                return resolved
        except Exception:
            logger.debug("Tier 1 failed for %s", car_name, exc_info=True)

    # Tier 2: ACD archive
    if ac_install_path is not None:
        try:
            result = _resolve_tier2(Path(ac_install_path), car_name)
            if result is not None:
                has_defaults = any(r.default_value is not None for r in result.values())
                resolved = ResolvedParameters(
                    car_name=car_name,
                    tier=ResolutionTier.ACD_ARCHIVE,
                    parameters=result,
                    has_defaults=has_defaults,
                    resolved_at=now,
                )
                try:
                    from .cache import save_to_cache

                    save_to_cache(db_path, resolved)
                except Exception:
                    logger.debug("Cache save failed for %s", car_name, exc_info=True)
                return resolved
        except Exception:
            logger.debug("Tier 2 failed for %s", car_name, exc_info=True)

    # Tier 3: Session fallback (never cached)
    try:
        result = _resolve_tier3(session_setup)
    except Exception:
        logger.debug("Tier 3 failed for %s", car_name, exc_info=True)
        result = {}

    has_defaults = any(r.default_value is not None for r in result.values())
    return ResolvedParameters(
        car_name=car_name,
        tier=ResolutionTier.SESSION_FALLBACK,
        parameters=result,
        has_defaults=has_defaults,
        resolved_at=now,
    )


def list_cars(
    ac_install_path: Path | None, db_path: Path
) -> list[CarStatus]:
    """List all installed cars with their resolution status.

    Raises ValueError if ac_install_path is None or content/cars/ doesn't exist.
    """
    if ac_install_path is None:
        raise ValueError("Assetto Corsa installation path is not configured.")

    cars_dir = Path(ac_install_path) / "content" / "cars"
    if not cars_dir.is_dir():
        raise ValueError(f"Cars directory not found: {cars_dir}")

    from .cache import get_cached_parameters

    car_names = sorted(
        d.name for d in cars_dir.iterdir() if d.is_dir()
    )

    statuses: list[CarStatus] = []
    for name in car_names:
        cached = get_cached_parameters(db_path, name)
        if cached is not None:
            statuses.append(CarStatus(
                car_name=name,
                status="resolved",
                tier=int(cached.tier),
                has_defaults=cached.has_defaults,
                resolved_at=cached.resolved_at,
            ))
        else:
            statuses.append(CarStatus(
                car_name=name,
                status="unresolved",
            ))

    return statuses
