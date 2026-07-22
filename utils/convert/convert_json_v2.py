"""Convert a v1 flat ViPER4Android preset (the ``com.llsl.viper4android`` JSON
produced by :func:`utils.convert.convert_json_v1.convert_json_v1_presets`) into
the v2 grouped preset the current app reads.

The v1 format is a single flat dict - ``masterEnabled``, ``fetThreshold``,
``eqBands`` (a ``";"``-joined string), one key per parameter, with speaker
presets living in a parallel ``spk*`` namespace.

The v2 format the app switched to is a ``schemaVersion: 2`` object with the
master switch at the top level and every effect nested under its own group
(``fetCompressor``, ``equalizer``, ...); list parameters are native JSON arrays,
not ``";"``-joined strings, and the headphone/speaker split is gone (v2 presets
are device-agnostic).

The group names, field names and value types below are transcribed from the
app's own effect definitions in
``app/src/main/java/com/llsl/viper4android/effect/EffectGroups.kt`` (the schema)
and ``EffectPrefs.kt`` (the serializer). Group order matches ``EFFECT_GROUPS`` so
our output lines up with what the app writes itself.

Defaults are not restated here: this converter loads
``default_presets/json_v2/default.json`` as its baseline and overlays the mapped
v1 values onto it (the same pattern the XML and v1 converters use with their own
templates), so every key is always written and any field the source omits keeps
the template's default.
"""

import json
from pathlib import Path

# The v2 baseline template - structure, defaults and key order.
default_v2_json_file = Path("default_presets/json_v2/default.json")

# Speaker presets reach us in the spk* namespace (see ``to_spk_key`` in
# convert_json_v1); "spkMasterEnabled" is the tell.
_SPK_MARKER = "spkMasterEnabled"

