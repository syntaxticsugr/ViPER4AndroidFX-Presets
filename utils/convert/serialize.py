"""Serialize the canon into any preset spoke (v2 json / v1 json / canonical xml).

Every serializer starts from the matching ``default_presets/`` template and
overlays the canon onto it. The template is doing real work here: it supplies the
defaults *and* decides which keys exist, so per-mode feature availability - the
speaker xml carrying no Bass or Dynamic System, the speaker v1 namespace being
``spk``-prefixed - falls out without being restated in code.

A canon field the target template has no key for is simply dropped, which is what
makes the lossy direction (v2 -> xml) behave.
"""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from utils.convert import registry as R
from utils.convert.parse import read_xml

_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATES = {
    "v2": _ROOT / "default_presets/json_v2/default.json",
    "v1_1": _ROOT / "default_presets/json_v1/default_m1.json",
    "v1_2": _ROOT / "default_presets/json_v1/default_m2.json",
    "xml_1": _ROOT / "default_presets/xml/default_m1.xml",
    "xml_2": _ROOT / "default_presets/xml/default_m2.xml",
}

_XML_HEADER = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>'


def _load_json(name: str) -> dict:
    with open(file=_TEMPLATES[name], mode="r", encoding="utf-8") as fh:
        return json.load(fp=fh)


def _load_text(name: str) -> str:
    with open(file=_TEMPLATES[name], mode="r", encoding="utf-8") as fh:
        return fh.read()


def _check_mode(mode: str) -> str:
    if mode not in ("1", "2"):
        raise ValueError(f"mode must be '1' (headphone) or '2' (speaker), got {mode!r}")
    return mode


def _join(f: R.Field, values: list) -> str:
    """Encode a canon list as the ``";"``-joined string v1 and xml both use."""
    if f.kind == "bool_list":
        parts = ["1" if bool(v) else "0" for v in values]
    elif f.kind == "double_list":
        parts = [str(float(v)) for v in values]
    else:
        parts = [str(int(v)) for v in values]
    text = ";".join(parts)
    # The EQ band string carries a trailing separator in both formats.
    return f"{text};" if f.trailing and parts else text


# ---------------------------------------------------------------------------
# v2 grouped JSON
# ---------------------------------------------------------------------------


def serialize_v2(canon: dict) -> dict:
    """Render the canon as a v2 grouped preset (device-agnostic).

    The canon already *is* the v2 value space, so this only has to re-nest it.
    """
    out = _load_json(name="v2")
    for f in R.FIELDS:
        if f.canon not in canon:
            continue
        value = canon[f.canon]
        if f.group:
            out.setdefault(f.group, {})[f.leaf] = value
        else:
            out[f.canon] = value
    return out


# ---------------------------------------------------------------------------
# v1 flat JSON
# ---------------------------------------------------------------------------


def serialize_v1(canon: dict, mode: str) -> dict:
    """Render the canon as a v1 flat preset in ``mode``'s key namespace.

    Headphone presets use the base keys, speaker presets the ``spk*`` ones (with
    Speaker Optimization the lone key that is spelled the same in both).
    """
    _check_mode(mode=mode)
    out = _load_json(name=f"v1_{mode}")

    for f in R.FIELDS:
        if not f.v1 or f.canon not in canon:
            continue
        key = R.to_spk_key(base_key=f.v1) if mode == "2" else f.v1
        if key not in out:
            continue

        value = canon[f.canon]
        if R.is_list_kind(kind=f.kind):
            out[key] = _join(f=f, values=value)
        elif f.kind == "nullable_long":
            # v1 spells "unset" as -1 where v2 uses null.
            out[key] = -1 if value is None else int(value)
        elif f.kind == "bool":
            out[key] = bool(value)
        elif f.kind == "str":
            out[key] = str(value)
        else:
            out[key] = int(value)
    return out


# ---------------------------------------------------------------------------
# Canonical XML
# ---------------------------------------------------------------------------


def _xml_value(f: R.Field, value) -> str:
    """Encode one canon value into its xml textual form."""
    if f.kind == "bool":
        return "true" if value else "false"
    if f.kind == "str":
        return str(value)
    if R.is_list_kind(kind=f.kind):
        return _join(f=f, values=value)
    # Numeric: invert the xml <-> canon formula. Nothing is clamped; an
    # IdxList simply snaps to its nearest step.
    return str(int(round(f.codec.encode(val=value))))


def serialize_xml(canon: dict, mode: str) -> list[tuple[str, str, str]]:
    """Render the canon as canonical xml elements ``[(tag, name, value)]``.

    Element order, tags and the set of parameters all come from the mode's
    template, so anything that mode does not support is left out entirely.
    """
    _check_mode(mode=mode)
    template = read_xml(text=_load_text(name=f"xml_{mode}"))

    elements: list[tuple[str, str, str]] = []
    for name, (tag, default) in template.items():
        if name == R.MODE_KEY:
            elements.append((tag, name, mode))
            continue

        if name == R.DS_XML_KEY:
            # The whole Dynamic System curve lives in this one string.
            members = [canon.get(m) for m in R.DS_MEMBERS]
            value = (
                ";".join(str(int(v)) for v in members)
                if all(v is not None for v in members)
                else default
            )
            elements.append((tag, name, value))
            continue

        f = R.BY_XML.get(name)
        if f is not None and f.canon in canon:
            elements.append((tag, name, _xml_value(f=f, value=canon[f.canon])))
        else:
            elements.append((tag, name, default))

    return elements


def xml_to_str(elements: list[tuple[str, str, str]]) -> str:
    """Format xml elements as a preset document, matching the app's own layout."""
    lines = [_XML_HEADER, "<map>"]
    for tag, name, value in elements:
        if tag == "string":
            if value:
                lines.append(f'  <string name="{name}">{escape(data=value)}</string>')
            else:
                lines.append(f'  <string name="{name}"/>')
        else:
            lines.append(f'  <{tag} name="{name}" value="{escape(data=str(value))}"/>')
    lines.append("</map>")
    return "\n".join(lines) + "\n"
