# Privacy boundaries

Object locations use ordinal segments such as `/$k0` and `/$k1/0`.
These are privacy-safe locations, not original JSON object key names.
They preserve insertion order and array indices, and do not guarantee
preservation of original object keys.

String values are used transiently for matching. Diagnostics contain only
fixed rules, categories, counts, statuses, severities and safe locations.
No arbitrary input strings are accepted as safe parameters.
JSON syntax errors and unknown exceptions never render exception text.

Absolute-path, network-path, file-URI, URL-credential and traversal rules
are static heuristics. They do not validate credentials or check resources.
Path-like text in object keys is intentionally not scanned.
Quoted or unconventional path notation can evade simple heuristics.

Fingerprinting is opt-in and is not called by default. A fingerprint can
correlate identical inputs. The report marks the opt-in explicitly.
JSON and text reports use the same diagnostic model. No execution logs,
telemetry, network requests or automatic scans are produced.

Save-format diagnostics additionally use fixed known field segments, such as
`/nodes/0/id` and `/links/1/origin_slot`; legacy link fields use array indices.
No arbitrary object key is copied to a location. The generic privacy walker
retains ordinal object locations for compatibility, including when it scans
saved workflows. Node IDs and link IDs are used only in transient comparison
indexes; type, widget and property values never enter diagnostic parameters.
Format and scope are fixed enums. Unknown and ambiguous selection stops before
adapter traversal. Missing verification is recorded as NOT_CHECKED, not as
proof that a workflow cannot execute.

API structural findings use /api_nodes/0, /api_nodes/0/class_type,
/api_nodes/0/inputs/$k0, or /api_nodes/0/_meta. Ordinals follow input order.
Neither node identifiers nor input keys enter locations. API class names,
metadata, reference values and literal inputs never enter report parameters.
The general string security pass retains its ordinal-only locations and
privacy heuristics; it does not interpret metadata titles or load resources.
