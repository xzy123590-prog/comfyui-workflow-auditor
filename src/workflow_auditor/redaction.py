"""Allowlisted report primitives; never redact by copying input substrings."""
import re

POINTER = re.compile(r"(?:/(?:\$k[0-9]+|[0-9]+|api_nodes|class_type|_meta|nodes|links|version|state|last_node_id|last_link_id|id|type|pos|size|flags|order|mode|properties|inputs|outputs|origin_id|origin_slot|target_id|target_slot))*", re.ASCII)
CATEGORIES = frozenset({"absolute_path", "unc_path", "file_uri",
                        "url_credentials", "path_traversal"})


def safe_pointer(value):
    if type(value) is not str or POINTER.fullmatch(value) is None:
        raise ValueError("Invalid safe location.")
    return value


def safe_parameters(values):
    if type(values) is not dict:
        raise ValueError("Invalid safe parameters.")
    result = {}
    for key, value in values.items():
        if key == "count" and type(value) is int and value >= 0:
            result[key] = value
        elif key == "category" and type(value) is str and value in CATEGORIES:
            result[key] = value
        elif key == "verified" and type(value) is bool:
            result[key] = value
        else:
            raise ValueError("Invalid safe parameters.")
    return result
