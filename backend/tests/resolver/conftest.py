"""Fixtures for resolver tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from ac_engineer.storage.db import init_db
from tests.acd_reader.conftest import build_acd


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Temporary database with all tables initialized."""
    p = tmp_path / "test.db"
    init_db(p)
    return p


@pytest.fixture
def sample_car_dir(tmp_path: Path) -> Path:
    """Create a temp directory mimicking content/cars/<car_name>/data/ with open data."""
    car_dir = tmp_path / "content" / "cars" / "ks_test_car" / "data"
    car_dir.mkdir(parents=True)

    # setup.ini with MIN/MAX/STEP/SHOW_CLICKS for several sections
    setup_ini = textwrap.dedent("""\
        [CAMBER_LF]
        SHOW_CLICKS=0
        MIN=-4.0
        MAX=0.0
        STEP=0.1

        [CAMBER_RF]
        SHOW_CLICKS=0
        MIN=-4.0
        MAX=0.0
        STEP=0.1

        [PRESSURE_LF]
        SHOW_CLICKS=0
        MIN=18.0
        MAX=35.0
        STEP=0.5

        [WING_1]
        SHOW_CLICKS=1
        MIN=0
        MAX=11
        STEP=1
    """)
    (car_dir / "setup.ini").write_text(setup_ini, encoding="utf-8")

    # suspensions.ini with default values
    suspensions_ini = textwrap.dedent("""\
        [FRONT]
        CAMBER=-3.0
        TOE_OUT=0.0
        SPRING_RATE=120000
        BUMP=5
        FAST_BUMP=3
        REBOUND=7
        FAST_REBOUND=4

        [REAR]
        CAMBER=-2.5
        TOE_OUT=0.2
        SPRING_RATE=100000
        BUMP=4
        FAST_BUMP=2
        REBOUND=6
        FAST_REBOUND=3
    """)
    (car_dir / "suspensions.ini").write_text(suspensions_ini, encoding="utf-8")

    # tyres.ini with pressure defaults
    tyres_ini = textwrap.dedent("""\
        [FRONT]
        PRESSURE_STATIC=26.0

        [REAR]
        PRESSURE_STATIC=24.0
    """)
    (car_dir / "tyres.ini").write_text(tyres_ini, encoding="utf-8")

    return tmp_path


@pytest.fixture
def sample_acd_car_dir(tmp_path: Path) -> Path:
    """Create a temp directory with a data.acd archive containing setup.ini + config files."""
    car_name = "ks_test_car"
    car_dir = tmp_path / "content" / "cars" / car_name
    car_dir.mkdir(parents=True)

    setup_ini = textwrap.dedent("""\
        [CAMBER_LF]
        SHOW_CLICKS=0
        MIN=-4.0
        MAX=0.0
        STEP=0.1

        [PRESSURE_LF]
        SHOW_CLICKS=0
        MIN=18.0
        MAX=35.0
        STEP=0.5

        [WING_1]
        SHOW_CLICKS=1
        MIN=0
        MAX=11
        STEP=1
    """)
    suspensions_ini = textwrap.dedent("""\
        [FRONT]
        CAMBER=-3.0

        [REAR]
        CAMBER=-2.5
    """)
    tyres_ini = textwrap.dedent("""\
        [FRONT]
        PRESSURE_STATIC=26.0

        [REAR]
        PRESSURE_STATIC=24.0
    """)

    entries = {
        "setup.ini": setup_ini.encode("utf-8"),
        "suspensions.ini": suspensions_ini.encode("utf-8"),
        "tyres.ini": tyres_ini.encode("utf-8"),
    }
    acd_data = build_acd(entries, car_name)
    (car_dir / "data.acd").write_bytes(acd_data)

    return tmp_path


@pytest.fixture
def sample_session_setup() -> dict[str, dict[str, float | str]]:
    """Session setup fallback format — section → {parameter: value}."""
    return {
        "CAMBER_LF": {"VALUE": -3.2},
        "CAMBER_RF": {"VALUE": -3.1},
        "PRESSURE_LF": {"VALUE": 26.5},
        "WING_1": {"VALUE": 6},
    }
