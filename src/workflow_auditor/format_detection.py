"""Conservative format selection; never inspect node types or widgets."""
from .rules.nodes import is_number
from .formats.api_format import is_api_id

FORMATS = ("generic-json", "workflow-v1", "workflow-v0.4", "api", "unknown", "ambiguous")


def save_format_evidence(value):
    if not isinstance(value, dict):
        return ()
    nodes = isinstance(value.get("nodes"), list)
    links = value.get("links")
    named = legacy = False
    if nodes and isinstance(links, list):
        for link in links:
            named |= isinstance(link, dict) and all(
                key in link for key in ("id", "origin_id", "origin_slot",
                                        "target_id", "target_slot", "type"))
            legacy |= isinstance(link, list) and len(link) == 6
            if named and legacy:
                break
    version = value.get("version")
    current = (is_number(version) and version == 1) or (
        nodes and isinstance(value.get("state"), dict)) or named
    old = nodes and ("last_node_id" in value or "last_link_id" in value or legacy)
    return tuple(name for name, present in (("workflow-v1", current),
                                             ("workflow-v0.4", old)) if present)


def api_format_evidence(value):
    if not isinstance(value, dict) or not value:
        return ()
    complete = False
    for key, node in value.items():
        if not is_api_id(key) or not isinstance(node, dict):
            return ()
        has_class, has_inputs = "class_type" in node, "inputs" in node
        if not (has_class or has_inputs):
            return ()
        complete |= has_class and has_inputs
    return ("api",) if complete else ()


def detect_format(value):
    evidence = save_format_evidence(value) + api_format_evidence(value)
    if len(evidence) > 1:
        return "ambiguous"
    return evidence[0] if evidence else "unknown"
