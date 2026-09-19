import re
from ..diagnostics import Diagnostic

PATTERNS = (
    ("STRING_ABSOLUTE_PATH", "absolute_path",
     re.compile(r"(?i)(?<![A-Za-z0-9])[a-z]:[\\/]|(?<!\S)/(?!/)[A-Za-z0-9_.~-]")),
    ("STRING_UNC_PATH", "unc_path", re.compile(r"\\\\[^\\\s]+\\|(?<!:)//[^/\s]+/")),
    ("STRING_FILE_URI", "file_uri", re.compile(r"(?i)\bfile:")),
    ("STRING_URL_WITH_CREDENTIALS", "url_credentials",
     re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s?#]*@")),
    ("STRING_PATH_TRAVERSAL", "path_traversal",
     re.compile(r"(?<![A-Za-z0-9_.])\.\.[\\/]")),
)


def scan_strings(value):
    diagnostics = []
    stack = [("", value)]
    while stack:
        pointer, item = stack.pop()
        if isinstance(item, dict):
            children = [(pointer + "/$k" + str(i), child)
                        for i, child in enumerate(item.values())]
            stack.extend(reversed(children))
        elif isinstance(item, list):
            stack.extend((pointer + "/" + str(i), item[i])
                         for i in range(len(item) - 1, -1, -1))
        elif isinstance(item, str):
            for rule, category, pattern in PATTERNS:
                count = sum(1 for _ in pattern.finditer(item))
                if count:
                    diagnostics.append(Diagnostic(
                        rule, severity="WARNING", json_pointer=pointer,
                        safe_parameters={"category": category, "count": count}))
    return diagnostics
