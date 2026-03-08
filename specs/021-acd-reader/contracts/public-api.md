# Public API Contract: ACD File Reader

**Feature**: 021-acd-reader | **Date**: 2026-03-08

## Module Import

```python
from ac_engineer.acd_reader import read_acd, AcdResult
```

## Function: `read_acd`

```python
def read_acd(file_path: Path, car_name: str) -> AcdResult:
    """Read and decrypt an Assetto Corsa data.acd archive.

    Derives the decryption key from the car folder name, decrypts the
    archive contents using AC's official XOR scheme, and returns all
    contained files as a mapping of filename to raw bytes.

    Args:
        file_path: Path to the data.acd file.
        car_name:  Car folder name used for key derivation
                   (e.g., "ks_ferrari_488_gt3").

    Returns:
        AcdResult with ok=True and files dict on success,
        or ok=False and error message on failure.

    Never raises exceptions regardless of input quality.
    """
```

### Parameters

| Parameter   | Type   | Required | Description                              |
|-------------|--------|----------|------------------------------------------|
| file_path   | Path   | Yes      | Absolute or relative path to data.acd    |
| car_name    | str    | Yes      | Car folder name for key derivation       |

### Return Value

`AcdResult` — always returned, never raises.

### Failure Reasons

| Condition                          | `error` message pattern                  |
|------------------------------------|------------------------------------------|
| `car_name` is empty                | `"Invalid car name: name is empty"`      |
| `file_path` does not exist         | `"File not found: {path}"`               |
| `file_path` is a directory         | `"Not a file: {path}"`                   |
| File is zero bytes                 | `"File is empty: {path}"`                |
| Archive truncated mid-entry        | `"Corrupted archive: unexpected end of data"` |
| Negative/invalid entry sizes       | `"Corrupted archive: invalid entry size"` |
| Decryption produces unreadable output | `"Unsupported encryption scheme"`     |

## Dataclass: `AcdResult`

```python
@dataclass(frozen=True, slots=True)
class AcdResult:
    """Result of an ACD archive extraction attempt."""

    ok: bool
    files: dict[str, bytes]
    error: str | None

    @classmethod
    def success(cls, files: dict[str, bytes]) -> AcdResult: ...

    @classmethod
    def failure(cls, error: str) -> AcdResult: ...
```

### Usage Examples

```python
from pathlib import Path
from ac_engineer.acd_reader import read_acd

# Successful extraction
result = read_acd(Path("C:/Games/AC/content/cars/ks_ferrari_488_gt3/data.acd"), "ks_ferrari_488_gt3")
if result.ok:
    for filename, content in result.files.items():
        text = content.decode("utf-8", errors="replace")
        print(f"{filename}: {len(content)} bytes")

# Missing file
result = read_acd(Path("/nonexistent/data.acd"), "some_car")
assert not result.ok
assert "File not found" in result.error

# Unsupported encryption
result = read_acd(Path("third_party_encrypted.acd"), "some_car")
assert not result.ok
assert result.error == "Unsupported encryption scheme"
```
