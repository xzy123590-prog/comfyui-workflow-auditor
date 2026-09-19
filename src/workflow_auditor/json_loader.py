import json
import math
from .diagnostics import Rejected
from .limits import DEFAULT_MAX_DEPTH, MAX_DEPTH, validate_limit


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Rejected("JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _constant(_value):
    raise Rejected("JSON_NON_FINITE_NUMBER")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise Rejected("JSON_NON_FINITE_NUMBER")
    return result


def _check_depth(text, maximum):
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > maximum:
                raise Rejected("JSON_TOO_DEEP")
        elif char in "]}":
            depth -= 1


def load_json(data, max_depth=DEFAULT_MAX_DEPTH):
    validate_limit(max_depth, MAX_DEPTH)
    try:
        text = data.decode("utf-8-sig", errors="strict")
        if not text.strip():
            raise Rejected("JSON_EMPTY")
        _check_depth(text, max_depth)
        return json.loads(text, object_pairs_hook=_pairs,
                          parse_constant=_constant, parse_float=_float)
    except RecursionError:
        raise Rejected("JSON_TOO_DEEP") from None
    except (UnicodeError, ValueError):
        raise Rejected("JSON_INVALID") from None
