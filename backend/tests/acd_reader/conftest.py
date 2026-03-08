from __future__ import annotations

import struct

import pytest


def build_acd(entries: dict[str, bytes], car_name: str) -> bytes:
    """Build a valid ACD binary archive from filename->content mapping.

    Derives the encryption key from car_name and encrypts each entry,
    then packs them in sequential ACD format.
    """
    key = _derive_key_for_test(car_name)
    parts: list[bytes] = []
    for filename, content in entries.items():
        fname_bytes = filename.encode("utf-8")
        encrypted = _encrypt_bytes(content, key)
        parts.append(struct.pack("<i", len(fname_bytes)))
        parts.append(fname_bytes)
        parts.append(struct.pack("<i", len(encrypted)))
        parts.append(encrypted)
    return b"".join(parts)


def _derive_key_for_test(name: str) -> bytes:
    """Derive ACD encryption key from car name (test helper)."""
    v0 = sum(ord(c) for c in name)
    v1 = sum(ord(c) * (i + 1) for i, c in enumerate(name))
    v2 = sum(ord(c) * (i + 1) * (i + 1) for i, c in enumerate(name))
    v3 = len(name) * sum(ord(c) for c in name)
    v4 = sum(ord(c) ** 2 for c in name)
    v5 = sum((i + 1) * ord(c) ** 2 for i, c in enumerate(name))
    v6 = sum(ord(c) for c in name) ** 2
    v7 = sum((ord(c) * (i + 1)) ** 2 for i, c in enumerate(name))
    key_str = f"{v0}-{v1}-{v2}-{v3}-{v4}-{v5}-{v6}-{v7}"
    return key_str.encode("ascii")


def _encrypt_bytes(data: bytes, key: bytes) -> bytes:
    """Encrypt bytes using the inverse of the ACD decryption formula."""
    return bytes((b + key[i % len(key)]) & 0xFF for i, b in enumerate(data))


@pytest.fixture
def sample_car_name() -> str:
    return "ks_ferrari_488_gt3"


@pytest.fixture
def sample_entries() -> dict[str, bytes]:
    return {
        "car.ini": b"[HEADER]\nVERSION=1\n",
        "tyres.ini": b"[FRONT]\nRADIUS=0.31\n",
        "data.lut": b"0|0\n100|0.5\n",
    }
