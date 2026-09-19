"""Offline targeted API checks; no node definitions or resources are loaded."""
from ..diagnostics import Diagnostic
from ..limits import (DEFAULT_MAX_NODES, DEFAULT_MAX_LINKS, HARD_MAX_NODES,
                      HARD_MAX_LINKS, validate_limit)


def is_api_id(value):
    return isinstance(value, str) and bool(value) and all("0" <= c <= "9" for c in value)


def validate(value, max_nodes=DEFAULT_MAX_NODES, max_links=DEFAULT_MAX_LINKS):
    validate_limit(max_nodes, HARD_MAX_NODES)
    validate_limit(max_links, HARD_MAX_LINKS)
    result = []

    def emit(rule, pointer="", severity="ERROR", status="CHECKED"):
        result.append(Diagnostic(rule, severity=severity, status=status, json_pointer=pointer))

    if not isinstance(value, dict):
        emit("FMT_FIELD_TYPE_INVALID")
        return result
    if len(value) > max_nodes:
        emit("WORKFLOW_TOO_MANY_NODES", "/api_nodes")
        return result
    if not value:
        emit("API_WORKFLOW_EMPTY", "/api_nodes", "WARNING")
        return result
    references = 0
    for ordinal, (node_id, node) in enumerate(value.items()):
        pointer = "/api_nodes/" + str(ordinal)
        if not is_api_id(node_id):
            emit("API_NODE_ID_INVALID", pointer)
        if not isinstance(node, dict):
            emit("API_NODE_OBJECT_INVALID", pointer)
            continue
        for field, valid in (("class_type", lambda x: isinstance(x, str) and bool(x)),
                             ("inputs", lambda x: isinstance(x, dict))):
            if field not in node:
                emit("API_" + field.upper() + "_MISSING", pointer + "/" + field)
            elif not valid(node[field]):
                emit("API_" + field.upper() + "_INVALID", pointer + "/" + field)
        if "_meta" in node and not isinstance(node["_meta"], dict):
            emit("API_META_INVALID", pointer + "/_meta", "WARNING")
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        for input_ordinal, item in enumerate(inputs.values()):
            location = pointer + "/inputs/$k" + str(input_ordinal)
            if not isinstance(item, list) or not item or not isinstance(item[0], str):
                continue
            exists = item[0] in value
            # A singleton resolving source is the explicit missing-index case.
            if len(item) == 1 and exists:
                emit("API_REFERENCE_INDEX_INVALID", location)
                continue
            if len(item) != 2:
                continue
            valid_index = type(item[1]) is int and item[1] >= 0
            if exists:
                if not valid_index:
                    emit("API_REFERENCE_INDEX_INVALID", location)
                    continue
            elif is_api_id(item[0]):
                if not valid_index:
                    emit("API_REFERENCE_AMBIGUOUS", location, "WARNING", "NOT_CHECKED")
                    continue
                emit("API_REFERENCE_SOURCE_MISSING", location, "WARNING", "NOT_CHECKED")
            else:
                continue
            references += 1
            if references > max_links:
                emit("WORKFLOW_TOO_MANY_LINKS", "/api_nodes")
                return result
    return result
