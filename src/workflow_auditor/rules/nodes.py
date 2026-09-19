"""Targeted node shape checks and a duplicate-preserving node index."""
import math
from ..diagnostics import Diagnostic


def is_number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def is_node_id(value):
    return type(value) in (int, str)


def id_key(value):
    return (type(value), value)


def is_pair(value):
    if isinstance(value, list):
        return len(value) == 2 and all(is_number(x) for x in value)
    return (isinstance(value, dict) and all(
        k in value and is_number(value[k]) for k in ("0", "1")))


NODE_FIELDS = {
    "id": is_node_id, "type": lambda v: isinstance(v, str),
    "pos": is_pair, "size": is_pair,
    "flags": lambda v: isinstance(v, dict), "order": is_number,
    "mode": is_number, "properties": lambda v: isinstance(v, dict),
}


def check_nodes(nodes):
    diagnostics, index = [], {}
    for i, node in enumerate(nodes):
        pointer = "/nodes/" + str(i)
        if not isinstance(node, dict):
            diagnostics.append(Diagnostic("NODE_FIELD_TYPE_INVALID", json_pointer=pointer))
            continue
        for field, valid in NODE_FIELDS.items():
            location = pointer + "/" + field
            if field not in node:
                diagnostics.append(Diagnostic("NODE_REQUIRED_FIELD_MISSING", json_pointer=location))
            elif not valid(node[field]):
                rule = "NODE_ID_INVALID" if field == "id" else "NODE_FIELD_TYPE_INVALID"
                diagnostics.append(Diagnostic(rule, json_pointer=location))
        for field in ("inputs", "outputs"):
            if field in node and not isinstance(node[field], list):
                diagnostics.append(Diagnostic("NODE_FIELD_TYPE_INVALID",
                                              json_pointer=pointer + "/" + field))
        if "id" in node and is_node_id(node["id"]):
            occurrences = index.setdefault(id_key(node["id"]), [])
            if occurrences:
                diagnostics.append(Diagnostic("NODE_ID_DUPLICATE", json_pointer=pointer + "/id"))
            occurrences.append(node)
    return diagnostics, index
