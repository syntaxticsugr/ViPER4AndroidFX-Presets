"""Detect which spoke a preset is written in - shared by the filter and converter.

One function both validates and classifies: it returns ``"xml"``/``"v1"``/``"v2"``
for a ViPER preset and ``None`` for anything else. The filter routes on it (into
per-format folders, skipping non-presets); the converter parses on it. Keeping it
in one place means "what format is this" has a single definition.
"""

import json

# Spoke -> the folder name that format uses throughout the pipeline
# (``filtered/presets/<dir>``, ``default_presets/<dir>``, release ``Preset/<dir>``).
FORMAT_DIRS = {"xml": "xml", "v1": "json_v1", "v2": "json_v2"}


def detect_format(text: str) -> str | None:
    """Return the preset's spoke (``"xml"``/``"v1"``/``"v2"``), or ``None``.

    XML counts as a ViPER preset when it carries the master-switch parameter; JSON
    is ``v2`` when it has the grouped schema's top-level key, ``v1`` when it has
    the flat schema's. Anything else - a stray settings file, unrelated JSON, a
    malformed document - returns ``None`` rather than raising, so callers can treat
    "not a preset" as an ordinary outcome.
    """
    if text.lstrip().startswith("<"):
        return "xml" if 'name="36868"' in text else None  # master switch

    try:
        obj = json.loads(s=text)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None

    if "schemaVersion" in obj or "masterEnable" in obj:
        return "v2"
    if "masterEnabled" in obj or "spkMasterEnabled" in obj:
        return "v1"
    return None
