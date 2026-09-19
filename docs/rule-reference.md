# Rule reference

All messages come from a fixed template table. Boundary and JSON rules are
ERROR; privacy string rules are WARNING. Unknown internal failures are
ERROR with NOT_CHECKED. A failure to verify file properties also produces
NOT_CHECKED. The report describes detected conditions, not workflow validity.

| Rule | Condition |
| --- | --- |
| INPUT_NOT_FOUND | An explicit input or component is absent |
| INPUT_NOT_REGULAR_FILE | Not a regular readable file, ambiguous traversal, or unverifiable boundary |
| INPUT_UNC_PATH | Network path syntax |
| INPUT_DEVICE_PATH | Device namespace, reserved device or alternate stream syntax |
| INPUT_LINK_OR_REPARSE_POINT | Link or reparse attribute |
| INPUT_TOO_LARGE | Byte limit exceeded |
| JSON_EMPTY | No JSON after decoding and whitespace removal |
| JSON_INVALID | Invalid encoding or JSON syntax |
| JSON_DUPLICATE_KEY | Repeated decoded key in one object |
| JSON_NON_FINITE_NUMBER | Non-finite constant or numeric overflow |
| JSON_TOO_DEEP | Container depth exceeds limit or decoder recursion fails |
| STRING_ABSOLUTE_PATH | Drive-rooted path or whitespace-delimited POSIX path candidate |
| STRING_UNC_PATH | UNC-style string candidate |
| STRING_FILE_URI | File URI scheme candidate |
| STRING_URL_WITH_CREDENTIALS | Authority contains a user-information delimiter |
| STRING_PATH_TRAVERSAL | Parent segment followed by a path separator |
| CLI_USAGE | Invalid command-line syntax or limits |
| INTERNAL_ERROR | Unexpected internal or output failure |

String findings have a fixed category and occurrence count in JSON.
Multiple rule categories may match one value. Text output displays the
fixed diagnostic message and safe location without including original text.

## Save-format rules

Save-format rules are ERROR / CHECKED unless stated below.

| Rule | Condition |
| --- | --- |
| FMT_UNKNOWN | No supported save format was identified. |
| FMT_AMBIGUOUS | Conflicting save-format features prevent selection. |
| FMT_VERSION_INVALID | The format version is missing its required numeric value. |
| FMT_VERSION_UNEXPECTED | The legacy version differs from the expected value. |
| FMT_REQUIRED_FIELD_MISSING | A required top-level field is absent. |
| FMT_FIELD_TYPE_INVALID | A top-level field or root has an invalid type. |
| WORKFLOW_TOO_MANY_NODES | The node count exceeds the configured limit. |
| WORKFLOW_TOO_MANY_LINKS | The link count exceeds the configured limit. |
| NODE_ID_INVALID | A node identifier has an invalid type. |
| NODE_ID_DUPLICATE | A node identifier occurs more than once. |
| NODE_REQUIRED_FIELD_MISSING | A required node field is absent. |
| NODE_FIELD_TYPE_INVALID | A node or node field has an invalid type. |
| LINK_SHAPE_INVALID | A link record or field has an invalid shape or type. |
| LINK_REQUIRED_FIELD_MISSING | A required link field is absent. |
| LINK_ID_INVALID | A link identifier is not a finite number. |
| LINK_ID_DUPLICATE | A link identifier occurs more than once. |
| LINK_ORIGIN_NODE_MISSING | The origin node is absent. |
| LINK_TARGET_NODE_MISSING | The target node is absent. |
| LINK_ORIGIN_SLOT_INVALID | The origin slot is invalid or out of bounds. |
| LINK_TARGET_SLOT_INVALID | The target slot is invalid or out of bounds. |
| LINK_INPUT_BACKREF_MISMATCH | The input backreference disagrees with the link. |
| LINK_OUTPUT_BACKREF_MISMATCH | The output backreferences do not contain the link. |
| LINK_SLOT_NOT_CHECKED | Available structure cannot establish the slot bounds. |
| LINK_BACKREF_NOT_CHECKED | Available structure cannot verify the backreference. |

FMT_VERSION_UNEXPECTED is WARNING / CHECKED for finite legacy versions other
than 0.4. LINK_SLOT_NOT_CHECKED and LINK_BACKREF_NOT_CHECKED are INFO /
NOT_CHECKED. Their presence does not establish execution failure.
Format detection errors stop adapter selection. Resource excess is a content
ERROR (exit 1); invalid limit arguments are CLI_USAGE (exit 2).

## API rules

Rules are ERROR / CHECKED unless the table specifies otherwise. All use
fixed messages and safe ordinal locations. The root type uses the existing
FMT_FIELD_TYPE_INVALID rule; node/reference excess uses existing WORKFLOW
count rules. Duplicate mapping keys use JSON_DUPLICATE_KEY during loading.

| Rule | Severity / status | Condition |
| --- | --- | --- |
| API_WORKFLOW_EMPTY | WARNING / CHECKED | The API mapping contains no nodes; executability is not established. |
| API_NODE_ID_INVALID | ERROR / CHECKED | An API node identifier is not a nonempty ASCII digit string. |
| API_NODE_OBJECT_INVALID | ERROR / CHECKED | An API node must be an object. |
| API_CLASS_TYPE_MISSING | ERROR / CHECKED | An API node requires class_type. |
| API_CLASS_TYPE_INVALID | ERROR / CHECKED | API class_type must be a nonempty string. |
| API_INPUTS_MISSING | ERROR / CHECKED | An API node requires inputs. |
| API_INPUTS_INVALID | ERROR / CHECKED | API inputs must be an object. |
| API_META_INVALID | WARNING / CHECKED | Optional API metadata should be an object. |
| API_REFERENCE_SOURCE_MISSING | WARNING / NOT_CHECKED | A reference-shaped value has no confirmable source; a connection is not established. |
| API_REFERENCE_INDEX_INVALID | ERROR / CHECKED | A value naming an existing source has an invalid or missing output index. |
| API_REFERENCE_AMBIGUOUS | WARNING / NOT_CHECKED | A reference-shaped value has an unconfirmed source and invalid index; interpretation remains unchecked. |

Existing-source singleton arrays are the missing-index exception; other
non-two-item arrays remain literals. Missing-source warnings do not establish
a broken connection. Confirmed references do not establish actual slot bounds.
