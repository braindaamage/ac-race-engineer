# Data Model: ACD File Reader

**Feature**: 021-acd-reader | **Date**: 2026-03-08

## Entities

### AcdResult

The outcome of an ACD extraction attempt. Discriminated by a boolean `ok` field.

| Field    | Type              | Description                                                      |
|----------|-------------------|------------------------------------------------------------------|
| ok       | bool              | `True` if extraction succeeded, `False` otherwise                |
| files    | dict[str, bytes]  | Mapping of filename → raw content bytes. Empty dict on failure   |
| error    | str or None       | Human-readable failure reason. `None` on success                 |

**Invariants**:
- When `ok is True`: `files` contains at least zero entries (empty archive is valid), `error is None`
- When `ok is False`: `files` is empty dict `{}`, `error` is a non-empty string

**Construction**: Via two factory class methods:
- `AcdResult.success(files)` — creates a success result
- `AcdResult.failure(error)` — creates a failure result

### Internal: Key Derivation

Not a persistent entity — computed in-memory during decryption.

| Step     | Output                | Description                                                        |
|----------|-----------------------|--------------------------------------------------------------------|
| Input    | str                   | Car folder name (e.g., `"ks_ferrari_488_gt3"`)                     |
| Step 1   | list[int] (8 values)  | 8 integers derived from arithmetic operations on name characters   |
| Step 2   | str                   | Integers joined with dashes (e.g., `"179-44-163-59-166-193-14-53"`)  |
| Step 3   | bytes                 | ASCII encoding of the dash-joined string — these are the key bytes |

### Internal: Archive Entry (parsed during extraction)

| Field          | Type   | Source                          |
|----------------|--------|---------------------------------|
| filename_len   | int    | 4-byte signed LE int from file  |
| filename       | str    | `filename_len` bytes, decoded   |
| content_size   | int    | 4-byte signed LE int from file  |
| content_raw    | bytes  | `content_size` encrypted bytes  |
| content        | bytes  | Decrypted content bytes         |

Entries are not stored as objects — they are parsed inline and accumulated into the `files` dict.

## State Transitions

This module has no state transitions. It is a pure function: input → output. No persistence, no mutation, no side effects.

## Relationships

```
data.acd (file on disk)
    │
    ▼
read_acd(path, car_name)
    │
    ├── [success] → AcdResult(ok=True, files={"car.ini": b"...", "tyres.ini": b"...", ...}, error=None)
    │
    └── [failure] → AcdResult(ok=False, files={}, error="File not found: ...")
```

No relationships to other entities in the system. Phase 8.2 will consume `AcdResult.files` to feed the setup range resolution pipeline.
