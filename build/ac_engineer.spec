# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for AC Race Engineer backend server.

Build commands:
  # One-directory (recommended — faster startup)
  pyinstaller build/ac_engineer.spec

  # One-file alternative
  pyinstaller build/ac_engineer.spec --onefile
"""

import os
from pathlib import Path

block_cipher = None

# Paths relative to repo root (spec file is in build/)
REPO_ROOT = Path(SPECPATH).parent
BACKEND = REPO_ROOT / "backend"

a = Analysis(
    [str(BACKEND / "api" / "server.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=[
        # Knowledge base markdown documents
        (str(BACKEND / "ac_engineer" / "knowledge" / "docs"), "ac_engineer/knowledge/docs"),
        # Engineer skill prompts
        (str(BACKEND / "ac_engineer" / "engineer" / "skills"), "ac_engineer/engineer/skills"),
    ],
    hiddenimports=[
        # Pydantic AI and LLM provider SDKs (dynamically imported based on config)
        "pydantic_ai",
        "anthropic",
        "openai",
        "google.generativeai",
        # File watcher
        "watchdog",
        "watchdog.observers",
        "watchdog.events",
        # Uvicorn internals
        "uvicorn.logging",
        "uvicorn.protocols.http.auto",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ac_engineer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ac_engineer",
)
