"""Canonical field registry for the ViPER4Android preset converter.

This is the hub of the hub-and-spoke converter: every cross-format mapping and
every value formula lives in :data:`FIELDS` below, so ``parse.py`` and
``serialize.py`` stay generic and carry no per-field knowledge.

The canon is the **v2 value space** - real-world values exactly as the grouped v2
JSON stores them (dB, Hz, native lists, ``None`` for a null preset id) - keyed by
the dotted v2 path, e.g. ``"fetCompressor.threshold"``. v1 and v2 already speak
that same value space, so all the scaling arithmetic is confined to the single
``xml <-> canon`` edge; the JSON spokes differ only in *encoding* (flat vs
grouped keys, ``";"``-joined strings vs native arrays, ``-1`` vs ``null``), which
:data:`Field.kind` describes on its own.

Two sources of truth back this table:

* ``Converter.md`` - the xml <-> json formulas. Its "In Range?" column is
  informational only: the audio engine accepts values the UI sliders cannot
  reach, so nothing here clamps.
* ``default_presets/`` - the defaults, and which keys exist for each
  (spoke, mode). Defaults are deliberately *not* restated here; a serializer
  starts from the matching template and overlays, which keeps one source of
  truth and makes per-mode feature availability fall out for free.
"""

from dataclasses import dataclass
from dataclasses import field as _dc_field

# ---------------------------------------------------------------------------
# Codecs: the xml <-> canon value transforms.
#
# Every codec is bidirectional - ``decode`` reads an xml value into the canon,
# ``encode`` writes it back. Splitting the two directions matters because the
# reverse of an index lookup is a search, not a formula.
# ---------------------------------------------------------------------------


class Codec:
    """A reversible xml <-> canon value transform."""

    #: True when ``encode`` cannot always round-trip (the canon value is snapped
    #: onto a coarser grid). Callers may surface this; nothing here clamps.
    lossy = False

    def decode(self, raw):
        """xml value -> canon value."""
        raise NotImplementedError

    def encode(self, val):
        """canon value -> xml value."""
        raise NotImplementedError


class Ident(Codec):
    """Value is stored identically on both sides."""

    def decode(self, raw):
        return raw

    def encode(self, val):
        return val


class Lin(Codec):
    """Affine scale: ``canon = raw * mul + add``.

    Covers every arithmetic row in Converter.md - channel pan (``2v - 100``),
    the FET dB conversions (``-0.6v`` / ``0.6v``), spectrum extension
    (``2200 + 60v`` Hz), reverb damp (``v / 10``), bass gain (``50v + 50``) and
    friends. Inverts analytically, so it round-trips exactly.
    """

    def __init__(self, mul: float, add: float = 0) -> None:
        self.mul = mul
        self.add = add

    def decode(self, raw):
        return raw * self.mul + self.add

    def encode(self, val):
        return (val - self.add) / self.mul


class IdxList(Codec):
    """Quantised pick: xml stores an index into ``table``, the canon the value.

    The forward direction is a plain lookup. The reverse has no formula - a canon
    value that isn't in the table is snapped to the nearest entry, which is why
    this is the one codec that can lose information. Snapping (rather than
    rejecting) keeps a v2 preset with an arbitrary output volume convertible to
    xml at all.
    """

    lossy = True

    def __init__(self, table: list[int]) -> None:
        self.table = table

    def decode(self, raw):
        index = int(raw)
        # Out-of-table indices are left alone rather than raising: a malformed
        # preset should degrade to a readable value, not kill the whole run.
        if 0 <= index < len(self.table):
            return self.table[index]
        return raw

    def encode(self, val):
        return min(
            range(len(self.table)),
            key=lambda i: abs(self.table[i] - val),
        )


# ---------------------------------------------------------------------------
# Field table
# ---------------------------------------------------------------------------

#: Value kinds. These drive the JSON encodings on their own:
#: v2 writes the native form, v1 writes ``";"``-joined strings for the lists and
#: ``-1`` for a null ``nullable_long``.
_LIST_KINDS = ("int_list", "bool_list", "double_list")


