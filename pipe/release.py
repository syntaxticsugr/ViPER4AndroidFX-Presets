import shutil
from dataclasses import dataclass
from pathlib import Path

from utils.create_directories import create_directories
from utils.release.check_duplicates import check_duplicates
from utils.release.list_missings import list_missings
from utils.release.search_in_xml import search_in_xml

# Preset files whose names contain any of these keywords are considered
# original and selected from a group of duplicates.
whitelist = [
    "Bee",
    "Devarim",
    "Deiwid63",
    "Inner_Fidelity",
    "J144df",
    "Joe_Meek",
    "Joemeek",
    "Percocet",
    "Roi007leaf",
    "Stormviper",
    "Smeejaytee",
    "V4ARISE",
    "Japanese",
    "Joe0Bloggs",
]


@dataclass
class ReleaseFiles:
    """The on-disk file structure for one release variant."""

    base_dir: Path
    kernel_dir: Path
    ddc_dir: Path
    preset_dir: Path

    @classmethod
    def create(cls, base_path: Path, variant_name: str) -> "ReleaseFiles":
        base_dir = base_path / variant_name
        kernel_dir = base_dir / "Kernel"
        ddc_dir = base_dir / "DDC"
        preset_dir = base_dir / "Preset"

        create_directories(directories=[base_dir, kernel_dir, ddc_dir, preset_dir])
        return cls(
            base_dir=base_dir,
            kernel_dir=kernel_dir,
            ddc_dir=ddc_dir,
            preset_dir=preset_dir,
        )


@dataclass
class PresetFormat:
    """A preset format to materialise a release in."""

    name: str  # release sub-folder, e.g. "XML" / "JSON"
    src_dir: Path  # where the converted preset files live
    ext: str  # preset file extension, e.g. ".xml" / ".json"


@dataclass
class Selection:
    """Format-independent set of names that make up a release variant.

    Holds bare file stems (no extension), so the same selection can be
    materialised as XML or JSON. Kernels/DDCs are companion ``.irs``/``.vdc``
    files, shared by both formats.
    """

    presets: list[str]
    kernels: list[str]
    ddcs: list[str]


def _stems(directory: Path, ext: str) -> list[str]:
    """Sorted stems of ``*ext`` files directly inside ``directory``."""
    return sorted(
        p.stem for p in directory.iterdir() if p.is_file() and p.suffix == ext
    )


def select_whitelist_preset(group: list[str], whitelist: list[str]) -> str:
    """Pick one name from a duplicate group of preset names.

    Returns the first (sorted) name containing a whitelist keyword, or the first
    name in the group when none match.
    """
    matching_names = [
        name
        for name in group
        if any(word.lower() in name.lower() for word in whitelist)
    ]
    if matching_names:
        return sorted(matching_names)[0]
    return group[0]


def preset_dependencies(xml_path: Path) -> tuple[str | None, str | None]:
    """Return the (kernel, ddc) file stems a preset references, if any."""
    found = search_in_xml(
        xml=xml_path,
        keys=["65540;65541;65542", "65547"],
    )
    irs = found["65540;65541;65542"]
    vdc = found["65547"]
    return (
        Path(irs).stem if irs else None,
        Path(vdc).stem if vdc else None,
    )


def select_full(
    xml_src: Path,
    irs_dir: Path,
    vdc_dir: Path,
) -> Selection:
    """Full variant - every preset, kernel & DDC."""
    return Selection(
        presets=_stems(directory=xml_src, ext=".xml"),
        kernels=_stems(directory=irs_dir, ext=".irs"),
        ddcs=_stems(directory=vdc_dir, ext=".vdc"),
    )


def select_lite(
    preset_groups: list[list[str]],
    xml_src: Path,
    irs_dir: Path,
    vdc_dir: Path,
) -> Selection:
    """Lite variant - one preset per duplicate group, plus its companions."""
    presets: list[str] = []
    for group in preset_groups:
        name = (
            select_whitelist_preset(group=group, whitelist=whitelist)
            if len(group) > 1
            else group[0]
        )
        presets.append(name)

    kernels: set[str] = set()
    ddcs: set[str] = set()
    for name in presets:
        irs, vdc = preset_dependencies(xml_path=xml_src / f"{name}.xml")
        if irs and (irs_dir / f"{irs}.irs").is_file():
            kernels.add(irs)
        if vdc and (vdc_dir / f"{vdc}.vdc").is_file():
            ddcs.add(vdc)

    return Selection(
        presets=sorted(presets),
        kernels=sorted(kernels),
        ddcs=sorted(ddcs),
    )


