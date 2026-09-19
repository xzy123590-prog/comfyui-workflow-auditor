import json
from . import __version__


SCOPES = {
    "api": "comfyui-api-format",
    "generic-json": "generic-json-security-core",
    "workflow-v1": "comfyui-workflow-v1",
    "workflow-v0.4": "comfyui-workflow-v0.4",
    "unknown": "format-detection", "ambiguous": "format-detection",
}


def make_report(diagnostics, fingerprint=None, format="generic-json"):
    ordered = sorted(diagnostics, key=lambda d: (d.json_pointer, d.rule_id, d.severity, d.status))
    return {
        "schema_version": "1",
        "tool": "comfyui-workflow-auditor",
        "tool_version": __version__,
        "scope": SCOPES[format],
        "format": format,
        "input_id": "input-1",
        "fingerprint": fingerprint,
        "summary": {
            "error_count": sum(d.severity == "ERROR" for d in ordered),
            "warning_count": sum(d.severity == "WARNING" for d in ordered),
            "info_count": sum(d.severity == "INFO" for d in ordered),
            "not_checked_count": sum(d.status == "NOT_CHECKED" for d in ordered),
        },
        "diagnostics": [d.to_dict() for d in ordered],
    }


def render(report, output_format="text"):
    if output_format == "json":
        return json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    lines = [report["tool"] + " " + report["tool_version"],
             "scope: " + report["scope"], "input: input-1"]
    fp = report["fingerprint"]
    if fp is not None:
        lines.append("fingerprint (user opt-in, sha256): " + fp["value"])
    summary = report["summary"]
    lines.append("errors={error_count} warnings={warning_count} info={info_count} "
                 "not_checked={not_checked_count}".format(**summary))
    for item in report["diagnostics"]:
        lines.append("{severity} {status} {rule_id} {json_pointer}: {message}".format(**item))
    return "\n".join(lines) + "\n"