@dataclass(frozen=True)
class Field:
    """One canonical field and how each spoke stores it.

    ``canon`` doubles as the v2 path, since the canon *is* the v2 value space.
    A ``None`` spoke key means the format simply has no such parameter - that
    presence matrix is what implements the lossy-projection rule (json-only
    effects vanish on the way to xml; xml sources leave them at canon defaults).
    """

    canon: str
    kind: str
    v1: str | None
    xml: str | None = None
    codec: Codec = _dc_field(default_factory=Ident)
    #: Override the xml element tag when it isn't implied by ``kind`` - bass and
    #: clarity mode are ints the app persists as ``<string>0</string>``.
    tag: str | None = None
    #: Emit a trailing separator in the ``";"``-joined encodings (the EQ band
    #: string carries one in both xml and v1; the other lists do not).
    trailing: bool = False
    #: Marks values needing bespoke handling in ``parse``/``serialize``.
    special: str | None = None

    @property
    def group(self) -> str:
        """v2 group name, or ``""`` for a top-level field."""
        return self.canon.rsplit(sep=".", maxsplit=1)[0] if "." in self.canon else ""

    @property
    def leaf(self) -> str:
        """v2 field name within its group."""
        return self.canon.rsplit(sep=".", maxsplit=1)[-1]

    @property
    def xml_tag(self) -> str:
        """The xml element tag this field is persisted as."""
        if self.tag:
            return self.tag
        if self.kind == "bool":
            return "boolean"
        if self.kind == "str":
            return "string"
        return "int"


# The lookup tables Converter.md indexes into. Public because the legacy xml
# migration in ``legacy.py`` normalises onto these same steps.
VOLUME_STEPS = [
    1,
    5,
    10,
    20,
    30,
    40,
    50,
    60,
    70,
    80,
    90,
    100,
    110,
    120,
    130,
    140,
    150,
    160,
    170,
    180,
    190,
    200,
]
THRESHOLD_STEPS = [30, 50, 70, 80, 90, 100]
AGC_STRENGTH_STEPS = [50, 100, 300]
AGC_MAX_GAIN_STEPS = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 3000]

