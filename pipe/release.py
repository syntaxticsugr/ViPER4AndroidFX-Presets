import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from utils.create_directories import create_directories
from utils.release.check_duplicates import check_duplicates
from utils.release.list_missings import list_missings
from utils.release.preset_deps import preset_deps

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
    """The on-disk file structure for one release variant.

    ``Kernel`` and ``DDC`` hold the format-independent ``.irs``/``.vdc``
    companions, shared by every preset format. ``Preset`` is the parent for the
    per-format subfolders (``Preset/XML``, ``Preset/JSON_V1``, ``Preset/JSON_V2``).
    """

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
    """A converted preset format and where its duplicate analysis is keyed.

    ``key`` indexes the per-format groups returned by :func:`check_duplicates`;
    ``name`` is the release sub-folder under ``Preset/``.
    """

    name: str  # "XML" / "JSON_V1" / "JSON_V2"
    src_dir: Path
    ext: str  # ".xml" / ".json"
    key: str  # "xml" / "v1" / "v2"


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
        return min(matching_names)
    return group[0]


# A "-headphone"/"-speaker" fan-out tail, and the "_2"/"_3"/... collision suffix
# (which may sit before that tail, e.g. foo_2-speaker).
_MODE_TAIL = re.compile(pattern=r"-(?:headphone|speaker)$")
_COLLISION = re.compile(pattern=r"_\d+$")


def canonical_name(name: str, collisions: set[str]) -> str:
    """A preset name with a filter-added collision suffix removed.

    ``foo_2 -> foo``, ``foo_2-speaker -> foo-speaker`` - but only when the stem is
    one filter actually renamed (in ``collisions``). Guessing from the name alone
    is unsafe: ``Track_2024`` is a real name, not a collision, and must survive
    even beside a byte-identical ``Track``. Filter is the only stage that knows a
    given ``_N`` was a clash-breaker, so it tells us; everything else is left whole.
    """
    tail = _MODE_TAIL.search(name)
    core = name[: tail.start()] if tail else name
    if core in collisions:
        core = _COLLISION.sub("", core)
    return core + (tail.group(0) if tail else "")


def select_full(groups: list[list[str]], collisions: set[str]) -> list[str]:
    """Full - every distinctly named preset, minus pure re-download artifacts.

    Differently named presets are all kept even when byte-identical (they may be
    the same tuning under two names someone might search for). The only thing
    dropped is a re-download: within a group of identical files, a filter-renamed
    ``foo_2`` collapses onto the ``foo`` it was cloned from. Sorting makes the
    un-suffixed name win, since it sorts first.
    """
    kept: list[str] = []
    for group in groups:
        by_canonical: dict[str, str] = {}
        for name in sorted(group):
            by_canonical.setdefault(
                canonical_name(name=name, collisions=collisions),
                name,
            )
        kept.extend(by_canonical.values())
    return sorted(kept)


def select_deduped(groups: list[list[str]]) -> list[str]:
    """Lite / Recommended - one preset per identical-content group.

    Collapses every duplicate, including differently named ones, to a single
    representative: the whitelist-preferred name, else the first sorted. The
    groups are this format's own, so xml's coarser equivalence collapses more
    presets than v2's.
    """
    return sorted(
        select_whitelist_preset(group=group, whitelist=whitelist)
        if len(group) > 1
        else group[0]
        for group in groups
    )


def variant_companions(
    selected: dict[str, list[str]],
    formats: list[PresetFormat],
    variant: str,
    irs_dir: Path,
    vdc_dir: Path,
    groups: dict[str, list[list[str]]],
    collisions: dict[str, set[str]],
) -> tuple[set[str], set[str]]:
    """The kernels & DDCs a variant must ship for its selected presets.

    ``Full`` carries every companion, deduplicated the same way its presets are -
    every distinct name kept, but a filter-renamed re-download (``Hall_2.irs``
    identical to ``Hall.irs``) dropped. Otherwise the set is the union of what the
    selected presets reference across *all* formats - a kernel a v2 preset needs
    is shipped even if no xml preset references it. ``Recommended`` then tops the
    set up so every unique kernel/DDC is represented at least once.
    """
    if variant == "Full":
        return (
            set(select_full(groups=groups["kernel"], collisions=collisions["kernel"])),
            set(select_full(groups=groups["ddc"], collisions=collisions["ddc"])),
        )

    kernels: set[str] = set()
    ddcs: set[str] = set()
    for fmt in formats:
        for name in selected[fmt.name]:
            kernel, ddc = preset_deps(path=fmt.src_dir / f"{name}{fmt.ext}")
            if kernel and (irs_dir / f"{kernel}.irs").is_file():
                kernels.add(kernel)
            if ddc and (vdc_dir / f"{ddc}.vdc").is_file():
                ddcs.add(ddc)

    if variant == "Recommended":
        for group in groups["kernel"]:
            if not kernels.intersection(group):
                kernels.add(group[0])
        for group in groups["ddc"]:
            if not ddcs.intersection(group):
                ddcs.add(group[0])

    return kernels, ddcs


