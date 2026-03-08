# Feature Specification: ACD File Reader

**Feature Branch**: `021-acd-reader`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Read and decrypt Assetto Corsa data.acd files to extract car parameter data (setup ranges, defaults, physics configurations) for the AI race engineer."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Car Data from Encrypted ACD Archive (Priority: P1)

The AI race engineer needs to read the full set of car physics and setup data from a car's data.acd file. This is the standard packaging format used by Assetto Corsa for official cars and most mods. The module receives the path to data.acd and the car's folder name, decrypts the archive, and returns all contained files identified by filename with their text contents.

**Why this priority**: Without this capability, the engineer cannot access parameter ranges or factory defaults for any car that packages its data in an ACD archive — which is the majority of cars. This is the core purpose of the module.

**Independent Test**: Can be fully tested by providing a known data.acd file and verifying that all expected INI files are extracted with correct, readable contents.

**Acceptance Scenarios**:

1. **Given** a valid data.acd file for a supported car and the correct car folder name, **When** the module reads the file, **Then** it returns a mapping of all contained filenames to their text contents, and each file's content is human-readable INI/text data.
2. **Given** a valid data.acd containing multiple files (e.g., car.ini, suspensions.ini, tyres.ini, aero.ini, drivetrain.ini, engine.ini), **When** the module extracts them, **Then** every file present in the archive appears in the result with its complete contents preserved exactly.
3. **Given** a data.acd and the car folder name, **When** the module is called, **Then** no files on disk are modified, created, or deleted — the operation is strictly read-only.

---

### User Story 2 - Graceful Handling of Unsupported or Missing Archives (Priority: P1)

Not all cars use data.acd — some ship with an open data/ folder of plain files. Others may use third-party encryption schemes that differ from the official Assetto Corsa format. The module must handle all of these cases without raising exceptions, returning a structured result that tells the caller exactly what happened.

**Why this priority**: The module will be called for every car the engineer analyzes. If it crashes on missing or incompatible files, it blocks the entire pipeline. Graceful failure is as critical as successful extraction.

**Independent Test**: Can be fully tested by calling the module with a nonexistent path, a file encrypted with a different scheme, and a truncated file, then verifying each returns a clear failure result without exceptions.

**Acceptance Scenarios**:

1. **Given** a path where no data.acd file exists, **When** the module attempts to read it, **Then** it returns a result indicating the file was not found, without raising an exception.
2. **Given** a data.acd encrypted with a third-party scheme (not the standard AC encryption), **When** the module attempts to decrypt it, **Then** it detects that the decrypted output is not readable text and returns a result indicating decryption was not possible with the supported scheme.
3. **Given** a data.acd file that is corrupted or truncated mid-archive, **When** the module reads it, **Then** it returns a result indicating the file could not be fully processed, without raising an exception.
4. **Given** a valid but empty data.acd archive (contains no files), **When** the module reads it, **Then** it returns a success result with an empty file mapping.

---

### User Story 3 - Handle Diverse Car Folder Names and File Contents (Priority: P2)

Mod cars can have folder names with special characters, non-ASCII sequences, or unusual formatting. The archive may also contain files beyond standard INI files (e.g., LUT files, custom data files). The module must handle all of these without failure.

**Why this priority**: While most cars follow conventions, the module must be robust enough to handle the full diversity of the AC modding ecosystem. Failures on edge-case names would silently exclude certain cars.

**Independent Test**: Can be tested by providing car folder names with special characters (spaces, accents, symbols) and archives containing non-INI files, verifying all are processed without errors.

**Acceptance Scenarios**:

1. **Given** a car folder name containing special characters (e.g., spaces, parentheses, accents like "ks_ferrari_488_gt3_(2018)"), **When** the module uses it for decryption, **Then** the decryption proceeds correctly using the name as-is.
2. **Given** an archive containing non-INI files (e.g., .lut files, .txt files, unnamed data files), **When** the module extracts the archive, **Then** all files are included in the result regardless of their extension or format.
3. **Given** a car folder name with non-ASCII characters (e.g., Unicode characters from mod authors), **When** the module uses it, **Then** it handles the encoding correctly without errors.

---

### Edge Cases

