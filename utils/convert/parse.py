"""Parse any preset spoke (xml / v1 flat json / v2 grouped json) into the canon.

Each ``parse_*`` starts from :func:`canon_defaults` and overlays whatever the
source actually carries, so the result is always a complete canon regardless of
how much the source format supports. That is what implements the projection
rule: an xml source simply never touches the json-only effects, which keeps
their canonical defaults.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from utils.convert import registry as R
from utils.convert.detect import detect_format
from utils.convert.legacy import migrate

_ROOT = Path(__file__).resolve().parents[2]
_V2_TEMPLATE = _ROOT / "default_presets/json_v2/default.json"

#: Convolver kernel names that are placeholders rather than real ``.irs`` files.
#: Matched against the whole (stripped) value - "Kernel" as a substring would
#: otherwise eat legitimate names like "TubeKernel.irs".
_KERNEL_PLACEHOLDERS = frozenset(
    {
        "Select impulse response file",
        "Kernel",
        "Choose Impulse Response",
        "Selecione o arquivo de impulso de resposta",
    }
)

#: A buggy converter once wrote "&" in kernel filenames as a broken close tag,
#: which leaves the document unparseable. Repaired textually before the document
#: reaches ElementTree.
_TEXT_REPAIRS = (
    (">Select impulse response file</string>amp;", "&amp;"),
    ("></string>amp;", "&amp;"),
)


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------


def _as_int(value) -> int:
    """Read a scalar as int, tolerating floats and float-ish strings ("5.0")."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(round(value))
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        return int(round(float(text)))


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true")


def _split(value) -> list[str]:
    """Split a ``";"``-joined list into non-empty parts, tolerating a real list.

    Drops the trailing empty field left by values like ``"0.0;0.0;"``.
    """
    if isinstance(value, list):
        return [str(part) for part in value]
    return [part for part in str(value).split(sep=";") if part.strip() != ""]


def coerce(kind: str, value):
    """Normalise ``value`` into the canonical representation for ``kind``."""
    if value is None:
        return None
    if kind == "bool":
        return _as_bool(value=value)
    if kind == "int":
        return _as_int(value=value)
    if kind == "float":
        return float(value)
    if kind == "str":
        return str(value)
    if kind == "int_list":
        return [_as_int(value=part) for part in _split(value=value)]
    if kind == "bool_list":
        return [_as_bool(value=part) for part in _split(value=value)]
    if kind == "double_list":
        return [float(part) for part in _split(value=value)]
    if kind == "nullable_long":
        number = _as_int(value=value)
        # Both spokes spell "unset" differently: v2 uses null, v1 uses -1.
        return None if number < 0 else number
    raise ValueError(f"unknown kind: {kind}")


def clean_kernel_name(name: str) -> str:
    """Blank placeholder convolver kernel names, keeping real ``.irs`` names."""
    return "" if name.strip() in _KERNEL_PLACEHOLDERS else name


# ---------------------------------------------------------------------------
# Canon defaults
# ---------------------------------------------------------------------------


def _read_v2(obj: dict) -> dict:
    """Read whatever canon fields ``obj`` (a v2 document) actually contains."""
    canon: dict = {}
    for f in R.FIELDS:
        if f.group:
            group = obj.get(f.group)
            if not isinstance(group, dict) or f.leaf not in group:
                continue
            raw = group[f.leaf]
        else:
            if f.canon not in obj:
                continue
            raw = obj[f.canon]
        canon[f.canon] = coerce(kind=f.kind, value=raw)
    return canon


_v2_template_cache: dict | None = None


def _v2_template() -> dict:
    """The parsed v2 template, read from disk once and cached.

    Only ever read from, never mutated - :func:`canon_defaults` re-derives a fresh
    canon (with fresh lists) from it on every call, so callers can mutate their
    result freely. Caching matters because pruning re-derives defaults once per
    file across thousands of presets.
    """
    global _v2_template_cache
    if _v2_template_cache is None:
        with open(file=_V2_TEMPLATE, mode="r", encoding="utf-8") as fh:
            _v2_template_cache = json.load(fp=fh)
    return _v2_template_cache


def canon_defaults() -> dict:
    """A fresh canon holding every field at its v2 template default.

    The v2 template is the superset of all three spokes, which makes it the
    natural place to source defaults for fields the narrower formats lack.
    """
    return _read_v2(obj=_v2_template())


