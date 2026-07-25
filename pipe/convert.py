"""Any-to-any preset conversion stage.

Reads presets in whatever spoke they arrive in - legacy or canonical xml, v1 flat
json, v2 grouped json - and writes all three formats for each one, via the
hub-and-spoke converter in ``utils/convert``.

Every output stem carries a complete xml + v1 + v2 triple. That matters because
:func:`pipe.prune.prune_noop_presets` walks the xml directory and deletes a
preset's json twins by stem, so the three directories have to stay aligned.

xml and v1 are device-specific, so a device-agnostic source (a v2 preset, or a
mode-less xml with no filename hint) fans out into a ``-headphone`` and a
``-speaker`` stem for those two formats. v2 itself is device-agnostic, so it is
written once per source under the plain stem - the three formats are pruned and
deduplicated independently downstream, so they need not share a stem.

Alongside the conversion this stage overlays the release *flavour*
(:func:`_enable_and_normalize`). The converter in ``utils/convert`` stays faithful
- it carries exactly what a preset holds - and this project's distribution choice
lives here, applied through the converter's ``transform`` seam.
"""

from pathlib import Path

from utils.convert.convert import convert
from utils.convert.parse import canon_defaults, detect_format, parse
from utils.create_directories import create_directories

#: Filename suffix used when one source fans out into a file per mode.
MODE_SUFFIX = {"1": "headphone", "2": "speaker"}

_SOURCE_SUFFIXES = (".xml", ".json")

# --- Release flavour -------------------------------------------------------
# The output stage: master limiter (output volume / channel pan / limiter
# threshold) and playback gain control. These normalise loudness rather than
# shape a preset's character, so a shared preset carrying someone's personal
# output-gain tweak would just impose it on everyone. The release pins them back
# to ViPER defaults no matter what the source held, and forces the master switch
# on so an applied preset audibly does something. Kept here, not in the
# converter, because it is this project's choice rather than a fact about presets.
_OUTPUT_STAGE = (
    "masterLimiter.threshold",
    "masterLimiter.outputVolume",
    "masterLimiter.channelPan",
    "playbackGainControl.enable",
    "playbackGainControl.strength",
    "playbackGainControl.maxGain",
    "playbackGainControl.outputThreshold",
)

# The canonical values to reset to, read once from the v2 template.
_DEFAULTS = canon_defaults()


def _enable_and_normalize(canon: dict) -> None:
    """Force the master switch on and reset the output stage to ViPER defaults.

    Mutates ``canon`` in place; passed as the ``transform`` to :func:`convert`.
    """
    canon["masterEnable"] = True
    for field in _OUTPUT_STAGE:
        canon[field] = _DEFAULTS[field]


# Device keywords that pin a mode-less xml preset to one mode from its filename.
# Corpus presets are frequently named for the device they came from (see
# pipe/filter.py), which is a dependable signal when the preset itself predates
# the mode parameter. Matched as substrings against the lowercased stem.
_SPEAKER_HINTS = ("speaker",)
_HEADPHONE_HINTS = ("headphone", "headset", "bluetooth", "usb")


def _mode_from_name(stem: str) -> str | None:
    """Guess a preset's mode from its filename, or ``None`` if the name is unclear.

    A name that points at only one device family decides the mode: a speaker hint
    alone -> mode 2, a headphone hint alone -> mode 1. A name carrying *both* (a
    "...Speakers" pack exported for "-bluetooth", say) is genuinely ambiguous, so
    it returns ``None`` and the caller fans out to both modes rather than letting
    hint order silently pick one - which would drop the other mode's tuning.
    """
    name = stem.lower()
    speaker = any(hint in name for hint in _SPEAKER_HINTS)
    headphone = any(hint in name for hint in _HEADPHONE_HINTS)
    if speaker and not headphone:
        return "2"
    if headphone and not speaker:
        return "1"
    return None


def mode_targets(fmt: str, mode: str | None, stem: str) -> list[tuple[str, str]]:
    """Resolve a source into the ``[(mode, output stem)]`` it should produce.

    A stated mode wins and keeps the original name. A mode-less xml falls back to
    a filename hint (still one file, original name) and, failing that, fans out
    to both modes under ``-headphone`` / ``-speaker`` stems. A v2 preset is
    device-agnostic by construction, so it always fans out to both and never
    consults the filename - a v2 named "speaker" still targets both devices.
    """
    if mode:
        return [(mode, stem)]

    if fmt == "xml":
        hinted = _mode_from_name(stem=stem)
        if hinted:
            return [(hinted, stem)]

    return [(m, f"{stem}-{suffix}") for m, suffix in MODE_SUFFIX.items()]


