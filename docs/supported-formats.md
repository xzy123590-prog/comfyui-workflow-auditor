# Supported formats

TARGETED_STATIC_SUBSET / NOT_A_FULL_JSON_SCHEMA_IMPLEMENTATION.
Pre-release offline static checks; the default remains generic-json.

| Selection | Report format | Scope |
| --- | --- | --- |
| generic-json (default) | generic-json | generic-json-security-core |
| workflow-v1 | workflow-v1 | comfyui-workflow-v1 |
| workflow-v0.4 | workflow-v0.4 | comfyui-workflow-v0.4 |
| api | api | comfyui-api-format |
| auto, no clear evidence | unknown | format-detection |
| auto, conflicting evidence | ambiguous | format-detection |

Auto requires an object root. A finite non-boolean version equal to 1 is a
current-format signal. A nodes array together with a state object or a named
link record is also a current-format signal. A nodes array together with a
legacy counter or a six-item link record is a legacy signal. Any occurrence
of each link shape can establish conflicting signals. Empty links alone do
not identify a format. Selection is followed by validation; a format signal
is not proof of valid content.

API evidence requires a nonempty object with nonempty ASCII digit string
keys and object values. Every node must contain class_type or inputs and
at least one must contain both. Values of those fields are not inspected
for selection. Extra node fields do not matter. Save signals cannot coexist
with this all-digit key mapping; detectors nevertheless independently return
evidence and multiple positive detectors produce FMT_AMBIGUOUS. Empty
objects remain FMT_UNKNOWN in auto mode. Detection never runs an adapter.

Explicit selection bypasses detection but applies all selected checks.
Version 1 requires version=1, state and nodes. Links may be absent and are
then treated as empty. Legacy requires both counters, nodes, links and a
finite numeric version. A version other than 0.4 produces a WARNING, not a
schema ERROR. Both formats allow additional fields and do not fully validate
optional metadata or state contents.

Nodes require id, type, pos, size, flags, order, mode and properties.
Coordinates accept a pair of numbers or an object with numeric members
named 0 and 1. Optional inputs and outputs must be arrays. Node IDs are
integers or strings; integer 1 and string "1" remain distinct. All duplicate
node occurrences are retained; their ports are not selected arbitrarily.

Named current-format links and six-element legacy links require an ID,
origin ID, origin slot, target ID, target slot and type. Link IDs are finite
numbers; 1 and 1.0 identify the same link. Endpoints are integers or strings.
Slots are integers or strings. Types may be strings, arrays of strings or
finite numbers. Booleans are never numbers, IDs or slots for these checks.
Invalid link endpoint or type shapes use LINK_SHAPE_INVALID.

Integer slots must be nonnegative and within a supplied port array. String
slots, missing or malformed arrays, and ambiguous duplicate nodes cannot
establish bounds. They produce INFO / NOT_CHECKED. Out-of-range slots do not
trigger backreference mismatches; their backreferences remain NOT_CHECKED.
A numeric input link differing from the top-level link, including an explicit
null input link, is a mismatch. An output links array of finite numbers must
contain the link. Missing, malformed or unverifiable backreference data is
NOT_CHECKED. Boolean backreferences are never treated as numeric matches.
No node definitions or dynamic slot schemas are loaded.

Node and link counts use existing array lengths. If either limit is exceeded,
adapter traversal stops before building indexes. The byte and depth limits
still protect input parsing; privacy string scanning retains its bounded
input behavior. Diagnostics never include IDs, types, widgets or properties.

A report does not prove workflow executability. Execution, automatic repair,
node registration, installed plugins and model files are outside
this implementation. All fixtures and test mutations are synthetic.

## Generic JSON

The generic-json security core checks strict JSON loading, byte/depth limits,
duplicate keys, non-finite numbers and sensitive string patterns. It performs
no workflow structural checks. Selecting auto is always explicit.

## API targeted subset

The root must be an object; each value must be a node object. IDs must be
nonempty ASCII digit strings. Identity is exact: "1" and "01" are distinct.
class_type is a required nonempty string; inputs is a required object.
Optional _meta must be an object (WARNING otherwise). Metadata titles have
no format-specific validation. Unknown node fields are allowed.
An explicitly selected empty API mapping produces API_WORKFLOW_EMPTY
(WARNING); that does not establish executability.

Only direct input values are examined as references. A two-item array with
an exact existing string source and non-boolean nonnegative integer index
is confirmed without inferring output bounds. Existing sources with invalid
indices produce ERROR / CHECKED. As a narrow missing-index exception, a
singleton containing an existing source also produces this error. Other
non-two-item arrays are literals. Numeric non-string source values are not
coerced. Nested arrays and objects are not recursively interpreted.

A two-item value with an absent ASCII digit string source and valid index
is WARNING / NOT_CHECKED; with an invalid index it is ambiguous and also
WARNING / NOT_CHECKED. Neither finding proves a damaged connection.
Other unresolvable string lists are literals. NOT_CHECKED counts explicitly
record findings that cannot be established from the supplied structure.

max-nodes limits top-level entries before traversal. max-links counts
confirmed references plus absent numeric sources with valid indices; it
excludes literals, invalid indices and ambiguous values. Traversal stops at
the first excess without copying inputs. Limits are content errors (exit 1).
Positive integer CLI limits are enforced against hard ceilings (exit 2).
No node classes, custom nodes, plugin inventories, actual output arities,
files, models, weights or remote endpoints are inspected. Cycles and semantic
input compatibility are outside this subset. Checks do not prove execution.
