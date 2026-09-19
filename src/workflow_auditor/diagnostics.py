from dataclasses import dataclass, field
from .redaction import safe_parameters, safe_pointer

TEMPLATES = {
    'API_WORKFLOW_EMPTY': 'The API mapping contains no nodes; executability is not established.',
    'API_NODE_ID_INVALID': 'An API node identifier is not a nonempty ASCII digit string.',
    'API_NODE_OBJECT_INVALID': 'An API node must be an object.',
    'API_CLASS_TYPE_MISSING': 'An API node requires class_type.',
    'API_CLASS_TYPE_INVALID': 'API class_type must be a nonempty string.',
    'API_INPUTS_MISSING': 'An API node requires inputs.',
    'API_INPUTS_INVALID': 'API inputs must be an object.',
    'API_META_INVALID': 'Optional API metadata should be an object.',
    'API_REFERENCE_SOURCE_MISSING': 'A reference-shaped value has no confirmable source; a connection is not established.',
    'API_REFERENCE_INDEX_INVALID': 'A value naming an existing source has an invalid or missing output index.',
    'API_REFERENCE_AMBIGUOUS': 'A reference-shaped value has an unconfirmed source and invalid index; interpretation remains unchecked.',

    "INPUT_NOT_FOUND": "The input file was not found.",
    "INPUT_NOT_REGULAR_FILE": "The input could not be verified as a readable regular file.",
    "INPUT_UNC_PATH": "UNC input paths are not accepted.",
    "INPUT_DEVICE_PATH": "Device input paths are not accepted.",
    "INPUT_LINK_OR_REPARSE_POINT": "Links and reparse points are not accepted.",
    "INPUT_TOO_LARGE": "The input exceeds the byte limit.",
    "JSON_EMPTY": "The JSON input is empty.",
    "JSON_INVALID": "The input is not strict UTF-8 JSON.",
    "JSON_DUPLICATE_KEY": "The JSON contains a duplicate object key.",
    "JSON_NON_FINITE_NUMBER": "Non-finite JSON numbers are not accepted.",
    "JSON_TOO_DEEP": "The JSON exceeds the nesting limit.",
    "STRING_ABSOLUTE_PATH": "A string contains an absolute path candidate.",
    "STRING_UNC_PATH": "A string contains a UNC path candidate.",
    "STRING_FILE_URI": "A string contains a file URI candidate.",
    "STRING_URL_WITH_CREDENTIALS": "A string contains URL credentials.",
    "STRING_PATH_TRAVERSAL": "A string contains a path traversal candidate.",
    "CLI_USAGE": "Command-line usage was rejected.",
    "INTERNAL_ERROR": "An internal error prevented processing.",
    'FMT_UNKNOWN': 'No supported save format was identified.',
    'FMT_AMBIGUOUS': 'Conflicting save-format features prevent selection.',
    'FMT_VERSION_INVALID': 'The format version is missing its required numeric value.',
    'FMT_VERSION_UNEXPECTED': 'The legacy version differs from the expected value.',
    'FMT_REQUIRED_FIELD_MISSING': 'A required top-level field is absent.',
    'FMT_FIELD_TYPE_INVALID': 'A top-level field or root has an invalid type.',
    'WORKFLOW_TOO_MANY_NODES': 'The node count exceeds the configured limit.',
    'WORKFLOW_TOO_MANY_LINKS': 'The link count exceeds the configured limit.',
    'NODE_ID_INVALID': 'A node identifier has an invalid type.',
    'NODE_ID_DUPLICATE': 'A node identifier occurs more than once.',
    'NODE_REQUIRED_FIELD_MISSING': 'A required node field is absent.',
    'NODE_FIELD_TYPE_INVALID': 'A node or node field has an invalid type.',
    'LINK_SHAPE_INVALID': 'A link record or field has an invalid shape or type.',
    'LINK_REQUIRED_FIELD_MISSING': 'A required link field is absent.',
    'LINK_ID_INVALID': 'A link identifier is not a finite number.',
    'LINK_ID_DUPLICATE': 'A link identifier occurs more than once.',
    'LINK_ORIGIN_NODE_MISSING': 'The origin node is absent.',
    'LINK_TARGET_NODE_MISSING': 'The target node is absent.',
    'LINK_ORIGIN_SLOT_INVALID': 'The origin slot is invalid or out of bounds.',
    'LINK_TARGET_SLOT_INVALID': 'The target slot is invalid or out of bounds.',
    'LINK_INPUT_BACKREF_MISMATCH': 'The input backreference disagrees with the link.',
    'LINK_OUTPUT_BACKREF_MISMATCH': 'The output backreferences do not contain the link.',
    'LINK_SLOT_NOT_CHECKED': 'Available structure cannot establish the slot bounds.',
    'LINK_BACKREF_NOT_CHECKED': 'Available structure cannot verify the backreference.',
}


@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    severity: str = "ERROR"
    status: str = "CHECKED"
    json_pointer: str = ""
    safe_parameters: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.rule_id not in TEMPLATES:
            raise ValueError("Unknown rule.")
        if self.severity not in {"ERROR", "WARNING", "INFO"}:
            raise ValueError("Unknown severity.")
        if self.status not in {"CHECKED", "NOT_CHECKED"}:
            raise ValueError("Unknown status.")
        safe_pointer(self.json_pointer)
        object.__setattr__(self, "safe_parameters", safe_parameters(self.safe_parameters))

    def to_dict(self):
        return dict(rule_id=self.rule_id, severity=self.severity, status=self.status,
                    json_pointer=safe_pointer(self.json_pointer),
                    message=TEMPLATES[self.rule_id],
                    safe_parameters=safe_parameters(self.safe_parameters))


class Rejected(Exception):
    def __init__(self, rule_id, status="CHECKED"):
        self.diagnostic = Diagnostic(rule_id, status=status)
        super().__init__(TEMPLATES[rule_id])