#: The registry. One row per canonical field, in v2 group order so the emitted
#: v2 JSON lines up with what the app writes itself.
FIELDS: list[Field] = [
    Field(canon="masterEnable", kind="bool", v1="masterEnabled", xml="36868"),
    # Master Limiter. Carried faithfully rather than pinned to defaults: these
    # have documented formulas, so an any-to-any conversion should preserve them.
    Field(
        canon="masterLimiter.threshold",
        kind="int",
        v1="limiter",
        xml="65588",
        codec=IdxList(table=THRESHOLD_STEPS),
    ),
    Field(
        canon="masterLimiter.outputVolume",
        kind="int",
        v1="outputVolume",
        xml="65586",
        codec=IdxList(table=VOLUME_STEPS),
    ),
    Field(
        canon="masterLimiter.channelPan",
        kind="int",
        v1="channelPan",
        xml="65587",
        codec=Lin(mul=2, add=-100),
    ),
    # Playback Gain Control (the legacy "AGC").
    Field(
        canon="playbackGainControl.enable",
        kind="bool",
        v1="agcEnabled",
        xml="65565",
    ),
    Field(
        canon="playbackGainControl.strength",
        kind="int",
        v1="agcStrength",
        xml="65566",
        codec=IdxList(table=AGC_STRENGTH_STEPS),
    ),
    Field(
        canon="playbackGainControl.maxGain",
        kind="int",
        v1="agcMaxGain",
        xml="65568",
        codec=IdxList(table=AGC_MAX_GAIN_STEPS),
    ),
    Field(
        canon="playbackGainControl.outputThreshold",
        kind="int",
        v1="agcOutputThreshold",
        xml="65567",
        codec=IdxList(table=THRESHOLD_STEPS),
    ),
    # LUFS - json only, no legacy equivalent.
    Field(canon="lufs.enable", kind="bool", v1="lufsEnabled"),
    Field(canon="lufs.target", kind="int", v1="lufsTarget"),
    Field(canon="lufs.maxGain", kind="int", v1="lufsMaxGain"),
    Field(canon="lufs.speed", kind="int", v1="lufsSpeed"),
    # FET Compressor. threshold/knee/gain are dB in json but raw 0-100 in xml.
    Field(canon="fetCompressor.enable", kind="bool", v1="fetEnabled", xml="65610"),
    Field(
        canon="fetCompressor.threshold",
        kind="int",
        v1="fetThreshold",
        xml="65611",
        codec=Lin(mul=-0.6),
    ),
    Field(canon="fetCompressor.ratio", kind="int", v1="fetRatio", xml="65612"),
    Field(canon="fetCompressor.kneeAuto", kind="bool", v1="fetAutoKnee", xml="65614"),
    Field(
        canon="fetCompressor.knee",
        kind="int",
        v1="fetKnee",
        xml="65613",
        codec=Lin(mul=0.6),
    ),
    Field(canon="fetCompressor.kneeMulti", kind="int", v1="fetKneeMulti", xml="65621"),
    Field(canon="fetCompressor.gainAuto", kind="bool", v1="fetAutoGain", xml="65616"),
    Field(
        canon="fetCompressor.gain",
        kind="int",
        v1="fetGain",
        xml="65615",
        codec=Lin(mul=0.6),
    ),
    Field(
        canon="fetCompressor.attackAuto",
        kind="bool",
        v1="fetAutoAttack",
        xml="65618",
    ),
    Field(canon="fetCompressor.attack", kind="int", v1="fetAttack", xml="65617"),
    Field(canon="fetCompressor.maxAttack", kind="int", v1="fetMaxAttack", xml="65622"),
    Field(
        canon="fetCompressor.releaseAuto",
        kind="bool",
        v1="fetAutoRelease",
        xml="65620",
    ),
    Field(canon="fetCompressor.release", kind="int", v1="fetRelease", xml="65619"),
    Field(
        canon="fetCompressor.maxRelease",
        kind="int",
        v1="fetMaxRelease",
        xml="65623",
    ),
    Field(canon="fetCompressor.crest", kind="int", v1="fetCrest", xml="65624"),
    Field(canon="fetCompressor.adapt", kind="int", v1="fetAdapt", xml="65625"),
    Field(canon="fetCompressor.noClip", kind="bool", v1="fetNoClip", xml="65626"),
    # Multiband Compressor - json only. Gains cross v1 <-> v2 unchanged; the
    # templates disagree on the *default* (v1 24, v2 0) but that only shows up in
    # the disabled default preset, so both are left as they are.
    Field(canon="multibandCompressor.enable", kind="bool", v1="mbcEnabled"),
    Field(
        canon="multibandCompressor.bandEnables",
        kind="bool_list",
        v1="mbcBandEnables",
    ),
    Field(canon="multibandCompressor.crossovers", kind="int_list", v1="mbcCrossovers"),
    Field(canon="multibandCompressor.thresholds", kind="int_list", v1="mbcThresholds"),
    Field(canon="multibandCompressor.ratios", kind="int_list", v1="mbcRatios"),
    Field(canon="multibandCompressor.gains", kind="int_list", v1="mbcGains"),
    Field(canon="multibandCompressor.knees", kind="int_list", v1="mbcKnees"),
    Field(canon="multibandCompressor.kneeMultis", kind="int_list", v1="mbcKneeMultis"),
    Field(canon="multibandCompressor.attacks", kind="int_list", v1="mbcAttacks"),
    Field(canon="multibandCompressor.maxAttacks", kind="int_list", v1="mbcMaxAttacks"),
    Field(canon="multibandCompressor.releases", kind="int_list", v1="mbcReleases"),
    Field(
        canon="multibandCompressor.maxReleases",
        kind="int_list",
        v1="mbcMaxReleases",
    ),
    Field(canon="multibandCompressor.crests", kind="int_list", v1="mbcCrests"),
    Field(canon="multibandCompressor.adapts", kind="int_list", v1="mbcAdapts"),
    Field(canon="multibandCompressor.kneeAutos", kind="bool_list", v1="mbcAutoKnees"),
    Field(canon="multibandCompressor.gainAutos", kind="bool_list", v1="mbcAutoGains"),
    Field(
        canon="multibandCompressor.attackAutos",
        kind="bool_list",
        v1="mbcAutoAttacks",
    ),
    Field(
        canon="multibandCompressor.releaseAutos",
        kind="bool_list",
        v1="mbcAutoReleases",
    ),
    Field(canon="multibandCompressor.noClips", kind="bool_list", v1="mbcNoClips"),
    # ViPER DDC.
    Field(canon="ddc.enable", kind="bool", v1="ddcEnabled", xml="65546"),
    Field(canon="ddc.device", kind="str", v1="ddcDevice", xml="65547"),
    # Spectrum Extension. One xml value drove both bark params, hence the
    # semicolon-joined key name; the exciter is json only.
    Field(canon="spectrumExtension.enable", kind="bool", v1="vseEnabled", xml="65548"),
    Field(
        canon="spectrumExtension.strength",
        kind="int",
        v1="vseStrength",
        xml="65549;65550",
        codec=Lin(mul=60, add=2200),
    ),
    Field(canon="spectrumExtension.exciter", kind="int", v1="vseExciter"),
    # FIR Equalizer. The band string carries a trailing ";" in xml and in v1;
    # the legacy format is always a 10-band curve, so bandCount has no xml key.
    Field(canon="equalizer.enable", kind="bool", v1="eqEnabled", xml="65551"),
    Field(canon="equalizer.bandCount", kind="int", v1="eqBandCount"),
    Field(
        canon="equalizer.bands",
        kind="double_list",
        v1="eqBands",
        xml="65552",
        tag="string",
        trailing=True,
    ),
    Field(canon="equalizer.presetId", kind="nullable_long", v1="eqPresetId"),
    # Dynamic EQ - json only.
    Field(canon="dynamicEq.enable", kind="bool", v1="dynamicEqEnabled"),
    Field(canon="dynamicEq.bandCount", kind="int", v1="dynamicEqBandCount"),
    Field(canon="dynamicEq.freqs", kind="int_list", v1="dynamicEqFreqs"),
    Field(canon="dynamicEq.qs", kind="int_list", v1="dynamicEqQs"),
    Field(canon="dynamicEq.gains", kind="int_list", v1="dynamicEqGains"),
    Field(canon="dynamicEq.thresholds", kind="int_list", v1="dynamicEqThresholds"),
    Field(canon="dynamicEq.attacks", kind="int_list", v1="dynamicEqAttacks"),
    Field(canon="dynamicEq.releases", kind="int_list", v1="dynamicEqReleases"),
    Field(canon="dynamicEq.filterTypes", kind="int_list", v1="dynamicEqFilterTypes"),
    # Convolver. Kernel names need the legacy "&" corruption and the placeholder
    # strings cleaned out on the way in - see ``parse.clean_kernel_name``.
    Field(canon="convolver.enable", kind="bool", v1="convolverEnabled", xml="65538"),
    Field(
        canon="convolver.kernelFile",
        kind="str",
        v1="convolverKernel",
        xml="65540;65541;65542",
        special="kernel",
    ),
    Field(
        canon="convolver.crossChannel",
        kind="int",
        v1="convolverCrossChannel",
        xml="65543",
    ),
    # Field Surround.
    Field(
        canon="fieldSurround.enable",
        kind="bool",
        v1="fieldSurroundEnabled",
        xml="65553",
    ),
    Field(
        canon="fieldSurround.widening",
        kind="int",
        v1="fieldSurroundWidening",
        xml="65554;65556",
    ),
    Field(
        canon="fieldSurround.midImage",
        kind="int",
        v1="fieldSurroundMidImage",
        xml="65555",
    ),
    Field(canon="fieldSurround.depth", kind="int", v1="fieldSurroundDepth"),
    # Differential Surround.
    Field(
        canon="diffSurround.enable",
        kind="bool",
        v1="diffSurroundEnabled",
        xml="65557",
    ),
    Field(
        canon="diffSurround.delay",
        kind="int",
        v1="diffSurroundDelay",
        xml="65558",
        codec=Lin(mul=1, add=1),
    ),
    Field(canon="diffSurround.reverse", kind="bool", v1="diffSurroundReverse"),
    Field(canon="diffSurround.wetDryMix", kind="int", v1="diffSurroundWetDryMix"),
    Field(canon="diffSurround.lpCutoff", kind="int", v1="diffSurroundLpCutoff"),
    # Stereo Imager - json only.
    Field(canon="stereoImager.enable", kind="bool", v1="stereoImgEnabled"),
    Field(canon="stereoImager.lowWidth", kind="int", v1="stereoImgLowWidth"),
    Field(canon="stereoImager.midWidth", kind="int", v1="stereoImgMidWidth"),
    Field(canon="stereoImager.highWidth", kind="int", v1="stereoImgHighWidth"),
    Field(canon="stereoImager.lowCrossover", kind="int", v1="stereoImgLowCrossover"),
    Field(canon="stereoImager.highCrossover", kind="int", v1="stereoImgHighCrossover"),
    # Headphone Surround +.
    Field(canon="headphoneSurround.enable", kind="bool", v1="vheEnabled", xml="65544"),
    Field(canon="headphoneSurround.quality", kind="int", v1="vheQuality", xml="65545"),
    # Reverberation. Damp is the only rescaled member (xml 0-100 -> json 0-10).
    Field(canon="reverb.enable", kind="bool", v1="reverbEnabled", xml="65559"),
    Field(canon="reverb.roomSize", kind="int", v1="reverbRoomSize", xml="65560"),
    Field(canon="reverb.width", kind="int", v1="reverbWidth", xml="65561"),
    Field(
        canon="reverb.damp",
        kind="int",
        v1="reverbDampening",
        xml="65562",
        codec=Lin(mul=0.1),
    ),
    Field(canon="reverb.wet", kind="int", v1="reverbWet", xml="65563"),
    Field(canon="reverb.dry", kind="int", v1="reverbDry", xml="65564"),
    # Dynamic System. The six curve members share one xml string - see
    # :data:`DS_XML_KEY` - so they carry no xml key of their own.
    Field(
        canon="dynamicSystem.enable",
        kind="bool",
        v1="dynamicSystemEnabled",
        xml="65569",
    ),
    Field(canon="dynamicSystem.presetId", kind="nullable_long", v1="dsPresetId"),
    Field(canon="dynamicSystem.device", kind="int", v1="dynamicSystemDevice"),
    Field(
        canon="dynamicSystem.strength",
        kind="int",
        v1="dynamicSystemStrength",
        xml="65573",
    ),
    Field(canon="dynamicSystem.xLow", kind="int", v1="dsXLow"),
    Field(canon="dynamicSystem.xHigh", kind="int", v1="dsXHigh"),
    Field(canon="dynamicSystem.yLow", kind="int", v1="dsYLow"),
    Field(canon="dynamicSystem.yHigh", kind="int", v1="dsYHigh"),
    Field(canon="dynamicSystem.sideGainLow", kind="int", v1="dsSideGainLow"),
    Field(canon="dynamicSystem.sideGainHigh", kind="int", v1="dsSideGainHigh"),
    # Psychoacoustic Bass - json only.
    Field(canon="psychoacousticBass.enable", kind="bool", v1="psychoBassEnabled"),
    Field(canon="psychoacousticBass.cutoff", kind="int", v1="psychoBassCutoff"),
    Field(canon="psychoacousticBass.intensity", kind="int", v1="psychoBassIntensity"),
    Field(
        canon="psychoacousticBass.harmonicOrder",
        kind="int",
        v1="psychoBassHarmonicOrder",
    ),
    Field(
        canon="psychoacousticBass.originalLevel",
        kind="int",
        v1="psychoBassOriginalLevel",
    ),
    # ViPER Bass.
    Field(canon="bass.enable", kind="bool", v1="bassEnabled", xml="65574"),
    Field(canon="bass.mode", kind="int", v1="bassMode", xml="65575", tag="string"),
    Field(canon="bass.frequency", kind="int", v1="bassFrequency", xml="65576"),
    Field(
        canon="bass.gain",
        kind="int",
        v1="bassGain",
        xml="65577",
        codec=Lin(mul=50, add=50),
    ),
    Field(canon="bass.antiPop", kind="bool", v1="bassAntiPop"),
    # Bass Mono - json only.
    Field(canon="bassMono.enable", kind="bool", v1="bassMonoEnabled"),
    Field(canon="bassMono.mode", kind="int", v1="bassMonoMode"),
    Field(canon="bassMono.frequency", kind="int", v1="bassMonoFrequency"),
    Field(canon="bassMono.gain", kind="int", v1="bassMonoGain"),
    Field(canon="bassMono.antiPop", kind="bool", v1="bassMonoAntiPop"),
    # ViPER Clarity.
    Field(canon="clarity.enable", kind="bool", v1="clarityEnabled", xml="65578"),
    Field(
        canon="clarity.mode",
        kind="int",
        v1="clarityMode",
        xml="65579",
        tag="string",
    ),
    Field(
        canon="clarity.gain",
        kind="int",
        v1="clarityGain",
        xml="65580",
        codec=Lin(mul=50),
    ),
    # Auditory System Protection. v1 kept a "strength"; v2 reuses the slot for a
    # crossfeed preset selector, matching the app's own migration.
    Field(canon="cure.enable", kind="bool", v1="cureEnabled", xml="65581"),
    Field(canon="cure.crossfeedPreset", kind="int", v1="cureStrength", xml="65582"),
    Field(
        canon="tubeSimulator.enable",
        kind="bool",
        v1="tubeSimulatorEnabled",
        xml="65583",
    ),
    Field(canon="analogX.enable", kind="bool", v1="analogxEnabled", xml="65584"),
    Field(canon="analogX.mode", kind="int", v1="analogxMode", xml="65585"),
    Field(
        canon="speakerCorrection.enable",
        kind="bool",
        v1="speakerOptEnabled",
        xml="65603",
    ),
]


