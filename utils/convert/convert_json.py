"""Convert a 2.7.2+ ViPER4Android preset XML (the format produced by
``utils/convert/convert_xml.py`` / the ``default_presets/xml/default_m{1,2}.xml``
templates) into the JSON preset format used by the modern rewrite
``com.llsl.viper4android``.

Value scales were reconciled against the new app source:
  - most params share the same human scale (FET, reverb, diff-surround, ...)
  - ``bassGain``   = xml * 50 + 50   (legacy step 0..19 -> stored 50..1000)
  - ``clarityGain``= xml * 50        (legacy step 0..9  -> stored 0..450)
  - the Dynamic System device string ``xLow;xHigh;yLow;yHigh;sLow;sHigh`` is
    split into the ``ds*`` keys
  - master gate / channel pan / limiter / AGC values are kept at the baseline
    defaults (the XML converter always leaves these at ViPER defaults)
  - Spectrum Extension (VSE) strength uses the v1.5.0 release-note lookup
    (legacy step 0..10 -> 2200..8200 Hz, ``2200 + step*600``); the new
    independent exciter has no legacy equivalent and stays at its default.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Path to Default Presets
default_m1_json_file = Path("default_presets/json/default_m1.json")
default_m2_json_file = Path("default_presets/json/default_m2.json")

# Keys whose speaker variant is NOT "spk" + Capitalized(base).
_SPK_KEY_OVERRIDES = {"speakerOptEnabled": "speakerOptEnabled"}

# 2.7.2 XML param id -> base JSON key, for plain "copy the value" params.
_BOOL_MAP = {
    "36868": "masterEnabled",
    "65565": "agcEnabled",
    "65610": "fetEnabled",
    "65614": "fetAutoKnee",
    "65616": "fetAutoGain",
    "65618": "fetAutoAttack",
    "65620": "fetAutoRelease",
    "65626": "fetNoClip",
    "65546": "ddcEnabled",
    "65548": "vseEnabled",
    "65551": "eqEnabled",
    "65538": "convolverEnabled",
    "65553": "fieldSurroundEnabled",
    "65557": "diffSurroundEnabled",
    "65544": "vheEnabled",
    "65559": "reverbEnabled",
    "65569": "dynamicSystemEnabled",
    "65583": "tubeSimulatorEnabled",
    "65574": "bassEnabled",
    "65578": "clarityEnabled",
    "65581": "cureEnabled",
    "65584": "analogxEnabled",
    "65603": "speakerOptEnabled",
}

# Direct (same-scale) integer params.
_INT_MAP = {
    "65611": "fetThreshold",
    "65612": "fetRatio",
    "65613": "fetKnee",
    "65615": "fetGain",
    "65617": "fetAttack",
    "65619": "fetRelease",
    "65621": "fetKneeMulti",
    "65622": "fetMaxAttack",
    "65623": "fetMaxRelease",
    "65624": "fetCrest",
    "65625": "fetAdapt",
    "65543": "convolverCrossChannel",
    "65555": "fieldSurroundMidImage",  # 0-10
    "65554;65556": "fieldSurroundWidening",  # 0-8 (legacy "surround" coeffs)
    "65558": "diffSurroundDelay",  # 0-19
    "65545": "vheQuality",  # 0-4
    "65560": "reverbRoomSize",  # 0-10
    "65561": "reverbWidth",  # 0-10
    "65562": "reverbDampening",
    "65563": "reverbWet",
    "65564": "reverbDry",
    "65573": "dynamicSystemStrength",  # 0-100
    "65576": "bassFrequency",  # 0-135 (display = value+15 Hz)
    "65582": "cureStrength",
    "65585": "analogxMode",
}

# String params copied verbatim.
_STR_MAP = {
    "65552": "eqBands",
    "65547": "ddcDevice",
    "65540;65541;65542": "convolverKernel",
}

# String-encoded mode integers (legacy stores e.g. <string>0</string>).
_MODE_STR_MAP = {
    "65575": "bassMode",
    "65579": "clarityMode",
}


def to_spk_key(base_key: str) -> str:
    """Map a base (headphone) JSON key to its speaker-mode equivalent."""
    if base_key in _SPK_KEY_OVERRIDES:
        return _SPK_KEY_OVERRIDES[base_key]
    return "spk" + base_key[0].upper() + base_key[1:]


def load_default_state(is_spk: bool) -> dict[str, object]:
    """Load the baseline default preset (a fresh dict) for the given mode.

    Headphone -> ``default_m1_json_file`` (base keys); speaker ->
    ``default_m2_json_file`` (``spk*`` keys). A new dict is returned on every
    call so callers can mutate it freely.
    """
    path = default_m2_json_file if is_spk else default_m1_json_file
    with open(file=path, mode="r", encoding="utf-8") as fh:
        return json.load(fp=fh)


def parse_272_xml(xml_path: Path) -> dict[str, tuple[str, str]]:
    """Parse a 2.7.2 preset XML into ``{name: (tag, value)}``.

    For ``<string>`` elements the value is the element text (``""`` if empty).
    For ``<int>`` / ``<boolean>`` it is the ``value`` attribute.
    """
    root = ET.parse(source=xml_path).getroot()
    out: dict[str, tuple[str, str]] = {}
    for el in root:
        name = el.get(key="name")
        if name is None:
            continue
        if el.tag == "string":
            out[name] = ("string", el.text if el.text is not None else "")
        else:
            out[name] = (el.tag, el.get(key="value", default=""))
    return out


def _as_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    raw = raw.strip()
    try:
        return int(raw)
    except ValueError:
        # tolerate float-ish ("5.0") legacy values
        try:
            return int(float(raw))
        except ValueError:
            return None


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def convert_272_xml_to_json(
    xml_path: Path,
) -> tuple[dict[str, object], bool, list[str]]:
    """Convert a 2.7.2 preset XML to the modern app's JSON dict.

    Starts from the mode-appropriate baseline default preset
    (:func:`load_default_state`) and overlays the source XML's values, written in
    the baseline's own key space (base keys for headphone, ``spk*`` for speaker).

    Returns ``(json_obj, is_speaker, warnings)``.
    """
    entries = parse_272_xml(xml_path=xml_path)
    warnings: list[str] = []

    mode = entries.get("32775", ("int", "1"))[1].strip()
    is_spk = mode == "2"

    # Baseline defaults for this mode; overlays write into this same key space.
    state = load_default_state(is_spk=is_spk)

    def key(base_key: str) -> str:
        return to_spk_key(base_key=base_key) if is_spk else base_key

    def set_val(base_key: str, value: object) -> None:
        state[key(base_key=base_key)] = value

    def bool_val(xid: str) -> bool | None:
        v = entries.get(xid)
        return None if v is None else (v[1].strip().lower() == "true")

    def int_val(xid: str) -> int | None:
        v = entries.get(xid)
        return None if v is None else _as_int(raw=v[1])

    def str_val(xid: str) -> str | None:
        v = entries.get(xid)
        return None if v is None else v[1]

    # Booleans (enables).
    for xid, k in _BOOL_MAP.items():
        b = bool_val(xid=xid)
        if b is not None:
            set_val(base_key=k, value=b)

    # Same-scale integers.
    for xid, k in _INT_MAP.items():
        n = int_val(xid=xid)
        if n is not None:
            set_val(base_key=k, value=n)

    # Verbatim strings.
    for xid, k in _STR_MAP.items():
        s = str_val(xid=xid)
        if s is not None:
            set_val(base_key=k, value=s)

    # Mode integers stored as strings.
    for xid, k in _MODE_STR_MAP.items():
        s = str_val(xid=xid)
        if s is not None:
            n = _as_int(raw=s)
            if n is not None:
                set_val(base_key=k, value=n)

    # Rescaled gains. Per the app's v1.5.0 release-note lookup tables the legacy
    # step index maps linearly onto the new continuous (x*100) scale:
    #   Bass/Mono Gain : step 0..19 -> 0.5x..10.0x  (stored 50..1000)
    #   Clarity Gain   : step 0..9  -> 0.0x..4.5x   (stored 0..450)
    bg = int_val(xid="65577")
    if bg is not None:
        set_val(
            base_key="bassGain", value=_clamp(value=bg * 50 + 50, low=50, high=1000)
        )
    cg = int_val(xid="65580")
    if cg is not None:
        set_val(base_key="clarityGain", value=_clamp(value=cg * 50, low=0, high=450))

    # Spectrum Extension strength. v1.5.0 release note: legacy step 0..10 maps
    # linearly to 2200..8200 Hz (step n -> 2200 + n*600). The legacy value lives
    # in the composite "65549;65550" (one value drove both bark params). The new
    # exciter has no legacy equivalent and is left at its default.
    vse = int_val(xid="65549;65550")
    if vse is not None:
        set_val(
            base_key="vseStrength",
            value=_clamp(value=2200 + vse * 600, low=2200, high=8200),
        )

    # Dynamic System device curve: "xLow;xHigh;yLow;yHigh;sideLow;sideHigh".
    ds = str_val(xid="65570;65571;65572")
    if ds:
        parts = [p for p in ds.split(sep=";") if p != ""]
        if len(parts) >= 6:
            vals = [_as_int(raw=p) for p in parts[:6]]
            if all(v is not None for v in vals):
                ds_keys = (
                    "dsXLow",
                    "dsXHigh",
                    "dsYLow",
                    "dsYHigh",
                    "dsSideGainLow",
                    "dsSideGainHigh",
                )
                for ds_key, v in zip(ds_keys, vals):
                    set_val(base_key=ds_key, value=v)
                set_val(base_key="dynamicSystemDevice", value=0)
                set_val(base_key="dsPresetId", value=-1)
        elif parts:
            warnings.append(
                f"Dynamic System device '{ds}' has {len(parts)} fields "
                "(expected 6); left ds* at defaults."
            )

    # FIR EQ is always a 10-band curve in the legacy format.
    set_val(base_key="eqBandCount", value=10)

    # Companion-file effects: warn so the user ships the referenced files.
    if state.get(key(base_key="convolverEnabled")) and state.get(
        key(base_key="convolverKernel")
    ):
        warnings.append(
            f"Convolver references kernel '{state[key(base_key='convolverKernel')]}' "
            "- ship the matching .irs file in the app's Kernel folder."
        )
    if state.get(key(base_key="ddcEnabled")) and state.get(key(base_key="ddcDevice")):
        warnings.append(
            f"DDC references '{state[key(base_key='ddcDevice')]}' "
            "- ship the matching .vdc file in the app's DDC folder."
        )

    return state, is_spk, warnings


def write_json_for_xml(xml_path: Path, out_dir: Path, preset_name: str) -> Path:
    """Convert ``xml_path`` and write ``<preset_name>.json`` into ``out_dir``.

    Returns the written path. Prints any conversion warnings.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    obj, _is_spk, warnings = convert_272_xml_to_json(xml_path=xml_path)
    json_path = out_dir / f"{preset_name}.json"
    with open(file=json_path, mode="w", encoding="utf-8") as fh:
        json.dump(obj=obj, fp=fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return json_path


def convert_json_presets(input_dir: Path, output_dir: Path) -> Path:
    """Convert every 2.7.2+ preset XML in ``input_dir`` to a modern JSON preset.

    Writes a ``<stem>.json`` into ``output_dir`` for each ``<stem>.xml`` found in
    ``input_dir`` (non-recursive). Standalone JSON converter; see
    :func:`pipe.convert.convert_presets` for the XML + JSON orchestrator.

    Returns ``output_dir``.
    """
    print("Converting Presets to JSON ...")

    output_dir.mkdir(parents=True, exist_ok=True)
    for xml_file in sorted(input_dir.iterdir()):
        if xml_file.suffix.lower() != ".xml":
            continue
        try:
            write_json_for_xml(
                xml_path=xml_file, out_dir=output_dir, preset_name=xml_file.stem
            )
        except Exception as exc:
            print(f"  [json] Failed for {xml_file.name}: {exc}")

    return output_dir


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    convert_json_presets(
        input_dir=input_dir,
        output_dir=output_dir,
    )