def copy_companions(
    kernels: set[str],
    ddcs: set[str],
    dest: ReleaseFiles,
    irs_dir: Path,
    vdc_dir: Path,
) -> None:
    """Copy the given kernels & DDCs into ``dest`` (shared by every format)."""
    for kernel in sorted(kernels):
        src = irs_dir / f"{kernel}.irs"
        if src.is_file():
            shutil.copy2(src=src, dst=dest.kernel_dir / src.name)

    for ddc in sorted(ddcs):
        src = vdc_dir / f"{ddc}.vdc"
        if src.is_file():
            shutil.copy2(src=src, dst=dest.ddc_dir / src.name)


def copy_presets(presets: list[str], preset_dest: Path, fmt: PresetFormat) -> None:
    """Copy a format's selected presets into ``preset_dest``, warning on gaps.

    A name with no ``fmt.ext`` source is expected here, not an error: the formats
    are pruned and deduplicated independently, so a stem present in one need not
    exist in another.
    """
    for name in presets:
        src = fmt.src_dir / f"{name}{fmt.ext}"
        if src.is_file():
            shutil.copy2(src=src, dst=preset_dest / src.name)


def create_release(
    irs_dir: Path,
    vdc_dir: Path,
    xml_dir: Path,
    json_v1_dir: Path,
    json_v2_dir: Path,
    collisions: dict[str, set[str]],
    output_dir: Path,
    version: str,
) -> Path:
    """Create a release with 3 variants - Full, Lite & Recommended.

    Each preset format is deduplicated on its own (a preset can be a duplicate in
    xml yet distinct in v2), so every format gets its own selection. Kernels/DDCs
    are format-independent, so each variant ships one shared ``Kernel``/``DDC``
    set covering every format's selected presets, and the presets are written per
    format into ``Preset/XML`` (2.7.2+ XML), ``Preset/JSON_V1`` (the v1 flat
    ``com.llsl.viper4android`` JSON) and ``Preset/JSON_V2`` (the v2 grouped JSON
    the current app reads).
    """
    print(f"Creating Release {version} ...")

    release_dir = output_dir / version

    formats = [
        PresetFormat(name="XML", src_dir=xml_dir, ext=".xml", key="xml"),
        PresetFormat(name="JSON_V1", src_dir=json_v1_dir, ext=".json", key="v1"),
        PresetFormat(name="JSON_V2", src_dir=json_v2_dir, ext=".json", key="v2"),
    ]

    # --- Per-category duplicate analysis (also writes dup_*.txt) -----------
    # Presets are grouped per format; kernels/DDCs once. These groups drive the
    # Lite/Recommended selections below.
    groups = check_duplicates(
        categories={
            "kernel": irs_dir,
            "ddc": vdc_dir,
            "xml": xml_dir,
            "v1": json_v1_dir,
            "v2": json_v2_dir,
        },
        output_dir=release_dir,
    )
    list_missings(
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
        preset_dirs={"xml": xml_dir, "v1": json_v1_dir, "v2": json_v2_dir},
        output_dir=release_dir,
    )

    # Full keeps every distinct name (dropping only re-download "_N" artifacts);
    # Lite and Recommended collapse every duplicate to one. Both are per format.
    presets_by_variant = {
        "Full": {
            fmt.name: select_full(
                groups=groups[fmt.key],
                collisions=collisions["preset"],
            )
            for fmt in formats
        },
        "Lite": {fmt.name: select_deduped(groups=groups[fmt.key]) for fmt in formats},
    }
    presets_by_variant["Recommended"] = presets_by_variant["Lite"]

    # --- Materialise every variant -----------------------------------------
    for variant_name in ("Full", "Lite", "Recommended"):
        print(f"Creating {variant_name} Variant ...")
        variant = ReleaseFiles.create(
            base_path=release_dir,
            variant_name=variant_name,
        )

        selected = presets_by_variant[variant_name]

        # Kernels & DDCs are format-independent — one shared set per variant,
        # covering every format's selected presets.
        kernels, ddcs = variant_companions(
            selected=selected,
            formats=formats,
            variant=variant_name,
            irs_dir=irs_dir,
            vdc_dir=vdc_dir,
            groups=groups,
            collisions=collisions,
        )
        copy_companions(
            kernels=kernels,
            ddcs=ddcs,
            dest=variant,
            irs_dir=irs_dir,
            vdc_dir=vdc_dir,
        )

        for fmt in formats:
            preset_dest = variant.preset_dir / fmt.name
            create_directories(directories=[preset_dest])
            copy_presets(
                presets=selected[fmt.name],
                preset_dest=preset_dest,
                fmt=fmt,
            )

    return release_dir
