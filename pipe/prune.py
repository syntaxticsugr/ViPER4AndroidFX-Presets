from pathlib import Path

from utils.release.search_in_xml import search_in_xml

_ROOT = Path(__file__).resolve().parent.parent

# Each preset targets one output mode, stored in parameter 32775:
# "1" = headphone/bluetooth/usb, "2" = speaker. The modes ship different default
# presets, so a preset is always compared against the default for its own mode.
MODE = "32775"
DEFAULT_PRESETS = {
    "1": _ROOT / "default_presets/xml/default_m1.xml",
    "2": _ROOT / "default_presets/xml/default_m2.xml",
}

# The effects whose parameters decide whether a preset does anything, as
# ``enable-flag id -> [parameter ids]``. An effect changes the sound only when its
# enable flag is on AND at least one of its parameters differs from the default
# preset; an effect switched on but left at default values - a flat EQ, a
# zero-gain Bass, a Convolver with no kernel - is inaudible. Ids come from
# default_presets/xml/m{1,2}_keys.txt.
#
# Some switches are intentionally left out of TUNED_EFFECTS because they can never
# represent custom tuning:
#  - parameterless toggles, with no value that could differ from the default:
#    Master Switch (36868), Speaker Optimization (65603), Tube Simulator (65583)
#  - converter rewrites to the default on every preset:
#    Playback Gain (65565) and the master limiter (65586-65588)
TUNED_EFFECTS = {
    "65610": [
        "65611",
        "65612",
        "65613",
        "65614",
        "65615",
        "65616",
        "65617",
        "65618",
        "65619",
        "65620",
        "65621",
        "65622",
        "65623",
        "65624",
        "65625",
        "65626",
    ],  # FET Compressor
    "65546": ["65547"],  # ViPER DDC (device file)
    "65548": ["65549;65550"],  # Spectrum Extension
    "65551": ["65552"],  # FIR Equalizer (band gains)
    "65538": ["65540;65541;65542", "65543"],  # Convolver (kernel, cross-channel)
    "65553": ["65554;65556", "65555"],  # Field Surround
    "65557": ["65558"],  # Differential Surround
    "65544": ["65545"],  # Headphone Surround +
    "65559": ["65560", "65561", "65562", "65563", "65564"],  # Reverberation
    "65569": ["65570;65571;65572", "65573"],  # Dynamic System
    "65574": ["65575", "65576", "65577"],  # ViPER Bass
    "65578": ["65579", "65580"],  # ViPER Clarity
    "65581": ["65582"],  # Auditory System Protection
    "65584": ["65585"],  # AnalogX
}

_TUNED_PARAMS = [param for params in TUNED_EFFECTS.values() for param in params]
_default_cache: dict[str, dict[str, str | None]] = {}


def _default_values(mode: str) -> dict[str, str | None]:
    """Return (and cache) the default preset's parameter values for ``mode``."""
    if mode not in _default_cache:
        path = DEFAULT_PRESETS.get(mode, DEFAULT_PRESETS["1"])
        _default_cache[mode] = search_in_xml(xml=path, keys=_TUNED_PARAMS)
    return _default_cache[mode]


def is_noop_preset(xml: Path) -> bool:
    """Return True if the preset leaves every effect at its default.

    Such a preset is the default config with nothing actually tuned, so it sounds
    identical to the default and is safe to drop. The preset "does something" as
    soon as one enabled effect in :data:`TUNED_EFFECTS` has a parameter that
    differs from its mode's default preset.
    """
    found = search_in_xml(
        xml=xml,
        keys=[MODE, *TUNED_EFFECTS, *_TUNED_PARAMS],
    )

    default = _default_values(found.get(MODE) or "1")
    for enable, params in TUNED_EFFECTS.items():
        if (found.get(enable) or "").lower() != "true":
            continue  # effect switched off
        if any(found.get(param) != default.get(param) for param in params):
            return False  # enabled and tuned away from the default

    return True


def prune_noop_presets(
    xml_dir: Path,
    json_v1_dir: Path,
    json_v2_dir: Path,
    report_dir: Path,
) -> list[str]:
    """Delete the no-op presets in ``xml_dir`` along with their JSON twins.

    Every ``*.xml`` that :func:`is_noop_preset` flags is removed, together with
    the same-named ``.json`` in ``json_v1_dir`` and ``json_v2_dir``, so no
    release variant can include it. The removed names are written to
    ``<report_dir>/pruned.txt`` (an empty file when nothing was pruned). Returns
    the sorted list of removed names.
    """
    print("Pruning Flagged Presets ...")

    pruned: list[str] = []
    for xml in sorted(xml_dir.glob("*.xml")):
        if not is_noop_preset(xml=xml):
            continue

        xml.unlink()
        for json_dir in (json_v1_dir, json_v2_dir):
            twin = json_dir / f"{xml.stem}.json"
            if twin.is_file():
                twin.unlink()
        pruned.append(xml.stem)

    print(f"Pruned {len(pruned)} flagged preset(s).")

    with open(file=report_dir / "pruned.txt", mode="w") as file:
        file.writelines(f"{stem}\n" for stem in pruned)

    return pruned
