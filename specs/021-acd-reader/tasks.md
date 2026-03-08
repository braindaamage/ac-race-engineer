# Tasks: ACD File Reader

**Input**: Design documents from `specs/021-acd-reader/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package and test directory structure

- [x] T001 Create package structure: `backend/ac_engineer/acd_reader/__init__.py` and `backend/ac_engineer/acd_reader/reader.py` as empty files. Create test directory: `backend/tests/acd_reader/conftest.py` and `backend/tests/acd_reader/test_reader.py` as empty files. Ensure `backend/tests/acd_reader/__init__.py` exists if required by the test runner.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types and test helpers that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Implement `AcdResult` frozen dataclass in `backend/ac_engineer/acd_reader/reader.py`. Fields: `ok: bool`, `files: dict[str, bytes]`, `error: str | None`. Include `@classmethod` factory methods `success(files)` and `failure(error)` per the contract in `contracts/public-api.md`. Use `@dataclass(frozen=True, slots=True)`. Add `from __future__ import annotations` at top of file.

- [x] T003 Create test fixtures in `backend/tests/acd_reader/conftest.py`: implement a helper function `build_acd(entries: dict[str, bytes], car_name: str) -> bytes` that constructs a valid ACD binary archive from the given filename→content mapping. The helper must: (1) derive the encryption key from `car_name` using these exact formulas: `v0 = sum(ord(c) for c in name)`, `v1 = sum(ord(c) * (i + 1) for i, c in enumerate(name))`, `v2 = sum(ord(c) * (i + 1) * (i + 1) for i, c in enumerate(name))`, `v3 = len(name) * sum(ord(c) for c in name)`, `v4 = sum(ord(c) ** 2 for c in name)`, `v5 = sum((i + 1) * ord(c) ** 2 for i, c in enumerate(name))`, `v6 = sum(ord(c) for c in name) ** 2`, `v7 = sum((ord(c) * (i + 1)) ** 2 for i, c in enumerate(name))`. Format as dash-joined string and ASCII-encode, (2) encrypt each entry's content bytes using the inverse formula: `encrypted_byte = (plain_byte + key[i % len(key)]) & 0xFF` — this is the exact inverse of the decryption formula in T005, (3) pack entries sequentially using the ACD archive format (4-byte LE int filename length, filename bytes, 4-byte LE int content size, encrypted content bytes). Return the complete archive as `bytes`. Also provide a `@pytest.fixture` named `sample_car_name` returning `"ks_ferrari_488_gt3"` and a `@pytest.fixture` named `sample_entries` returning a dict with 3 sample files: `{"car.ini": b"[HEADER]\nVERSION=1\n", "tyres.ini": b"[FRONT]\nRADIUS=0.31\n", "data.lut": b"0|0\n100|0.5\n"}`.

**Checkpoint**: AcdResult type and test fixtures ready — user story implementation can begin

---

## Phase 3: User Story 1 — Extract Car Data from Encrypted ACD Archive (Priority: P1)

**Goal**: Given a valid data.acd and car folder name, decrypt and return all contained files as `dict[str, bytes]`

**Independent Test**: Provide a known data.acd (built by test fixture), verify all expected files are extracted with byte-for-byte content fidelity

### Implementation for User Story 1

- [x] T004 [US1] Implement `_derive_key(car_name: str) -> bytes` private function in `backend/ac_engineer/acd_reader/reader.py`. The function must: (1) compute 8 values from the characters of the car name using these exact formulas: `v0 = sum(ord(c) for c in name)`, `v1 = sum(ord(c) * (i + 1) for i, c in enumerate(name))`, `v2 = sum(ord(c) * (i + 1) * (i + 1) for i, c in enumerate(name))`, `v3 = len(name) * sum(ord(c) for c in name)`, `v4 = sum(ord(c) ** 2 for c in name)`, `v5 = sum((i + 1) * ord(c) ** 2 for i, c in enumerate(name))`, `v6 = sum(ord(c) for c in name) ** 2`, `v7 = sum((ord(c) * (i + 1)) ** 2 for i, c in enumerate(name))`, (2) format those 8 integers as a decimal string joined by dashes (e.g., `"179-44-163-59-166-193-14-53"`), (3) return the ASCII-encoded bytes of that formatted string. Reference: research.md R1 for the exact algorithm specification.

- [x] T005 [US1] Implement `_decrypt_bytes(data: bytes, key: bytes) -> bytes` private function in `backend/ac_engineer/acd_reader/reader.py`. Decryption is byte-by-byte: `decrypted_byte = (encrypted_byte - key[i % len(key)]) & 0xFF`. Return the full decrypted bytes.

- [x] T006 [US1] Implement `_parse_archive(data: bytes, key: bytes) -> dict[str, bytes]` private function in `backend/ac_engineer/acd_reader/reader.py`. Parse the sequential binary format: read 4-byte LE signed int for filename length, read filename bytes and decode to str, read 4-byte LE signed int for content size, read content_size encrypted bytes and decrypt them with `_decrypt_bytes`. Accumulate entries into a `dict[str, bytes]`. Loop until all data is consumed. Use `struct.unpack('<i', ...)` for integers. Raise `ValueError` on structural errors (negative sizes, truncated data) — these will be caught by `read_acd`.

- [x] T007 [US1] Implement `_is_readable(content: bytes) -> bool` private function in `backend/ac_engineer/acd_reader/reader.py`. Check the ratio of printable ASCII bytes (codes 0x20-0x7E plus 0x09, 0x0A, 0x0D for tab/newline/CR) in the first `min(512, len(content))` bytes. Return `True` if ratio >= 0.85, `False` otherwise. Return `True` for empty content (zero bytes means no evidence against readability).

- [x] T008 [US1] Implement `read_acd(file_path: Path, car_name: str) -> AcdResult` public function in `backend/ac_engineer/acd_reader/reader.py`. Happy path only in this task: read the file with `Path.read_bytes()`, derive the key with `_derive_key`, parse the archive with `_parse_archive`, check readability of the first entry with `_is_readable`. If files is empty (zero entries), skip the readability check and return `AcdResult.success({})` directly. Return `AcdResult.success(files)` if readable, `AcdResult.failure("Unsupported encryption scheme")` if not readable. Wrap the entire body in a try/except that catches all exceptions and returns `AcdResult.failure(str(e))` — this ensures FR-006 (no unhandled exceptions). Import `Path` from `pathlib`.

- [x] T009 [US1] Wire up public exports in `backend/ac_engineer/acd_reader/__init__.py`. Import `AcdResult` and `read_acd` from `.reader`. Define `__all__ = ["read_acd", "AcdResult"]`. Add module docstring: `"""ACD reader — decrypt and extract Assetto Corsa data.acd archives."""`

- [x] T010 [US1] Write tests for successful extraction in `backend/tests/acd_reader/test_reader.py`. Create a `TestReadAcdSuccess` class with tests: (1) `test_extracts_all_files` — build an ACD archive with `build_acd` fixture, write to `tmp_path / "data.acd"`, call `read_acd`, assert `result.ok is True`, assert all filenames present in `result.files`, assert `result.error is None`. (2) `test_content_fidelity` — verify extracted bytes match original bytes exactly for each file. (3) `test_single_file_archive` — archive with just one file. (4) `test_empty_archive` — archive with zero entries (empty bytes or just EOF), assert `result.ok is True` and `result.files == {}`. (5) `test_read_only_operation` — verify no new files created in `tmp_path` beyond the input. Import from `ac_engineer.acd_reader`.

**Checkpoint**: US1 complete — core extraction works for valid archives. Run `pytest backend/tests/acd_reader/ -v` to validate.

---

## Phase 4: User Story 2 — Graceful Handling of Unsupported or Missing Archives (Priority: P1)

**Goal**: Return structured failure results for all error conditions without raising exceptions

**Independent Test**: Call `read_acd` with nonexistent path, corrupted file, third-party encrypted file, and empty car name — verify each returns `AcdResult(ok=False)` with appropriate error message

### Implementation for User Story 2

- [x] T011 [US2] Add input validation to `read_acd` in `backend/ac_engineer/acd_reader/reader.py`. Before the try block, add early-return checks in this order: (1) if `car_name` is empty or whitespace-only → `AcdResult.failure("Invalid car name: name is empty")`, (2) if `file_path` does not exist → `AcdResult.failure(f"File not found: {file_path}")`, (3) if `file_path` is a directory → `AcdResult.failure(f"Not a file: {file_path}")`, (4) if file size is 0 → `AcdResult.failure(f"File is empty: {file_path}")`. These checks run before any decryption attempt.

- [x] T012 [US2] Enhance `_parse_archive` error handling in `backend/ac_engineer/acd_reader/reader.py`. Raise `ValueError("Corrupted archive: unexpected end of data")` when there are not enough bytes to read a complete entry. Raise `ValueError("Corrupted archive: invalid entry size")` when filename_len or content_size is negative. These ValueError exceptions are caught by `read_acd`'s try/except and converted to `AcdResult.failure(...)`.

- [x] T013 [US2] Write tests for all failure modes in `backend/tests/acd_reader/test_reader.py`. Create a `TestReadAcdFailure` class with tests: (1) `test_file_not_found` — nonexistent path, assert error contains "File not found". (2) `test_path_is_directory` — pass `tmp_path` itself, assert error contains "Not a file". (3) `test_empty_file` — write 0 bytes, assert error contains "File is empty". (4) `test_empty_car_name` — valid file but `car_name=""`, assert error contains "Invalid car name". (5) `test_whitespace_car_name` — `car_name="  "`, assert error contains "Invalid car name". (6) `test_truncated_archive` — write first 10 bytes of a valid archive, assert error contains "Corrupted archive". (7) `test_unsupported_encryption` — write random bytes (e.g., `os.urandom(200)`), assert result.error == "Unsupported encryption scheme". (8) `test_negative_entry_size` — craft bytes with a valid filename length but negative content size using `struct.pack('<i', -1)`, assert error contains "Corrupted archive". All tests must assert `result.ok is False`, `result.files == {}`, and `result.error` is a non-empty string.

**Checkpoint**: US2 complete — all error paths return structured failures. Run `pytest backend/tests/acd_reader/ -v` to validate.

---

## Phase 5: User Story 3 — Handle Diverse Car Folder Names and File Contents (Priority: P2)

**Goal**: Key derivation and archive extraction work correctly with special characters, non-ASCII names, and non-INI file contents

**Independent Test**: Build ACD archives using car names with spaces, parentheses, accents, and Unicode — verify all extract successfully

### Implementation for User Story 3

- [x] T014 [US3] Review and verify `_derive_key` in `backend/ac_engineer/acd_reader/reader.py` handles car names with special characters (spaces, parentheses, underscores, hyphens, dots) and non-ASCII characters (accented letters, Unicode). The key derivation operates on `ord()` of each character — verify it works for characters with code points > 127. If the current implementation uses `.encode('ascii')` anywhere, switch to `.encode('utf-8')` for the key string output. Add defensive handling if the car name contains characters that could cause issues with the arithmetic operations.

- [x] T015 [US3] Write tests for diverse inputs in `backend/tests/acd_reader/test_reader.py`. Create a `TestReadAcdDiverse` class with tests: (1) `test_car_name_with_parentheses` — name `"ks_ferrari_488_gt3_(2018)"`, build and extract archive, assert success. (2) `test_car_name_with_spaces` — name `"my custom car"`, build and extract, assert success. (3) `test_car_name_with_accents` — name `"coche_rápido"`, build and extract, assert success. (4) `test_car_name_with_unicode` — name `"車_mod_01"`, build and extract, assert success. (5) `test_archive_with_lut_file` — include a `.lut` file with binary-like content, verify it appears in results. (6) `test_archive_with_mixed_extensions` — archive containing `.ini`, `.lut`, `.txt`, and extensionless files, verify all are extracted. (7) `test_long_car_name` — name with 100+ characters, build and extract, assert success. Use `build_acd` fixture from conftest for all tests.

**Checkpoint**: US3 complete — module handles the full diversity of AC modding ecosystem. Run `pytest backend/tests/acd_reader/ -v` to validate.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T016 Run full test suite with `conda run -n ac-race-engineer pytest backend/tests/acd_reader/ -v` and verify all tests pass. Verify test count is reasonable (expect ~20 tests). Fix any failures.

- [x] T017 Validate quickstart.md scenarios: verify the import `from ac_engineer.acd_reader import read_acd, AcdResult` works from a Python REPL. Verify the module has zero imports from other `ac_engineer` subpackages (autonomous module requirement FR-011).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — core extraction logic
- **US2 (Phase 4)**: Depends on Phase 3 (T008 `read_acd` must exist before adding validation)
- **US3 (Phase 5)**: Depends on Phase 3 (T004 `_derive_key` must exist before verifying edge cases)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (Phase 3) — adds error handling to existing `read_acd` function
- **User Story 3 (P2)**: Depends on US1 (Phase 3) — verifies/extends existing `_derive_key` function

### Within Each User Story

- Implementation tasks are sequential within each story (each builds on previous)
- Tests for each story come after implementation (test the completed behavior)
- Fixtures (conftest.py) must be ready before any test tasks

### Parallel Opportunities

- T004 and T005 can run in parallel (independent private functions in same file, but no file conflict since they're both in reader.py — execute sequentially to avoid conflicts)
- T006 and T007 depend on T004+T005
- US2 and US3 could theoretically run in parallel after US1, but both modify `reader.py` — execute sequentially to avoid merge conflicts
- Within Phase 2, T002 and T003 work on different files and CAN run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```text
# These two tasks work on different files and can run in parallel:
T002: AcdResult dataclass in backend/ac_engineer/acd_reader/reader.py
T003: Test fixtures in backend/tests/acd_reader/conftest.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (1 task)
2. Complete Phase 2: Foundational (2 tasks)
3. Complete Phase 3: User Story 1 (7 tasks)
4. **STOP and VALIDATE**: Run `pytest backend/tests/acd_reader/ -v` — core extraction works
5. This is a usable module: can extract files from any valid data.acd

### Incremental Delivery

1. Setup + Foundational → Structure ready
2. Add User Story 1 → Core extraction works (MVP)
3. Add User Story 2 → All error cases handled gracefully
4. Add User Story 3 → Edge-case car names work
5. Polish → Full validation pass

### Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | 1 | Directory structure and empty files |
| Phase 2: Foundational | 2 | AcdResult type + test fixtures |
| Phase 3: US1 | 7 | Core extraction + tests |
| Phase 4: US2 | 3 | Error handling + tests |
| Phase 5: US3 | 2 | Diverse inputs + tests |
| Phase 6: Polish | 2 | Final validation |
| **Total** | **17** | |

---

## Notes

- All source goes in two files: `reader.py` (implementation) and `__init__.py` (exports)
- All tests go in two files: `conftest.py` (fixtures) and `test_reader.py` (tests)
- The `build_acd` fixture in conftest.py is critical — it must correctly implement encryption so tests use realistic data
- File contents are `bytes` not `str` — tests must compare bytes
- Commit after each phase checkpoint
