from __future__ import annotations

import struct

import pytest

from ac_engineer.acd_reader.reader import _derive_key


def build_acd(
    entries: dict[str, bytes],
    car_name: str,
    *,
    sentinel: bool = False,
) -> bytes:
    """Build a valid ACD binary archive from filename->content mapping.

    Derives the encryption key from car_name and encrypts each entry,
    then packs them in the AC format (4 bytes per content byte, int32-LE).

    Args:
        sentinel: If True, prepend the -1111 header (8 bytes).
    """
    key = _derive_key(car_name)
    parts: list[bytes] = []

    if sentinel:
        parts.append(struct.pack("<i", -1111))
        parts.append(struct.pack("<i", 0))

    for filename, content in entries.items():
        fname_bytes = filename.encode("utf-8")
        encrypted = _encrypt_bytes(content, key)
        parts.append(struct.pack("<i", len(fname_bytes)))
        parts.append(fname_bytes)
        parts.append(struct.pack("<i", len(encrypted)))
        # Each encrypted byte stored as int32-LE
        for b in encrypted:
            parts.append(struct.pack("<i", b))

    return b"".join(parts)


def _encrypt_bytes(data: bytes, key: bytes) -> bytes:
    """Encrypt bytes using the inverse of the ACD decryption formula.

    Mirrors the null-byte-skipping decryption: key_pos advances only for
    non-zero encrypted bytes.  For typical test data no encrypted byte
    will be zero, so key_pos advances on every byte.
    """
    result = bytearray()
    key_pos = 0
    for b in data:
        encrypted = (b + key[key_pos % len(key)]) & 0xFF
        result.append(encrypted)
        key_pos += 1
    return bytes(result)


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