def select_recommended(
    lite: Selection,
    irs_groups: list[list[str]],
    vdc_groups: list[list[str]],
) -> Selection:
    """Recommended variant - Lite presets, plus one of every unique kernel/DDC.

    Keeps Lite's preset selection and its companions, then tops up the
    kernels/DDCs so every unique ``.irs``/``.vdc`` (one per duplicate group) is
    represented at least once.
    """
    kernels = set(lite.kernels)
    for group in irs_groups:
        if not kernels.intersection(group):
            kernels.add(group[0])

    ddcs = set(lite.ddcs)
    for group in vdc_groups:
        if not ddcs.intersection(group):
            ddcs.add(group[0])

    return Selection(
        presets=list(lite.presets),
        kernels=sorted(kernels),
        ddcs=sorted(ddcs),
    )


def materialize(
    selection: Selection,
    dest: ReleaseFiles,
    fmt: PresetFormat,
    irs_dir: Path,
    vdc_dir: Path,
) -> list[str]:
    """Copy a selection into ``dest`` for ``fmt``. Returns missing preset names."""
    missing: list[str] = []

    for name in selection.presets:
        src = fmt.src_dir / f"{name}{fmt.ext}"
        if src.is_file():
            shutil.copy2(src=src, dst=dest.preset_dir / src.name)
        else:
            missing.append(name)

    for irs in selection.kernels:
        src = irs_dir / f"{irs}.irs"
        if src.is_file():
            shutil.copy2(src=src, dst=dest.kernel_dir / src.name)

    for vdc in selection.ddcs:
        src = vdc_dir / f"{vdc}.vdc"
        if src.is_file():
            shutil.copy2(src=src, dst=dest.ddc_dir / src.name)

    return missing


def create_release(
    irs_dir: Path,
    vdc_dir: Path,
    xml_dir: Path,
    json_dir: Path,
    output_dir: Path,
    version: str,
) -> Path:
    """Create a release with 3 variants - Full, Lite & Recommended.

    The variant selections (which presets / kernels / DDCs each contains) are
    computed once, in code, from the duplicate analysis, then materialised for
    every preset format: the 2.7.2+ XML under ``<version>/XML`` and the modern
    ``com.llsl.viper4android`` JSON under ``<version>/JSON``. Both formats share
    one selection, so they stay in lockstep.
    """
    print(f"Creating Release {version} ...")

    release_dir = output_dir / version
    create_directories(directories=[release_dir])

    # --- Collect names (in code, and as dup_*.txt) -------------------------
    # Duplicate groups drive the Lite/Recommended selection; check_duplicates
    # also writes the canonical dup_{irs,vdc,xml}.txt at the release root.
    groups = check_duplicates(
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
        xml_dir=xml_dir,
        output_dir=release_dir,
    )
    list_missings(
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
        xml_dir=xml_dir,
        output_dir=release_dir,
    )

    full = select_full(
        xml_src=xml_dir,
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
    )
    lite = select_lite(
        preset_groups=groups["xml"],
        xml_src=xml_dir,
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
    )
    recommended = select_recommended(
        lite=lite,
        irs_groups=groups["irs"],
        vdc_groups=groups["vdc"],
    )
    selections = {"Full": full, "Lite": lite, "Recommended": recommended}

    # --- Materialise every variant for every format, from the same names ---
    formats = [
        PresetFormat(name="XML", src_dir=xml_dir, ext=".xml"),
        PresetFormat(name="JSON", src_dir=json_dir, ext=".json"),
    ]

    for fmt in formats:
        print(f"Creating {fmt.name} Release ...")
        fmt_dir = release_dir / fmt.name

        for variant_name, selection in selections.items():
            variant = ReleaseFiles.create(
                base_path=fmt_dir,
                variant_name=variant_name,
            )
            missing = materialize(
                selection=selection,
                dest=variant,
                fmt=fmt,
                irs_dir=irs_dir,
                vdc_dir=vdc_dir,
            )
            if missing:
                print(
                    f"  [{fmt.name}/{variant_name}] no {fmt.ext} preset for: "
                    f"{', '.join(missing)}"
                )

            # Per-variant diagnostics parse the <map> format, so XML only.
            if fmt.name == "XML":
                list_missings(
                    irs_dir=variant.kernel_dir,
                    vdc_dir=variant.ddc_dir,
                    xml_dir=variant.preset_dir,
                    output_dir=variant.base_dir,
                )
                check_duplicates(
                    irs_dir=variant.kernel_dir,
                    vdc_dir=variant.ddc_dir,
                    xml_dir=variant.preset_dir,
                    output_dir=variant.base_dir,
                )

    return release_dir
