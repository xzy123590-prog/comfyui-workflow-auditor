# Security boundaries

Reports contain fixed message templates and ordinal object locations.
They do not include input filenames, keys, original strings or exception
text. Rule matching is heuristic; a clean report does not prove that an
input is safe, executable or free of secrets.

The input boundary rejects network path syntax, device syntax, links,
reparse points and unverified file types. Windows uses standard-library
bindings to native no-follow handles and denies write/delete sharing while
holding checked ancestors. POSIX uses directory-relative no-follow opens.
Unsupported verification fails closed with NOT_CHECKED.

A concurrent writer or privileged actor is outside a complete snapshot
guarantee. Bounded reads and metadata rechecks detect size growth and
ordinary modifications. Fingerprints describe bytes actually read.

This is an unofficial local pre-release static auditor, with no telemetry or
automatic network operations. It is not affiliated with or endorsed by
ComfyUI. No workflow execution or automatic repair is implemented. This project is licensed under the Apache License, Version 2.0; see `LICENSE`.

The save-format and Workflow API Format adapters validate only targeted static
subsets of workflow data. No resource referenced by a node, link, or API input
is accessed. Fixed field names and array indices extend safe locations;
arbitrary node IDs and input keys remain excluded. Count limits bound node
indexing, link traversal, and API-reference analysis.

Unverifiable slots, backreferences, missing-source reference candidates, and
other ambiguous structures are reported conservatively, including NOT_CHECKED
where appropriate. Ordinary or nested two-element lists are not treated as
connections solely because of their shape.

These checks do not prove workflow executability, installed-node availability,
plugin presence, or model and weight availability.
