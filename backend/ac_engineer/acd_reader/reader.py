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


def _trunc_div(a: int, b: int) -> int:
    """Integer division truncating toward zero (C/Go semantics)."""
    return int(a / b)


def _derive_key(car_name: str) -> bytes:
    """Derive ACD encryption key from car folder name.

    Ported from the Go reference implementation in
    github.com/JustaPenguin/assetto-server-manager/pkg/acd.
    """
    chars = [ord(c) for c in car_name]
    n = len(chars)

    # part1: sum of all char codes
    part1 = 0
    for i in range(n):
        part1 += chars[i]

    # part2: alternating multiply / subtract, step 2
    # Go: for i := 0; i < n-1; i++ { part2 *= f[i]; i++; part2 -= f[i] }
    part2 = 0
    i = 0
    while i < n - 1:
        part2 *= chars[i]
        i += 1
        part2 -= chars[i]
        i += 1  # for-loop increment

    # part3: multiply, trunc-divide, add with magic constant 0x1b
    # Go: for i := 1; i < n-3; i += 4 {
    #   part3 *= f[i]; i++; part3 /= (f[i]+0x1b); i-=2; part3 += -0x1b - f[i]
    # }
    # Net per iteration: body does i+1-2 = i-1, then for does i+4, total +3
    part3 = 0
    i = 1
    while i < n - 3:
        part3 *= chars[i]
        i += 1
        part3 = _trunc_div(part3, chars[i] + 0x1b)
        i -= 2
        part3 += -0x1b - chars[i]
        i += 4  # for-loop increment

    # part4: start at 0x1683, subtract chars[1:]
    part4 = 0x1683
    for i in range(1, n):
        part4 -= chars[i]

    # part5: complex multiply chain
    # Go: for i := 1; i < n-4; i += 4 {
    #   nn := (f[i]+0xf)*part5; i--; x := f[i]; i++; x+=0xf; x*=nn; x+=0x16; part5=x
    # }
    # Body does i-1+1=i (net 0), then for does i+4
    part5 = 0x42
    i = 1
    while i < n - 4:
        nn = (chars[i] + 0xf) * part5
        i -= 1
        x = chars[i]
        i += 1
        x += 0xf
        x *= nn
        x += 0x16
        part5 = x
        i += 4  # for-loop increment

    # part6: start at 0x65, subtract every other char from index 0
    part6 = 0x65
    i = 0
    while i < n - 2:
        part6 -= chars[i]
        i += 2

    # part7: start at 0xab, modulo every other char from index 0
    part7 = 0xab
    i = 0
    while i < n - 2:
        part7 %= chars[i]
        i += 2

    # part8: divide by f[i], add f[i+1], step 1
    # Go: for i := 0; i < n-1; i++ {
    #   tmp := f[i]; part8 /= tmp; i++; tmp2 := f[i]; part8 += tmp2; i--
    # }
    # Body does i+1-1=i (net 0), then for does i+1
    part8 = 0xab
    i = 0
    while i < n - 1:
        tmp = chars[i]
        if tmp != 0:
            part8 = _trunc_div(part8, tmp)
        i += 1
        part8 += chars[i]
        i -= 1
        i += 1  # for-loop increment

    parts = [part1, part2, part3, part4, part5, part6, part7, part8]
    key_str = "-".join(str(v & 0xFF) for v in parts)
    return key_str.encode("ascii")


def _decrypt_bytes(data: bytes, key: bytes) -> bytes:
    """Decrypt bytes using AC's subtraction scheme.

    Null bytes are passed through without advancing the key position.
    """
    out = bytearray(len(data))
    key_pos = 0
    for i, b in enumerate(data):
        if b == 0:
            continue
        out[i] = (b - key[key_pos % len(key)]) & 0xFF
        key_pos += 1
    return bytes(out)


_SENTINEL = -1111


def _parse_entries(data: bytes, offset: int, key: bytes) -> dict[str, bytes]:
    """Parse ACD entries — each content byte is stored as int32-LE on disk."""
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

        # Read content size (number of logical bytes)
        if offset + 4 > len(data):
            raise ValueError("Corrupted archive: unexpected end of data")
        (content_size,) = struct.unpack("<i", data[offset : offset + 4])
        offset += 4
        if content_size < 0:
            raise ValueError("Corrupted archive: invalid entry size")

        # Each byte stored as int32-LE on disk (4 bytes per logical byte)
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
    """Parse an ACD binary archive, handling optional -1111 sentinel."""
    offset = 0
    if len(data) >= 4:
        (sentinel,) = struct.unpack("<i", data[0:4])
        if sentinel == _SENTINEL:
            offset = 8  # skip 4-byte sentinel + 4-byte throwaway
    return _parse_entries(data, offset, key)


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
