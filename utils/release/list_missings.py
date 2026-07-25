import os
from collections import defaultdict
from pathlib import Path

from utils.release.preset_deps import preset_deps


def _format_section(missing: dict[str, set[str]]) -> list[str]:
    """Render one companion type's misses as ``count : name : [presets]`` lines,
    largest group first (ties broken by name)."""
    lines = [
        f"{len(presets)} : {name} : {sorted(presets)}\n"
        for name, presets in missing.items()
    ]
    return sorted(
        lines,
        key=lambda line: (int(line.split(" : ")[0]), line.split(" : ")[1]),
        reverse=True,
    )


def list_missings(
    irs_dir: Path,
    vdc_dir: Path,
    preset_dirs: dict[str, Path],
    output_dir: Path,
) -> None:
    """Per spoke, list the IRS/VDC companions its presets reference but that are
    absent from ``irs_dir``/``vdc_dir``, into ``missing_<spoke>.txt``.

    ``preset_dirs`` maps a spoke name (``"xml"``, ``"v1"``, ``"v2"``) to its
    converted-preset directory. Each is scanned on its own - the spokes are
    pruned independently, so a preset (and thus its missing companion) can be
    present in one spoke yet gone from another.

    Companion refs are read from the canon (via :func:`preset_deps`), so every
    spoke is scanned the same way, and the very extraction that gathers a
    variant's companions is what decides here whether one is missing.
    """
    for spoke, preset_dir in preset_dirs.items():
        missing_irs: defaultdict[str, set[str]] = defaultdict(set)
        missing_vdc: defaultdict[str, set[str]] = defaultdict(set)

        for root, _, files in os.walk(top=preset_dir):
            root = Path(root)
            for file in files:
                kernel, ddc = preset_deps(path=root / file)
                if kernel and not (irs_dir / f"{kernel}.irs").is_file():
                    missing_irs[f"{kernel}.irs"].add(file)
                if ddc and not (vdc_dir / f"{ddc}.vdc").is_file():
                    missing_vdc[f"{ddc}.vdc"].add(file)

        lines = [
            "[IRS]\n",
            *_format_section(missing=missing_irs),
            "\n[VDC]\n",
            *_format_section(missing=missing_vdc),
        ]
        with open(file=output_dir / f"missing_{spoke}.txt", mode="w") as file:
            file.writelines(lines)
