"""Shared targeted save-format checks, not a full JSON Schema implementation."""
from ..diagnostics import Diagnostic
from ..limits import (DEFAULT_MAX_NODES, DEFAULT_MAX_LINKS, HARD_MAX_NODES,
                      HARD_MAX_LINKS, validate_limit)
from ..rules.nodes import check_nodes, is_number, is_node_id
from ..rules.connections import check_connections


def check_workflow(value, legacy=False, max_nodes=DEFAULT_MAX_NODES,
                   max_links=DEFAULT_MAX_LINKS):
    validate_limit(max_nodes, HARD_MAX_NODES)
    validate_limit(max_links, HARD_MAX_LINKS)
    result = []

    def emit(rule, field="", severity="ERROR"):
        result.append(Diagnostic(rule, severity=severity,
                                 json_pointer="/" + field if field else ""))

    if not isinstance(value, dict):
        emit("FMT_FIELD_TYPE_INVALID")
        return result
    required = ("last_node_id", "last_link_id", "nodes", "links", "version") if legacy else (
        "version", "state", "nodes")
    for field in required:
        if field not in value:
            emit("FMT_REQUIRED_FIELD_MISSING", field)
    if "version" in value:
        version = value["version"]
        if not is_number(version) or not legacy and version != 1:
            emit("FMT_VERSION_INVALID", "version")
        elif legacy and version != 0.4:
            emit("FMT_VERSION_UNEXPECTED", "version", "WARNING")
    checks = {"nodes": lambda x: isinstance(x, list),
              "links": lambda x: isinstance(x, list)}
    if legacy:
        checks.update(last_node_id=is_node_id, last_link_id=is_number)
    else:
        checks["state"] = lambda x: isinstance(x, dict)
    for field, valid in checks.items():
        if field in value and not valid(value[field]):
            emit("FMT_FIELD_TYPE_INVALID", field)
    nodes, links = value.get("nodes"), value.get("links", [])
    over_limit = False
    for field, sequence, limit, rule in (
        ("nodes", nodes, max_nodes, "WORKFLOW_TOO_MANY_NODES"),
        ("links", links, max_links, "WORKFLOW_TOO_MANY_LINKS")):
        if isinstance(sequence, list) and len(sequence) > limit:
            emit(rule, field)
            over_limit = True
    if over_limit:
        return result
    if isinstance(nodes, list):
        node_results, index = check_nodes(nodes)
        result.extend(node_results)
        if isinstance(links, list):
            result.extend(check_connections(links, index, legacy))
    return result