def _reserve_stem(
    base: str,
    suffixes: list[str],
    used_v2: set[str],
    used_dev: set[str],
) -> str:
    """Reserve a collision-free output stem for a source and return it.

    A source writes into two filename namespaces at once, and a clash in *either*
    must rename the whole source, so its xml/v1/v2 stay aligned under one stem:

    * ``json_v2/``            -> ``<stem>.json``                 (``used_v2``)
    * ``xml/`` & ``json_v1/`` -> ``<stem><suffix>.{xml,json}``   (``used_dev``)

    ``suffixes`` are the device-variant tails - ``[""]`` for a single-mode source,
    ``["-headphone", "-speaker"]`` when it fans out. Reserving the *variants* (not
    just the base) is what stops a mode-less ``Foo`` (-> ``Foo-headphone``) from
    clobbering a literal ``Foo-headphone``. Compared case-insensitively so names
    survive a copy onto a case-insensitive filesystem. Returns ``base`` unless a
    ``_2``/``_3``/... was needed to dodge an earlier source's output.

    These are collisions between *distinct* presets, so - unlike filter's
    re-download renames - the result is deliberately not fed to ``collisions`` in
    the release stage: both presets are meant to survive, not collapse onto one.
    """
    cand = base
    n = 1
    while cand.lower() in used_v2 or any(
        f"{cand}{suffix}".lower() in used_dev for suffix in suffixes
    ):
        n += 1
        cand = f"{base}_{n}"
    used_v2.add(cand.lower())
    used_dev.update(f"{cand}{suffix}".lower() for suffix in suffixes)
    return cand


def convert_presets(input_dir: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    """Convert every preset in ``input_dir`` into all three supported formats.

    Outputs live under a single ``<output_dir>/preset-converted`` container, in
    the ``xml/``, ``json_v1/`` and ``json_v2/`` subdirs.

    Returns ``(preset_xml_dir, preset_json_v1_dir, preset_json_v2_dir)``.
    """
    print("Converting Presets ...")

    preset_converted_dir = output_dir / "preset-converted"
    preset_xml_dir = preset_converted_dir / "xml"
    preset_json_v1_dir = preset_converted_dir / "json_v1"
    preset_json_v2_dir = preset_converted_dir / "json_v2"
    create_directories(
        directories=[
            preset_converted_dir,
            preset_xml_dir,
            preset_json_v1_dir,
            preset_json_v2_dir,
        ]
    )

    converted = 0
    # A source's three outputs share one stem; a clash - the same name in two
    # subfolders, the same stem across source formats, or a fan-out variant
    # meeting a literal "-headphone"/"-speaker" preset - takes a "_N" suffix
    # rather than overwriting. Two namespaces: v2 (the base stem) and the shared
    # xml+v1 device variants.
    used_v2: set[str] = set()
    used_dev: set[str] = set()
    # Walk recursively, so a flat folder of mixed presets and a tree split by
    # format (filter's ``presets/{xml,json_v1,json_v2}``) both just work.
    for source in sorted(input_dir.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in _SOURCE_SUFFIXES:
            continue

        try:
            text = source.read_text(encoding="utf-8", errors="replace")

            _canon, mode = parse(text=text)
            fmt = detect_format(text=text)

            # The release flavour is applied to every output: master switch on,
            # output stage pinned to defaults. The converter stays faithful; this
            # overlay is the pipeline's own choice.

            # Resolve the device targets, then claim a collision-free stem for the
            # whole source (v2 base + every device variant it will emit).
            targets = mode_targets(fmt=fmt, mode=mode, stem=source.stem)
            suffixes = [stem[len(source.stem) :] for _m, stem in targets]
            stem = _reserve_stem(
                base=source.stem,
                suffixes=suffixes,
                used_v2=used_v2,
                used_dev=used_dev,
            )

            # v2 is device-agnostic - one file per source, under the base stem.
            (preset_json_v2_dir / f"{stem}.json").write_text(
                data=convert(text=text, target="v2", transform=_enable_and_normalize)
                + "\n",
                encoding="utf-8",
            )

            # xml and v1 are device-specific - one file per resolved mode.
            for (target_mode, _orig_stem), suffix in zip(targets, suffixes):
                out_stem = f"{stem}{suffix}"
                (preset_xml_dir / f"{out_stem}.xml").write_text(
                    data=convert(
                        text=text,
                        target="xml",
                        mode=target_mode,
                        transform=_enable_and_normalize,
                    ),
                    encoding="utf-8",
                )
                (preset_json_v1_dir / f"{out_stem}.json").write_text(
                    data=convert(
                        text=text,
                        target="v1",
                        mode=target_mode,
                        transform=_enable_and_normalize,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                converted += 1

        except Exception as exc:
            print(f"  [convert] Failed for {source.name}: {exc}")

    print(f"Converted {converted} preset(s).")

    return preset_xml_dir, preset_json_v1_dir, preset_json_v2_dir


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    convert_presets(
        input_dir=input_dir,
        output_dir=output_dir,
    )
