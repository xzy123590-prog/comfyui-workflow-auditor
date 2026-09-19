import argparse
import sys
from .diagnostics import Diagnostic, Rejected
from .fingerprints import fingerprint
from .input_boundary import read_input
from .json_loader import load_json
from .limits import DEFAULT_MAX_BYTES, DEFAULT_MAX_DEPTH, MAX_BYTES, MAX_DEPTH, validate_limit
from .format_detection import detect_format
from .formats import workflow_v1, workflow_v04, api_format
from .limits import (DEFAULT_MAX_NODES, DEFAULT_MAX_LINKS, HARD_MAX_NODES, HARD_MAX_LINKS)
from .report import make_report, render
from .rules.privacy_strings import scan_strings


class SafeParser(argparse.ArgumentParser):
    def error(self, _message):
        raise Rejected("CLI_USAGE")


def _integer(text):
    try:
        return int(text)
    except (ValueError, TypeError):
        raise Rejected("CLI_USAGE") from None


def _parse(argv):
    parser = SafeParser(prog="workflow-auditor", allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=SafeParser)
    audit = sub.add_parser("audit", allow_abbrev=False)
    audit.add_argument("input")
    audit.add_argument("--output-format", choices=("text", "json"), default="text")
    audit.add_argument("--fingerprint", action="store_true")
    audit.add_argument("--max-bytes", type=_integer, default=DEFAULT_MAX_BYTES)
    audit.add_argument("--max-depth", type=_integer, default=DEFAULT_MAX_DEPTH)
    audit.add_argument("--format", choices=("generic-json", "auto", "workflow-v1", "workflow-v0.4", "api"),
                       default="generic-json")
    audit.add_argument("--max-nodes", type=_integer, default=DEFAULT_MAX_NODES)
    audit.add_argument("--max-links", type=_integer, default=DEFAULT_MAX_LINKS)
    args = parser.parse_args(argv)
    try:
        validate_limit(args.max_bytes, MAX_BYTES)
        validate_limit(args.max_depth, MAX_DEPTH)
        validate_limit(args.max_nodes, HARD_MAX_NODES)
        validate_limit(args.max_links, HARD_MAX_LINKS)
    except ValueError:
        raise Rejected("CLI_USAGE") from None
    return args


def main(argv=None):
    output_format = "text"
    fp = None
    code = 0
    selected_format = "generic-json"
    try:
        args = _parse(argv)
        output_format = args.output_format
        selected_format = "unknown" if args.format == "auto" else args.format
        data = read_input(args.input, args.max_bytes)
        fp = fingerprint(data, args.fingerprint)
        try:
            value = load_json(data, args.max_depth)
        except Rejected as exc:
            diagnostics = [exc.diagnostic]
            code = 1
        else:
            if args.format == "auto":
                selected_format = detect_format(value)
            if selected_format in ("unknown", "ambiguous"):
                rule = "FMT_AMBIGUOUS" if selected_format == "ambiguous" else "FMT_UNKNOWN"
                diagnostics = [Diagnostic(rule)]
            elif selected_format == "generic-json":
                diagnostics = scan_strings(value)
            else:
                adapter = {"workflow-v1": workflow_v1, "workflow-v0.4": workflow_v04,
                           "api": api_format}[selected_format]
                diagnostics = adapter.validate(value, args.max_nodes, args.max_links)
                diagnostics.extend(scan_strings(value))
            code = 1 if any(d.severity == "ERROR" for d in diagnostics) else 0
    except Rejected as exc:
        diagnostics = [exc.diagnostic]
        code = 2
    except Exception:
        diagnostics = [Diagnostic("INTERNAL_ERROR", status="NOT_CHECKED")]
        code = 3
    try:
        sys.stdout.write(render(make_report(diagnostics, fp, selected_format), output_format))
    except Exception:
        try:
            sys.stderr.write("INTERNAL_ERROR: Report output failed.\n")
        except Exception:
            pass
        return 3
    return code
