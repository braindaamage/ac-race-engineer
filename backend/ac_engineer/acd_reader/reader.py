from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AcdResult:
    """Result of an ACD archive extraction attempt."""

    ok: bool
    files: dict[str, bytes]
    error: str | None

    @classmethod
    def success(cls, files: dict[str, bytes]) -> AcdResult:
        return cls(ok=True, files=files, error=None)

    @classmethod
    def failure(cls, error: str) -> AcdResult:
        return cls(ok=False, files={}, error=error)


def _derive_key(car_name: str) -> bytes:
    """Derive ACD encryption key from car folder name."""
    name = car_name
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


def _decrypt_bytes(data: bytes, key: bytes) -> bytes:
    """Decrypt bytes using AC's subtraction scheme."""
    return bytes((b - key[i % len(key)]) & 0xFF for i, b in enumerate(data))


_V2_SENTINEL = -1111


def _parse_entries_v1(data: bytes, offset: int, key: bytes) -> dict[str, bytes]:
    """Parse standard ACD entries: 1 byte per content byte on disk."""
    files: dict[str, bytes] = {}
    while offset < len(data):
        # Read filename length
        if offset + 4 > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        (fname_len,) = struct.unpack("<i", data[offset : offset + 4])
        offset += 4
        if fname_len < 0:
            raise ValueError("Corrupted archive: invalid entry size")

        # Read filename
        if offset + fname_len > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        filename = data[offset : offset + fname_len].decode("utf-8")
        offset += fname_len

        # Read content size
        if offset + 4 > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        (content_size,) = struct.unpack("<i", data[offset : offset + 4])
        offset += 4
        if content_size < 0:
            raise ValueError("Corrupted archive: invalid entry size")

        # Read and decrypt content
        if offset + content_size > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        encrypted = data[offset : offset + content_size]
        offset += content_size
        files[filename] = _decrypt_bytes(encrypted, key)

    return files


def _parse_entries_v2(data: bytes, offset: int, key: bytes) -> dict[str, bytes]:
    """Parse -1111 format entries: each content byte stored as 4-byte int32-LE."""
    files: dict[str, bytes] = {}
    while offset < len(data):
        # Read filename length
        if offset + 4 > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        (fname_len,) = struct.unpack("<i", data[offset : offset + 4])
        offset += 4
        if fname_len < 0:
            raise ValueError("Corrupted archive: invalid entry size")

        # Read filename (single-byte chars, same as v1)
        if offset + fname_len > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        filename = data[offset : offset + fname_len].decode("utf-8")
        offset += fname_len

        # Read content size (number of logical bytes)
        if offset + 4 > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        (content_size,) = struct.unpack("<i", data[offset : offset + 4])
        offset += 4
        if content_size < 0:
            raise ValueError("Corrupted archive: invalid entry size")

        # Each byte stored as int32-LE → 4 bytes per logical byte on disk
        disk_size = content_size * 4
        if offset + disk_size > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")

        # Extract encrypted bytes from int32 values
        encrypted = bytes(
            struct.unpack("<i", data[offset + i * 4 : offset + i * 4 + 4])[0] & 0xFF
            for i in range(content_size)
        )
        offset += disk_size
        files[filename] = _decrypt_bytes(encrypted, key)

    return files


def _parse_archive(data: bytes, key: bytes) -> dict[str, bytes]:
    """Parse an ACD binary archive, auto-detecting v1 vs v2 (-1111) format."""
    if len(data) >= 4:
        (sentinel,) = struct.unpack("<i", data[0:4])
        if sentinel == _V2_SENTINEL:
            # Skip 8-byte header (4-byte sentinel + 4-byte unknown field)
            return _parse_entries_v2(data, 8, key)
    return _parse_entries_v1(data, 0, key)


def _is_readable(content: bytes) -> bool:
    """Check if content is likely readable text (printable ASCII ratio)."""
    if len(content) == 0:
        return True
    sample = content[: min(512, len(content))]
    printable = sum(
        1 for b in sample if (0x20 <= b <= 0x7E) or b in (0x09, 0x0A, 0x0D)
    )
    return printable / len(sample) >= 0.85


def read_acd(file_path: Path, car_name: str) -> AcdResult:
    """Read and decrypt an Assetto Corsa data.acd archive.

    Args:
        file_path: Path to the data.acd file.
        car_name:  Car folder name used for key derivation.

    Returns:
        AcdResult with ok=True and files dict on success,
        or ok=False and error message on failure.

    Never raises exceptions regardless of input quality.
    """
    # Input validation (T011 will extend these)
    if not car_name or car_name.isspace():
        return AcdResult.failure("Invalid car name: name is empty")
    if not file_path.exists():
        return AcdResult.failure(f"File not found: {file_path}")
    if file_path.is_dir():
        return AcdResult.failure(f"Not a file: {file_path}")
    if file_path.stat().st_size == 0:
        return AcdResult.failure(f"File is empty: {file_path}")

    try:
        data = file_path.read_bytes()
        key = _derive_key(car_name)
        files = _parse_archive(data, key)

        if not files:
            return AcdResult.success({})

        # Check readability of first entry
        first_content = next(iter(files.values()))
        if not _is_readable(first_content):
            return AcdResult.failure("Unsupported encryption scheme")

        return AcdResult.success(files)
    except Exception as e:
        return AcdResult.failure(str(e))