# The v1 -> v2 map, one section per v2 group, in EFFECT_GROUPS order.
# Each field is (v1_key, v2_key, kind):
#   kind: "bool" | "int" | "str" | "int_list" | "bool_list" | "double_list" | "nullable_long"
SCHEMA: list[tuple[str, list[tuple[str, str, str]]]] = [
    (
        "masterLimiter",
        [
            ("limiter", "threshold", "int"),
            ("outputVolume", "outputVolume", "int"),
            ("channelPan", "channelPan", "int"),
        ],
    ),
    (
        "playbackGainControl",
        [
            ("agcEnabled", "enable", "bool"),
            ("agcStrength", "strength", "int"),
            ("agcMaxGain", "maxGain", "int"),
            ("agcOutputThreshold", "outputThreshold", "int"),
        ],
    ),
    (
        "lufs",
        [
            ("lufsEnabled", "enable", "bool"),
            ("lufsTarget", "target", "int"),
            ("lufsMaxGain", "maxGain", "int"),
            ("lufsSpeed", "speed", "int"),
        ],
    ),
    (
        "fetCompressor",
        [
            ("fetEnabled", "enable", "bool"),
            ("fetThreshold", "threshold", "int"),
            ("fetRatio", "ratio", "int"),
            ("fetAutoKnee", "kneeAuto", "bool"),
            ("fetKnee", "knee", "int"),
            ("fetKneeMulti", "kneeMulti", "int"),
            ("fetAutoGain", "gainAuto", "bool"),
            ("fetGain", "gain", "int"),
            ("fetAutoAttack", "attackAuto", "bool"),
            ("fetAttack", "attack", "int"),
            ("fetMaxAttack", "maxAttack", "int"),
            ("fetAutoRelease", "releaseAuto", "bool"),
            ("fetRelease", "release", "int"),
            ("fetMaxRelease", "maxRelease", "int"),
            ("fetCrest", "crest", "int"),
            ("fetAdapt", "adapt", "int"),
            ("fetNoClip", "noClip", "bool"),
        ],
    ),
    (
        "multibandCompressor",
        [
            ("mbcEnabled", "enable", "bool"),
            ("mbcBandEnables", "bandEnables", "bool_list"),
            ("mbcCrossovers", "crossovers", "int_list"),
            ("mbcThresholds", "thresholds", "int_list"),
            ("mbcRatios", "ratios", "int_list"),
            ("mbcGains", "gains", "int_list"),
            ("mbcKnees", "knees", "int_list"),
            ("mbcKneeMultis", "kneeMultis", "int_list"),
            ("mbcAttacks", "attacks", "int_list"),
            ("mbcMaxAttacks", "maxAttacks", "int_list"),
            ("mbcReleases", "releases", "int_list"),
            ("mbcMaxReleases", "maxReleases", "int_list"),
            ("mbcCrests", "crests", "int_list"),
            ("mbcAdapts", "adapts", "int_list"),
            ("mbcAutoKnees", "kneeAutos", "bool_list"),
            ("mbcAutoGains", "gainAutos", "bool_list"),
            ("mbcAutoAttacks", "attackAutos", "bool_list"),
            ("mbcAutoReleases", "releaseAutos", "bool_list"),
            ("mbcNoClips", "noClips", "bool_list"),
        ],
    ),
    (
        "ddc",
        [
            ("ddcEnabled", "enable", "bool"),
            ("ddcDevice", "device", "str"),
        ],
    ),
    (
        "spectrumExtension",
        [
            ("vseEnabled", "enable", "bool"),
            ("vseStrength", "strength", "int"),
            ("vseExciter", "exciter", "int"),
        ],
    ),
    (
        "equalizer",
        [
            ("eqEnabled", "enable", "bool"),
            ("eqBandCount", "bandCount", "int"),
            ("eqBands", "bands", "double_list"),
            ("eqPresetId", "presetId", "nullable_long"),
        ],
    ),
    (
        "dynamicEq",
        [
            ("dynamicEqEnabled", "enable", "bool"),
            ("dynamicEqBandCount", "bandCount", "int"),
            ("dynamicEqFreqs", "freqs", "int_list"),
            ("dynamicEqQs", "qs", "int_list"),
            ("dynamicEqGains", "gains", "int_list"),
            ("dynamicEqThresholds", "thresholds", "int_list"),
            ("dynamicEqAttacks", "attacks", "int_list"),
            ("dynamicEqReleases", "releases", "int_list"),
            ("dynamicEqFilterTypes", "filterTypes", "int_list"),
        ],
    ),
    (
        "convolver",
        [
            ("convolverEnabled", "enable", "bool"),
            ("convolverKernel", "kernelFile", "str"),
            ("convolverCrossChannel", "crossChannel", "int"),
        ],
    ),
    (
        "fieldSurround",
        [
            ("fieldSurroundEnabled", "enable", "bool"),
            ("fieldSurroundWidening", "widening", "int"),
            ("fieldSurroundMidImage", "midImage", "int"),
            ("fieldSurroundDepth", "depth", "int"),
        ],
    ),
    (
        "diffSurround",
        [
            ("diffSurroundEnabled", "enable", "bool"),
            ("diffSurroundDelay", "delay", "int"),
            ("diffSurroundReverse", "reverse", "bool"),
            ("diffSurroundWetDryMix", "wetDryMix", "int"),
            ("diffSurroundLpCutoff", "lpCutoff", "int"),
        ],
    ),
    (
        "stereoImager",
        [
            ("stereoImgEnabled", "enable", "bool"),
            ("stereoImgLowWidth", "lowWidth", "int"),
            ("stereoImgMidWidth", "midWidth", "int"),
            ("stereoImgHighWidth", "highWidth", "int"),
            ("stereoImgLowCrossover", "lowCrossover", "int"),
            ("stereoImgHighCrossover", "highCrossover", "int"),
        ],
    ),
    (
        "headphoneSurround",
        [
            ("vheEnabled", "enable", "bool"),
            ("vheQuality", "quality", "int"),
        ],
    ),
    (
        "reverb",
        [
            ("reverbEnabled", "enable", "bool"),
            ("reverbRoomSize", "roomSize", "int"),
            ("reverbWidth", "width", "int"),
            ("reverbDampening", "damp", "int"),
            ("reverbWet", "wet", "int"),
            ("reverbDry", "dry", "int"),
        ],
    ),
    (
        "dynamicSystem",
        [
            ("dynamicSystemEnabled", "enable", "bool"),
            ("dsPresetId", "presetId", "nullable_long"),
            ("dynamicSystemDevice", "device", "int"),
            ("dynamicSystemStrength", "strength", "int"),
            ("dsXLow", "xLow", "int"),
            ("dsXHigh", "xHigh", "int"),
            ("dsYLow", "yLow", "int"),
            ("dsYHigh", "yHigh", "int"),
            ("dsSideGainLow", "sideGainLow", "int"),
            ("dsSideGainHigh", "sideGainHigh", "int"),
        ],
    ),
    (
        "psychoacousticBass",
        [
            ("psychoBassEnabled", "enable", "bool"),
            ("psychoBassCutoff", "cutoff", "int"),
            ("psychoBassIntensity", "intensity", "int"),
            ("psychoBassHarmonicOrder", "harmonicOrder", "int"),
            ("psychoBassOriginalLevel", "originalLevel", "int"),
        ],
    ),
    (
        "bass",
        [
            ("bassEnabled", "enable", "bool"),
            ("bassMode", "mode", "int"),
            ("bassFrequency", "frequency", "int"),
            ("bassGain", "gain", "int"),
            ("bassAntiPop", "antiPop", "bool"),
        ],
    ),
    (
        "bassMono",
        [
            ("bassMonoEnabled", "enable", "bool"),
            ("bassMonoMode", "mode", "int"),
            ("bassMonoFrequency", "frequency", "int"),
            ("bassMonoGain", "gain", "int"),
            ("bassMonoAntiPop", "antiPop", "bool"),
        ],
    ),
    (
        "clarity",
        [
            ("clarityEnabled", "enable", "bool"),
            ("clarityMode", "mode", "int"),
            ("clarityGain", "gain", "int"),
        ],
    ),
    (
        "cure",
        [
            ("cureEnabled", "enable", "bool"),
            # v1 stored a "strength"; v2's Cure exposes a crossfeed-preset
            # selector instead. The legacy value is carried into that slot to
            # match the app's own migration - a rough mapping, but Cure is
            # rarely tuned in the corpus.
            ("cureStrength", "crossfeedPreset", "int"),
        ],
    ),
    (
        "tubeSimulator",
        [
            ("tubeSimulatorEnabled", "enable", "bool"),
        ],
    ),
    (
        "analogX",
        [
            ("analogxEnabled", "enable", "bool"),
            ("analogxMode", "mode", "int"),
        ],
    ),
    (
        "speakerCorrection",
        [
            ("speakerOptEnabled", "enable", "bool"),
        ],
    ),
]