- What happens when data.acd is a zero-byte file? The module returns a failure result indicating the file is empty or corrupted.
- What happens when a single file inside the archive is corrupted but others are valid? The module extracts what it can and indicates partial failure.
- What happens when the data.acd path is a directory instead of a file? The module returns a failure result indicating the path is not a file.
- What happens when the caller provides an empty string as the car folder name? The module returns a failure result indicating an invalid car name.
- What happens when file contents inside the archive contain binary data (non-text)? The module includes the raw bytes in the result — it does not filter or interpret contents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a file path and a car folder name as its only inputs for reading an ACD archive.
- **FR-002**: System MUST decrypt data.acd files using Assetto Corsa's official encryption scheme, which derives the decryption key from the car folder name.
- **FR-003**: System MUST parse the decrypted archive to extract individual files, returning a mapping of filename to file contents.
- **FR-004**: System MUST detect when decryption produces non-readable output (indicating an unsupported encryption scheme) and report this as a distinct failure reason.
- **FR-005**: System MUST return a structured result for every call — either successful extraction with file contents, or a failure with a clear reason.
- **FR-006**: System MUST NOT raise unhandled exceptions for any input, including missing files, corrupted data, empty archives, invalid paths, or empty car names.
- **FR-007**: System MUST NOT modify, create, or delete any files on disk — the operation is strictly read-only.
- **FR-008**: System MUST NOT require any external configuration, network access, or database — the car folder name and file path are sufficient.
- **FR-009**: System MUST handle car folder names containing special characters, spaces, and non-ASCII sequences without error.
- **FR-010**: System MUST extract all files from the archive regardless of their extension or format (not limited to .ini files).
- **FR-011**: System MUST have no dependencies on other modules in the AC Race Engineer system — it is fully autonomous.

### Key Entities

- **ACD Archive**: A binary file (data.acd) containing multiple packed files, optionally encrypted using a key derived from the car folder name. Key attributes: file path, encryption status, contained file entries.
- **ACD Entry**: A single file packed within the archive. Key attributes: filename (string), content (bytes/text), size.
- **Extraction Result**: The outcome of an extraction attempt. Either a success containing a mapping of filenames to their text contents, or a failure containing a reason (file not found, decryption unsupported, corrupted data, empty archive, invalid input).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The module successfully extracts all files from any data.acd encrypted with Assetto Corsa's official scheme, with 100% content fidelity (byte-for-byte match with the original packed files).
- **SC-002**: The module correctly identifies and reports unsupported encryption within a single read pass — no retries, no hangs, no crashes.
- **SC-003**: The module handles all specified edge cases (missing file, corrupted archive, empty archive, special characters in name, invalid inputs) by returning structured failure results — zero unhandled exceptions across all cases.
- **SC-004**: The module operates with no external dependencies beyond the standard library and the two provided inputs (file path, car folder name).
- **SC-005**: The module processes a typical car's data.acd (containing 10-30 files) in under 1 second on standard hardware.

## Assumptions

- The Assetto Corsa official encryption scheme is a well-documented algorithm that derives a key from the car folder name using a specific byte-manipulation process. The implementation will follow this known algorithm.
- The ACD archive format uses a simple sequential layout: a series of entries each consisting of a filename (length-prefixed), content size, and content bytes (XOR-encrypted).
- "Readable text" detection for distinguishing successful decryption from unsupported schemes can be accomplished by checking whether the decrypted output contains valid text characters (e.g., printable ASCII ratio above a threshold).
- Files extracted from the archive are returned as strings (decoded text), since the primary consumers are INI parsers. Binary files (like .lut lookup tables) will still be included but may contain encoding artifacts — this is acceptable for Phase 8.1 since interpretation is deferred to Phase 8.2.
- The module targets Python 3.11+ and uses only the standard library (no third-party packages required).

## Scope Boundaries

**In scope**:
- Reading and decrypting data.acd files using AC's official encryption
- Parsing the archive format to extract individual files
- Returning structured results (success with contents, or failure with reason)
- Handling all error cases gracefully

**Out of scope**:
- Interpreting the contents of extracted files (deferred to Phase 8.2)
- Caching extraction results
- Writing, modifying, or re-encrypting ACD files
- Supporting encryption schemes other than AC's official one (detected and reported, not supported)
- Integration with the setup range resolution pipeline (Phase 8.2)