# ---------------------------------------------------------------------------
# Spoke parsers
# ---------------------------------------------------------------------------


def parse_v2(text: str) -> tuple[dict, None]:
    """Parse a v2 grouped preset. v2 is device-agnostic, so the mode is ``None``."""
    canon = canon_defaults()
    canon.update(_read_v2(obj=json.loads(s=text)))
    return canon, None


def parse_v1(text: str) -> tuple[dict, str]:
    """Parse a v1 flat preset, returning the canon and the mode it was written in.

    Speaker presets arrive in the ``spk*`` namespace; keys are folded back to the
    base namespace so one registry column covers both.
    """
    obj = json.loads(s=text)
    mode = "2" if any(k.startswith("spk") for k in obj) else "1"
    base = {R.to_base_key(key=k): v for k, v in obj.items()}

    canon = canon_defaults()
    for f in R.FIELDS:
        if f.v1 and f.v1 in base:
            canon[f.canon] = coerce(kind=f.kind, value=base[f.v1])
    return canon, mode


def read_xml(text: str) -> dict[str, tuple[str, str]]:
    """Parse a preset ``<map>`` into ``{name: (tag, value)}``.

    ``<string>`` carries its value as element text (``""`` when empty); ``<int>``
    and ``<boolean>`` carry it in the ``value`` attribute.
    """
    for broken, fixed in _TEXT_REPAIRS:
        text = text.replace(broken, fixed)

    root = ET.fromstring(text=text)
    entries: dict[str, tuple[str, str]] = {}
    for el in root:
        name = el.get("name")
        if name is None:
            continue
        if el.tag == "string":
            entries[name] = ("string", el.text if el.text is not None else "")
        else:
            entries[name] = (el.tag, el.get("value", ""))
    return entries


def parse_xml(text: str) -> tuple[dict, str | None]:
    """Parse a preset xml into the canon and its mode.

    Legacy documents are normalised onto the canonical parameter ids and scales
    first, so anything older than 2.7.2 is handled without the registry needing
    to know two generations of key names.

    The mode comes from a single parameter; presets that predate it leave it out,
    so the mode is ``None`` when it can't be read from the document. That is a
    genuine "unknown", distinct from a stated mode - the caller decides whether
    to guess from the filename or emit both variants, rather than this silently
    assuming one mode.
    """
    entries = migrate(entries=read_xml(text=text))
    canon = canon_defaults()

    stated = entries.get(R.MODE_KEY)
    mode = stated[1].strip() if stated else None
    if mode not in ("1", "2"):
        mode = None

    for f in R.FIELDS:
        if not f.xml or f.xml not in entries:
            continue
        tag, raw = entries[f.xml]

        if f.kind == "bool":
            canon[f.canon] = _as_bool(value=raw)
            continue
        if f.kind == "str":
            value = clean_kernel_name(name=raw) if f.special == "kernel" else raw
            canon[f.canon] = value
            continue
        if R.is_list_kind(kind=f.kind):
            # Lists reach xml as a ";"-joined string; no member is rescaled.
            canon[f.canon] = coerce(kind=f.kind, value=raw)
            continue

        # Numeric: read the stored scalar, then apply the xml <-> canon formula.
        # Nothing is clamped - the engine accepts values the UI cannot reach.
        canon[f.canon] = coerce(
            kind=f.kind, value=f.codec.decode(raw=_as_int(value=raw))
        )

    # Dynamic System keeps its whole curve in one string.
    ds = entries.get(R.DS_XML_KEY)
    if ds:
        parts = _split(value=ds[1])
        if len(parts) >= len(R.DS_MEMBERS):
            for name, part in zip(R.DS_MEMBERS, parts):
                canon[name] = _as_int(value=part)

    return canon, mode


_PARSERS = {"xml": parse_xml, "v1": parse_v1, "v2": parse_v2}


def parse(text: str) -> tuple[dict, str | None]:
    """Parse any spoke into ``(canon, mode)``; ``mode`` is ``None`` for v2."""
    fmt = detect_format(text=text)
    if fmt is None:
        raise ValueError("unrecognized preset (not xml / v1 / v2)")
    return _PARSERS[fmt](text=text)