def _to_base_key(key: str) -> str:
    """Strip the speaker ``spk*`` prefix so both namespaces map the same way.

    ``spkBassGain -> bassGain``. ``speakerOptEnabled`` has no prefix in either
    mode and no base key starts with ``spk``, so this is safe to run on any key.
    """
    if key.startswith("spk") and len(key) > 3:
        return key[3].lower() + key[4:]
    return key


def _normalize(v1: dict[str, object]) -> dict[str, object]:
    """Return the preset in the base (headphone) key space.

    Speaker presets arrive spk-prefixed; rewrite them to base keys so one map
    covers both. Headphone presets pass through unchanged.
    """
    if _SPK_MARKER not in v1:
        return v1
    return {_to_base_key(key=k): v for k, v in v1.items()}


def _as_int(value: object) -> int:
    """Read a scalar as int, tolerating floats and float-ish strings ("5.0")."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).strip())
    except ValueError:
        return int(float(str(value).strip()))


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true")


def _parts(value: object) -> list[str]:
    """Split a ``";"``-joined list value into non-empty parts.

    Tolerates an already-split list, and drops the trailing empty field left by
    values like ``"0.0;0.0;"``.
    """
    if isinstance(value, list):
        return [str(p) for p in value]
    return [p for p in str(value).split(";") if p.strip() != ""]


def _coerce(kind: str, value: object) -> object:
    """Convert a v1 value into its v2 JSON representation."""
    if kind == "bool":
        return _as_bool(value=value)
    if kind == "int":
        return _as_int(value=value)
    if kind == "str":
        return str(value)
    if kind == "int_list":
        return [_as_int(value=p) for p in _parts(value=value)]
    if kind == "bool_list":
        return [_as_bool(value=p) for p in _parts(value=value)]
    if kind == "double_list":
        return [float(p) for p in _parts(value=value)]
    if kind == "nullable_long":
        n = _as_int(value=value)
        return None if n < 0 else n
    raise ValueError(f"unknown kind: {kind}")


def load_default_state() -> dict[str, object]:
    """Load a fresh copy of the v2 baseline template (structure + defaults).

    A new dict is returned on every call so callers can overlay onto it freely.
    """
    with open(file=default_v2_json_file, mode="r", encoding="utf-8") as fh:
        return json.load(fp=fh)


def convert_v1_to_v2(v1: dict[str, object]) -> dict[str, object]:
    """Convert a single v1 flat preset dict to the v2 grouped dict.

    Starts from the v2 template (:func:`load_default_state`) and overlays every
    mapped v1 value onto it. A field the source omits keeps the template's
    default, so the result is always a complete, well-formed v2 preset.
    """
    base = _normalize(v1=v1)
    out = load_default_state()

    if "masterEnabled" in base:
        out["masterEnable"] = _as_bool(value=base["masterEnabled"])

    for group_key, fields in SCHEMA:
        group = out.setdefault(group_key, {})
        for v1_key, v2_key, kind in fields:
            if v1_key in base:
                group[v2_key] = _coerce(kind=kind, value=base[v1_key])

    return out


def convert_json_v2_presets(input_dir: Path, output_dir: Path) -> Path:
    """Convert every v1 flat JSON preset in ``input_dir`` to a v2 grouped preset.

    Writes a ``<stem>.json`` into ``output_dir`` for each ``<stem>.json`` found
    in ``input_dir`` (non-recursive). Standalone JSON v2 converter; see
    :func:`pipe.convert.convert_presets` for the XML + JSON v1 + JSON v2
    orchestrator.

    Returns ``output_dir``.
    """
    print("Converting Presets to JSON v2 ...")

    output_dir.mkdir(parents=True, exist_ok=True)
    for json_file in sorted(input_dir.iterdir()):
        if json_file.suffix.lower() != ".json":
            continue
        try:
            with open(file=json_file, mode="r", encoding="utf-8") as fh:
                v1 = json.load(fp=fh)
            v2 = convert_v1_to_v2(v1=v1)
            out_path = output_dir / json_file.name
            with open(file=out_path, mode="w", encoding="utf-8") as fh:
                json.dump(obj=v2, fp=fh, indent=2, ensure_ascii=False)
                fh.write("\n")
        except Exception as exc:
            print(f"  [json_v2] Failed for {json_file.name}: {exc}")

    return output_dir


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    convert_json_v2_presets(
        input_dir=input_dir,
        output_dir=output_dir,
    )
