# Architecture

The CLI validates bounded integer limits, reads one file through the input
boundary, optionally fingerprints the bytes, strictly loads JSON, scans
string values, selects an explicitly requested or conservatively detected
format adapter when requested, and serializes a report. No input key or value is retained
in a diagnostic. Reports sort by safe location, rule identifier, severity and status.

The byte cap is checked before reads and enforced during reads. Native
Windows handles open reparse points themselves; their attributes must be
verified before use. Ancestor handles remain open through the read.
The POSIX implementation uses no-follow opens relative to directory
descriptors. Operating-system failures are mapped to fixed diagnostics.

UTF-8 decoding accepts a leading BOM. A lexical, iterative depth guard
ignores braces inside quoted strings before the standard JSON decoder is
invoked. The decoder detects duplicate keys and rejects non-finite numbers,
including exponent overflow. Decoder recursion failures map to JSON_TOO_DEEP.

The privacy walker is iterative and inspects string values only.
Safe parameter names and values are allowlisted. The schema describes the generic core and the implemented save-format and API
diagnostics. It is not a workflow schema. Its contract tests exercise the vocabulary used in the
schema with a small standard-library checker; no general schema validator
dependency is provided.

Tests and fixtures are newly authored synthetic data. The Windows handle
path is exercised locally; POSIX behavior requires execution on a POSIX
host for platform validation. Attribute injection tests cover symlink and
reparse classification without requiring permission to create links.

The format_detection module returns a fixed enum without examining node types.
The two save adapters share top-level checks, node validation and connection
validation. Node indexes retain lists of occurrences. Link IDs use numeric
equality with an explicit boolean exclusion. Neither adapter overwrites the
input. Count limits precede indexing, and diagnostics contain no raw IDs.

Not implemented: registrations, model or plugin presence, media
inspection, execution checks, environment scanning, network access or repairs.
TARGETED_STATIC_SUBSET / NOT_A_FULL_JSON_SCHEMA_IMPLEMENTATION.

API detection returns independent structural evidence. The API adapter uses
the existing root mapping for exact source lookups; it never normalizes IDs.
It visits direct inputs once and counts references incrementally without an
inputs copy. Node limits precede traversal; reference excess stops traversal.
API structural locations use /api_nodes plus ordinals, fixed field names,
and ordinal input keys. The unchanged generic privacy walker still uses
ordinal object locations throughout all formats, preserving core semantics.
The adapter does not validate metadata titles or arbitrary extra fields.
Schema changes describe reports, not an official workflow schema.
