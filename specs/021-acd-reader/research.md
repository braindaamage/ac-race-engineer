# Research: ACD File Reader

**Feature**: 021-acd-reader | **Date**: 2026-03-08

## R1: ACD Encryption Algorithm

**Decision**: Implement AC's official key derivation + XOR decryption as specified by the user.

**Rationale**: The algorithm is well-documented in the AC modding community. The user provided the exact specification:

1. **Key derivation**: 8 independent arithmetic operations on the car folder name characters produce 8 integer values.
2. **Key formatting**: The 8 integers are joined with dashes as a decimal string (e.g., `"179-44-163-59-166-193-14-53"`).
3. **Key bytes**: The ASCII code points of each character in that formatted string.
4. **Decryption**: Byte-by-byte subtraction-XOR: `decrypted_byte = (encrypted_byte - key[i % len(key)]) & 0xFF`.

**Alternatives considered**:
- Using a third-party ACD library: None exist as maintained packages. Community implementations are scattered scripts, not packaged modules.
- Wrapping AC's own decryption code: Would require reverse engineering and platform coupling. Direct reimplementation is simpler and portable.

## R2: ACD Archive Format

**Decision**: Parse the sequential binary format as specified by the user.

**Rationale**: The format is straightforward:
- Each entry: `4-byte int (filename length)` → `filename bytes` → `4-byte int (content size)` → `encrypted content bytes`
- Entries are sequential until EOF
- All integers are little-endian (standard for Windows-native formats)

**Alternatives considered**:
- Using `struct.unpack` vs manual byte slicing: `struct.unpack` is cleaner and handles endianness explicitly. Chosen.
- Streaming vs full file read: Full file read (`Path.read_bytes()`) is simpler and sufficient — typical data.acd files are 50-500 KB. No need for streaming.

## R3: Content Type — bytes vs str

**Decision**: Return `bytes` as the canonical type for extracted file contents.

**Rationale**: The user explicitly specified this to resolve the spec's inconsistency. Callers (Phase 8.2) are responsible for decoding to str. This is correct because:
- Some entries may be binary (e.g., .lut lookup tables)
- Encoding assumptions (UTF-8 vs Latin-1 vs Windows-1252) belong to the consumer, not the extractor
- Returning bytes is lossless; returning str requires an encoding choice that may be wrong

**Alternatives considered**:
- Return str with UTF-8 decoding + errors="replace": Lossy for binary files, assumes encoding.
- Return str with encoding detection (chardet): Adds external dependency, unreliable for short files.

## R4: Readability Detection

**Decision**: Check printable ASCII ratio in first 512 bytes of first extracted entry. Threshold: >= 0.85.

**Rationale**: The user specified this exact approach. It works because:
- Successfully decrypted INI files are overwhelmingly printable ASCII (typically 98%+)
- Third-party encrypted content appears as random bytes (~30-40% printable)
- 512 bytes is sufficient to distinguish — INI files have headers/sections within the first few hundred bytes
- The 0.85 threshold provides margin for files with some non-ASCII content (e.g., comments with accented characters)

**Alternatives considered**:
- Check all entries: Slower, unnecessary — if the first entry decrypts correctly, the key is valid for all.
- Check for specific INI patterns (e.g., `[SECTION]`): Too rigid — archive may contain non-INI files as the first entry.
- Lower threshold (0.5): Too permissive — random data can occasionally reach 50% printable.

## R5: Error Handling Strategy

**Decision**: Return a result type with success/failure discrimination. Never raise exceptions.

**Rationale**: The spec requires zero unhandled exceptions. A result type (similar to Rust's `Result` pattern) is the cleanest approach:
- Success: contains `dict[str, bytes]` mapping of filename → content
- Failure: contains a reason string describing what went wrong
- Callers check `.ok` (bool) to determine success/failure

**Alternatives considered**:
- Raise custom exceptions: Contradicts spec requirement FR-006 (no unhandled exceptions). Would force callers to wrap every call in try/except.
- Return `None` on failure: Loses the reason for failure. Callers can't distinguish "file not found" from "unsupported encryption".
- Return `tuple[dict | None, str | None]`: Awkward API, no type safety.

## R6: Module Architecture

**Decision**: Single package with two files: `__init__.py` (exports) and `reader.py` (all implementation).

**Rationale**: The user specified "single module, no submodules needed." The implementation is ~200-300 LOC — splitting into multiple files would be over-engineering. All private helpers (_derive_key, _decrypt_bytes, _parse_archive, _is_readable) live in reader.py.

**Alternatives considered**:
- Single `__init__.py` with everything: Works but mixing exports with implementation is less clean.
- Multiple modules (crypto.py, parser.py, models.py): Over-engineered for the scope. A 200-LOC module doesn't need 4 files.

## R7: Integer Endianness

**Decision**: Use little-endian for 4-byte integers in the archive format.

**Rationale**: Assetto Corsa is a Windows-native application. Windows uses little-endian byte order. The ACD format follows this convention. Use `struct.unpack('<i', ...)` for signed 32-bit integers.

**Alternatives considered**:
- Big-endian: Incorrect for this format.
- Unsigned integers (`'<I'`): The format uses signed 32-bit integers. Filename lengths and content sizes are always positive but stored as signed ints in the original AC code.
