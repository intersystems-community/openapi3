import re

_OBJECTSCRIPT_RESERVED = {
    "Class", "ClassMethod", "Method", "Property", "Parameter", "Query",
    "Trigger", "XData", "Index", "ForeignKey", "Relationship", "Storage",
    "Projection", "Import", "Include", "As", "Extends", "If", "Else",
    "For", "While", "Try", "Catch", "Quit", "Return", "Set", "Do"
}

_OBJECTSCRIPT_RESERVED_LOWER = {w.lower() for w in _OBJECTSCRIPT_RESERVED}

_IDENTIFIER_RE = re.compile(r"[^A-Za-z0-9]")
_LEADING_NONLETTER_RE = re.compile(r"^[^A-Za-z]+")

def sanitize_names(value) -> str:

    if not isinstance(value, str):
        value = str(value or "")

    value = _IDENTIFIER_RE.sub("", value)
    value = _LEADING_NONLETTER_RE.sub("", value)

    if value.lower() in _OBJECTSCRIPT_RESERVED_LOWER:
        value = f"{value}Generated"

    return value


def sanitize_comments(value: str) -> str:
    """
    Escape doc comment content so a spec cannot inject extra ObjectScript lines.
    """
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        # Prevent accidental new doc-comment / class syntax injection
        line = line.replace("///", "/ / /")
        lines.append(line)
    return "\n/// ".join(lines)

_MIME_TYPE_RE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+(?:\s*;\s*[A-Za-z0-9!#$&^_.+-]+=[A-Za-z0-9!#$&^_.+-]+)*$")

def validate_media_type(value: str) -> str:
    if not isinstance(value, str) or not _MIME_TYPE_RE.fullmatch(value):
        raise ValueError(f"Unsafe or invalid media type: {value!r}")
    return value
