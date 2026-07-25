"""Normalise a legacy preset xml into the canonical (2.7.2+) xml dialect.

This is deliberately a separate axis from the rest of the converter: it moves an
xml document *forward in version* without leaving the xml spoke, which is a
different job from moving a preset *between formats*. Running it as a pre-pass
means ``parse.parse_xml`` only ever sees canonical ids and scales, and the
registry never has to carry two generations of key names.

Older builds stored several parameters under different ids and on wider raw
scales; ``Converter.md`` ("Old XML -> New XML") is the source for both. A value
is only rescaled when it falls outside the canonical range - presets in the wild
are often already half-migrated, and that guard keeps an
already-canonical value from being converted a second time.
"""

from utils.convert.registry import (
    AGC_MAX_GAIN_STEPS,
    AGC_STRENGTH_STEPS,
    THRESHOLD_STEPS,
    VOLUME_STEPS,
)

#: Parameters that simply moved id. Values are unchanged by the move; any scale
#: change is handled by :data:`_RESCALES` under the *new* id.
RENAMES = {
    # Master Limiter / Playback Gain
    "65608": "65586",
    "65609": "65588",
    "65604": "65565",
    "65605": "65566",
    "65606": "65567",
    "65607": "65568",
    # FET Compressor
    "65627": "65610",
    "65628": "65611",
    "65629": "65612",
    "65630": "65613",
    "65631": "65614",
    "65632": "65615",
    "65633": "65616",
    "65634": "65617",
    "65635": "65618",
    "65636": "65619",
    "65637": "65620",
    "65638": "65621",
    "65639": "65622",
    "65640": "65623",
    "65641": "65624",
    "65642": "65625",
    "65643": "65626",
    # FIR Equalizer
    "65595": "65551",
    "65596": "65552",
    # Convolver
    "65589": "65538",
    "65591;65592;65593": "65540;65541;65542",
    "65594": "65543",
    # Reverberation
    "65597": "65559",
    "65598": "65560",
    "65599": "65561",
    "65600": "65562",
    "65601": "65563",
    "65602": "65564",
}


def _nearest(table: list[int], value: int) -> int:
    """Index of the closest entry in ``table`` - legacy values can be off-step."""
    return min(range(len(table)), key=lambda i: abs(table[i] - value))


#: ``new id -> (canonical max, old-raw -> canonical)``. The formula runs only
#: when a value exceeds the canonical max, which is what distinguishes a legacy
#: raw value from one that has already been migrated.
_RESCALES = {
    "65586": (21, lambda v: _nearest(table=VOLUME_STEPS, value=v)),
    "65587": (100, lambda v: (v + 100) // 2),
    "65588": (5, lambda v: _nearest(table=THRESHOLD_STEPS, value=v)),
    "65566": (2, lambda v: _nearest(table=AGC_STRENGTH_STEPS, value=v)),
    "65567": (5, lambda v: _nearest(table=THRESHOLD_STEPS, value=v)),
    "65568": (10, lambda v: _nearest(table=AGC_MAX_GAIN_STEPS, value=v)),
    "65554;65556": (8, lambda v: (v - 120) // 10),  # Field Surround widening
    "65555": (10, lambda v: (v - 100) // 10),  # Field Surround mid image
    "65558": (19, lambda v: (v // 100) - 1),  # Differential Surround delay
    "65560": (10, lambda v: v // 10),  # Reverb room size
    "65561": (10, lambda v: v // 10),  # Reverb room width
    "65573": (100, lambda v: (v - 100) // 20),  # Dynamic System strength
    "65576": (135, lambda v: v - 15),  # ViPER Bass cutoff
    "65577": (11, lambda v: (v - 50) // 50),  # ViPER Bass strength
    "65580": (9, lambda v: v // 50),  # ViPER Clarity strength
}


def migrate(entries: dict[str, tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Rewrite parsed xml ``{name: (tag, value)}`` into the canonical dialect.

    Applies the id renames first, then the scale corrections, so a rescale can be
    written against the canonical id regardless of which id the value arrived
    under. Unknown parameters are passed through untouched.
    """
    moved: dict[str, tuple[str, str]] = {}
    for name, entry in entries.items():
        # A canonical id already present wins over a legacy one being renamed
        # onto it, so a half-migrated preset keeps its newer value.
        new_name = RENAMES.get(name, name)
        if new_name in moved and name in RENAMES:
            continue
        moved[new_name] = entry

    for name, (limit, formula) in _RESCALES.items():
        entry = moved.get(name)
        if entry is None:
            continue
        tag, raw = entry
        try:
            value = int(str(raw).strip())
        except ValueError:
            continue
        if value > limit:
            moved[name] = (tag, str(formula(value)))

    return moved


def is_legacy(entries: dict[str, tuple[str, str]]) -> bool:
    """True when the document still carries any pre-2.7.2 parameter id."""
    return any(name in RENAMES for name in entries)
