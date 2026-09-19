# comfyui-workflow-auditor

Pre-release offline static auditor for generic JSON, Workflow JSON v1.0,
Workflow JSON v0.4, and Workflow API Format. Unofficial; not affiliated with
or endorsed by ComfyUI. Static auditing does not prove executability.

Only Python 3.11 or newer and its standard library are required.
There is no telemetry, no automatic network access, and no automatic repair.
The auditor does not inspect installed nodes and does not inspect models or weights.

Configure the process module search path for the `src` layout, then run:

```text
python -S -m workflow_auditor audit tests/fixtures/valid_generic.json --format generic-json
python -S -m workflow_auditor audit tests/fixtures/workflow_v1_valid.json --format workflow-v1
python -S -m workflow_auditor audit tests/fixtures/workflow_v04_valid.json --format auto --output-format json
python -S -m unittest discover -s tests
```

`--format` accepts `generic-json` (the default), `auto`, `workflow-v1`, and
`workflow-v0.4`, and `api`. Auto mode must be explicitly selected. Explicit formats validate content without auto selection.
Auto stops on unknown or conflicting format features. It does not inspect
node type names or widget values to choose a format.

Workflow JSON v1.0 and Workflow JSON v0.4 use a targeted static subset:
TARGETED_STATIC_SUBSET / NOT_A_FULL_JSON_SCHEMA_IMPLEMENTATION.
Checks cover required fields, basic types, duplicate IDs, link endpoints,
slots and backreferences that can be verified from the supplied file.
Unknown fields are allowed. Unverifiable relationships are NOT_CHECKED.
This is not a full JSON Schema implementation.

API checks cover a node mapping, ASCII digit string IDs, class_type, inputs,
optional metadata shape, and conservative direct input reference recognition.
A confirmed reference has exactly two items: an existing exact string ID and
a non-boolean nonnegative integer index. Ordinary lists and nested values
are not recursively interpreted as connections. Missing numeric sources are
WARNING / NOT_CHECKED; invalid indices for existing sources are ERROR.
No real output counts are inferred. API checks are a targeted static subset.

```text
python -S -m workflow_auditor audit tests/fixtures/api_valid.json --format api --output-format json
```

Options also include `--output-format text|json`, `--fingerprint`,
`--max-bytes INTEGER`, `--max-depth INTEGER`, `--max-nodes INTEGER`, and
`--max-links INTEGER`. Defaults: text, fingerprint off, 1048576 bytes,
depth 64, 10000 nodes and 50000 links. Hard ceilings: 16777216 bytes,
depth 128, 100000 nodes and 500000 links. All limits must be positive integers.
The node and link limits apply to save and API adapters. Containers count toward
depth; a scalar root has depth zero.

Exit codes: 0 means no ERROR diagnostics; 1 means content errors;
2 means input boundary or usage rejection; 3 means an internal error.
WARNING and NOT_CHECKED alone do not produce exit code 1.

The report includes a fixed format and scope, summary counts, safe diagnostic
locations and the input label `input-1`. Fingerprinting is opt-in, hashes exact
input bytes including any BOM, and is null by default.
Only one explicitly supplied local regular file is read. Referenced resources
are never opened. No execution, registration, installation, model or plugin
presence checks are performed. See `docs/supported-formats.md` for limitations.
## License

Copyright 2026 XZY (xzy123590-prog)

Licensed under the Apache License, Version 2.0. See `LICENSE`.