# ---------------------------------------------------------------------------
# Spoke-specific constants
# ---------------------------------------------------------------------------

#: The xml parameter holding the output mode: "1" headphone/bluetooth/usb,
#: "2" speaker. v1 encodes the same split as a key prefix, v2 not at all.
MODE_KEY = "32775"

#: Dynamic System stores its whole curve in one string, as
#: ``xLow;xHigh;yLow;yHigh;sideGainLow;sideGainHigh``. It is the only place where
#: a single xml key feeds several canon fields, so it is handled explicitly.
DS_XML_KEY = "65570;65571;65572"
DS_MEMBERS = (
    "dynamicSystem.xLow",
    "dynamicSystem.xHigh",
    "dynamicSystem.yLow",
    "dynamicSystem.yHigh",
    "dynamicSystem.sideGainLow",
    "dynamicSystem.sideGainHigh",
)

#: The one v1 key that is *not* re-prefixed in the speaker namespace.
SPK_EXEMPT = frozenset({"speakerOptEnabled"})


def to_spk_key(base_key: str) -> str:
    """Map a base (headphone) v1 key to its speaker-namespace equivalent.

    ``bassGain -> spkBassGain``. Speaker Optimization is the sole exception and
    keeps its name in both modes.
    """
    if base_key in SPK_EXEMPT:
        return base_key
    return "spk" + base_key[0].upper() + base_key[1:]


def to_base_key(key: str) -> str:
    """Strip the speaker ``spk`` prefix so both v1 namespaces map identically.

    ``spkBassGain -> bassGain``. Safe on any key: no base key starts with
    ``spk``, and the exempt key has no prefix to remove.
    """
    if key.startswith("spk") and len(key) > 3 and key not in SPK_EXEMPT:
        return key[3].lower() + key[4:]
    return key


# ---------------------------------------------------------------------------
# Derived lookups
# ---------------------------------------------------------------------------

BY_CANON: dict[str, Field] = {f.canon: f for f in FIELDS}
BY_V1: dict[str, Field] = {f.v1: f for f in FIELDS if f.v1}
BY_XML: dict[str, Field] = {f.xml: f for f in FIELDS if f.xml}


#: Canon fields grouped by their v2 group, preserving table order.
def groups() -> dict[str, list[Field]]:
    """Return ``{v2 group name: [fields]}`` in registry order (``""`` = top level)."""
    out: dict[str, list[Field]] = {}
    for f in FIELDS:
        out.setdefault(f.group, []).append(f)
    return out


def is_list_kind(kind: str) -> bool:
    """True when the kind is a list that v1 stores as a ``";"``-joined string."""
    return kind in _LIST_KINDS
