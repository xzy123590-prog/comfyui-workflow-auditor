"""Checks only edges and backreferences available in the input itself."""
from ..diagnostics import Diagnostic
from .nodes import is_number, is_node_id, id_key

LINK_FIELDS = ("id", "origin_id", "origin_slot", "target_id", "target_slot", "type")


def _link_type(value):
    return (isinstance(value, str) or is_number(value) or
            isinstance(value, list) and all(isinstance(x, str) for x in value))


def check_connections(links, nodes, legacy=False):
    diagnostics, seen = [], set()

    def emit(rule, pointer):
        unchecked = rule.endswith("NOT_CHECKED")
        diagnostics.append(Diagnostic(rule, severity="INFO" if unchecked else "ERROR",
                                      status="NOT_CHECKED" if unchecked else "CHECKED",
                                      json_pointer=pointer))

    for i, link in enumerate(links):
        base = "/links/" + str(i)
        if legacy:
            if not isinstance(link, list) or len(link) != 6:
                emit("LINK_SHAPE_INVALID", base)
                continue
            fields = dict(zip(LINK_FIELDS, link))
        else:
            if not isinstance(link, dict):
                emit("LINK_SHAPE_INVALID", base)
                continue
            fields = link

        def location(field):
            return base + "/" + (str(LINK_FIELDS.index(field)) if legacy else field)

        for field in LINK_FIELDS:
            if field not in fields:
                emit("LINK_REQUIRED_FIELD_MISSING", location(field))
        link_id = fields.get("id")
        valid_id = "id" in fields and is_number(link_id)
        if "id" in fields:
            if not valid_id:
                emit("LINK_ID_INVALID", location("id"))
            elif link_id in seen:
                emit("LINK_ID_DUPLICATE", location("id"))
            else:
                seen.add(link_id)
        if "type" in fields and not _link_type(fields["type"]):
            emit("LINK_SHAPE_INVALID", location("type"))

        for side, ports in (("origin", "outputs"), ("target", "inputs")):
            endpoint, slot_field = side + "_id", side + "_slot"
            slot_location = location(slot_field)
            occurrences = []
            if endpoint in fields:
                if not is_node_id(fields[endpoint]):
                    emit("LINK_SHAPE_INVALID", location(endpoint))
                else:
                    occurrences = nodes.get(id_key(fields[endpoint]), [])
                    if not occurrences:
                        emit("LINK_" + side.upper() + "_NODE_MISSING", location(endpoint))
            slot = fields.get(slot_field)
            if slot_field not in fields:
                emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                continue
            if type(slot) not in (int, str) or type(slot) is int and slot < 0:
                emit("LINK_" + side.upper() + "_SLOT_INVALID", slot_location)
                emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                continue
            # Duplicate nodes do not justify selecting one occurrence's ports.
            node = occurrences[0] if len(occurrences) == 1 else None
            array = node.get(ports) if node is not None else None
            if type(slot) is str or not isinstance(array, list):
                emit("LINK_SLOT_NOT_CHECKED", slot_location)
                emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                continue
            if slot >= len(array):
                emit("LINK_" + side.upper() + "_SLOT_INVALID", slot_location)
                emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                continue
            port = array[slot]
            if not isinstance(port, dict) or not valid_id:
                emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                continue
            if side == "target":
                if "link" not in port or (port["link"] is not None and not is_number(port["link"])):
                    emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                elif port["link"] != link_id:
                    emit("LINK_INPUT_BACKREF_MISMATCH", slot_location)
            else:
                refs = port.get("links")
                if not isinstance(refs, list) or not all(is_number(x) for x in refs):
                    emit("LINK_BACKREF_NOT_CHECKED", slot_location)
                elif link_id not in refs:
                    emit("LINK_OUTPUT_BACKREF_MISMATCH", slot_location)
    return diagnostics
