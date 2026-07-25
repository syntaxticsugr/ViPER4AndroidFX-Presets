"""Drop no-op presets - ones that leave every effect at its default and so sound
identical to applying nothing.

Pruning is **per spoke**. Each converted format is judged on its own and its own
files are removed, with no cross-format coupling: a preset whose only tuning is a
json-only effect (multiband, dynamic EQ, ...) is a genuine no-op *as xml* - that
effect can't be expressed there - so its xml is dropped while its v1/v2 survive.
Because a file is parsed back into the canon before the check, and a narrower
format simply never carries the effects it lacks, one rule covers all three: xml
only ever "sees" xml-representable tuning, v1/v2 see everything.

The no-op rule matches the app's own notion of an inert preset: an effect changes
the sound only when it is switched on *and* at least one of its parameters differs
from the default. Two kinds of switch never count as tuning and are left out:

* the output stage - master limiter and playback gain - which the release flavour
  pins to defaults, so it can never differ;
* parameterless toggles (Tube Simulator, Speaker Optimization) and the master
  switch, which have no parameter that could differ from the default.

The last two fall out for free: a group with no non-``enable`` parameters can
never satisfy "a parameter differs", so it is skipped without being named.
"""

from pathlib import Path

from utils.convert import registry as R
from utils.convert.parse import canon_defaults, parse

# The output stage is normalised by the release flavour, so it never signals
# tuning; excluded explicitly rather than relying on the flavour having run.
_OUTPUT_STAGE_GROUPS = frozenset({"masterLimiter", "playbackGainControl"})


def _tuned_groups() -> dict[str, list[str]]:
    """Build ``{effect group: [its parameter canon fields]}`` from the registry.

    A group qualifies when it has an ``enable`` switch and at least one other
    parameter. Groups with only an ``enable`` (parameterless toggles) and the
    output stage are excluded, matching the app's inert-preset rule.
    """
    by_group: dict[str, list[R.Field]] = {}
    for f in R.FIELDS:
        if f.group:
            by_group.setdefault(f.group, []).append(f)

    tuned: dict[str, list[str]] = {}
    for group, fields in by_group.items():
        if group in _OUTPUT_STAGE_GROUPS:
            continue
        leaves = {f.leaf for f in fields}
        if "enable" not in leaves:
            continue
        params = [f.canon for f in fields if f.leaf != "enable"]
        if params:
            tuned[group] = params
    return tuned


_TUNED_GROUPS = _tuned_groups()
_DEFAULTS = canon_defaults()


def is_noop(canon: dict) -> bool:
    """True when ``canon`` leaves every effect at its default.

    An effect "does something" only when it is enabled and at least one of its
    parameters differs from the canonical default; if none do, the preset is a
    no-op.
    """
    for group, params in _TUNED_GROUPS.items():
        if not canon.get(f"{group}.enable"):
            continue
        if any(canon.get(param) != _DEFAULTS.get(param) for param in params):
            return False
    return True


def _prune_dir(directory: Path, suffix: str) -> list[str]:
    """Delete every no-op ``*suffix`` preset in ``directory``; return their stems."""
    pruned: list[str] = []
    for preset in sorted(directory.glob(f"*{suffix}")):
        try:
            canon, _mode = parse(
                text=preset.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
        except Exception as exc:
            print(f"  [prune] Could not read {preset.name}: {exc}")
            continue
        if is_noop(canon=canon):
            preset.unlink()
            pruned.append(preset.stem)
    return pruned


def prune_noop_presets(
    xml_dir: Path,
    json_v1_dir: Path,
    json_v2_dir: Path,
    report_dir: Path,
) -> dict[str, list[str]]:
    """Prune no-op presets from each converted format independently.

    Each of ``xml_dir``/``json_v1_dir``/``json_v2_dir`` is pruned against its own
    contents - the formats are not kept in lockstep, since a preset can be inert
    in one and meaningful in another. The removed stems are written per format to
    ``<report_dir>/pruned_{xml,v1,v2}.txt`` and returned as
    ``{"xml": [...], "v1": [...], "v2": [...]}``.
    """
    print("Pruning No-op Presets ...")

    pruned = {
        "xml": _prune_dir(directory=xml_dir, suffix=".xml"),
        "v1": _prune_dir(directory=json_v1_dir, suffix=".json"),
        "v2": _prune_dir(directory=json_v2_dir, suffix=".json"),
    }

    for spoke, stems in pruned.items():
        with open(file=report_dir / f"pruned_{spoke}.txt", mode="w") as report:
            report.writelines(f"{stem}\n" for stem in stems)

    return pruned
