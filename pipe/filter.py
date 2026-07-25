import os
import shutil
from pathlib import Path

from utils.convert.detect import FORMAT_DIRS, detect_format
from utils.create_directories import create_directories

# ViPER preset export files are often named for the device they target rather
# than the preset. Inside a pack folder these become the pack's per-device
# variants, so such a file is renamed after its folder (see resolve_preset_name).
_DEVICE_FILE_NAMES = {
    "bt_a2dp": "bluetooth",
    "headset": "headset",
    "speaker": "speaker",
    "usb_device": "usb",
}
_DEVICE_KEYWORDS = ("bluetooth", "headset", "speaker", "usb")


def resolve_preset_name(file_name: str, root: Path) -> str:
    """Resolve the release name for a preset, expanding device-named exports.

    A file literally named for a device (``headset``, ``speaker``, ``bt_a2dp``,
    ``usb_device``) is a per-device variant of the pack it sits in, so it is
    renamed after its folder - appending the device only when the folder name
    doesn't already say which one. Every other preset keeps its own name.
    """
    if file_name not in _DEVICE_FILE_NAMES:
        return file_name

    device = _DEVICE_FILE_NAMES[file_name]
    folder = f"{root.stem}{root.suffix}".strip()
    if any(keyword in folder.lower() for keyword in _DEVICE_KEYWORDS):
        return folder
    return f"{folder}-{device}"


def copy_file(full_path: Path, target_dir: Path, file_name: str, used: set[str]) -> str:
    """Copy ``full_path`` into ``target_dir`` as ``file_name``, never overwriting.

    Returns the stem actually written - equal to ``file_name`` unless the name was
    already taken, in which case a ``_2``, ``_3``, ... suffix was appended. That
    return value is how the caller learns a rename happened: it is the only place
    that knows a given ``_N`` is a collision artifact rather than part of a real
    name, which the release stage later needs to undo re-downloads correctly.

    Deduplication no longer happens here - identical files are collapsed later, on
    the converted output, where the canonical form catches far more of them. This
    only resolves name conflicts, compared case-insensitively so it is safe on
    macOS/Windows, so no file is ever lost.
    """
    extension = full_path.suffix

    unique_name = file_name
    repeat = 1
    while f"{unique_name}{extension}".lower() in used:
        repeat += 1
        unique_name = f"{file_name}_{repeat}"
    used.add(f"{unique_name}{extension}".lower())

    create_directories(directories=[target_dir])
    shutil.copy2(src=full_path, dst=target_dir / f"{unique_name}{extension}")
    return unique_name


def filter_presets(
    input_dir: Path, output_dir: Path
) -> tuple[Path, Path, Path, dict[str, set[str]]]:
    """Collect IRSs, VDCs and presets (xml + v1/v2 json) from an extract tree.

    Companion ``.irs``/``.vdc`` files and every ViPER preset - in any source
    format - are gathered into ``filtered/{irs,vdc,presets}``, resolving name
    conflicts. The presets land in one folder because the converter detects each
    file's format itself.

    Presets are split by format into ``presets/{xml,json_v1,json_v2}`` (the
    converter walks that tree, and the fragments are convenient on their own).
    Classification uses the converter's own :func:`detect_format`, so "what counts
    as a preset" has one definition; a file it doesn't recognise is skipped.

    Returns ``(irs_dir, vdc_dir, presets_dir, collisions)``. ``collisions`` maps
    ``"kernel"``/``"ddc"``/``"preset"`` to the stems that were renamed to break a
    name clash (``foo_2``, ...) - the release stage uses it to tell a re-download
    artifact from a real ``_N`` in a name, which it can't otherwise know.
    """
    print("Filtering IRSs, VDCs & Presets ...")

    filter_dir = output_dir / "filtered"
    irs_dir = filter_dir / "irs"
    vdc_dir = filter_dir / "vdc"
    presets_dir = filter_dir / "presets"
    preset_dirs = {name: presets_dir / name for name in FORMAT_DIRS.values()}
    create_directories(
        directories=[
            filter_dir,
            irs_dir,
            vdc_dir,
            presets_dir,
            *preset_dirs.values(),
        ]
    )

    # Name clashes are resolved within each destination folder, so each format's
    # subfolder gets its own namespace (foo.xml and foo.json never collide).
    used: dict[str, set[str]] = {
        "kernel": set(),
        "ddc": set(),
        **{name: set() for name in preset_dirs},
    }
    collisions: dict[str, set[str]] = {"kernel": set(), "ddc": set(), "preset": set()}

    def gather(used_key: str, target_dir: Path, name: str, collision_cat: str) -> None:
        """Copy the current file, noting the stem if a clash forced a rename."""
        written = copy_file(
            full_path=full_path,
            target_dir=target_dir,
            file_name=name,
            used=used[used_key],
        )
        if written != name:
            collisions[collision_cat].add(written)

    for root, _, files in os.walk(top=input_dir):
        root = Path(root)

        for file in files:
            full_path = root / file
            file_name = full_path.stem.strip()
            extension = full_path.suffix.lower()

            if extension == ".irs":
                gather(
                    used_key="kernel",
                    target_dir=irs_dir,
                    name=file_name,
                    collision_cat="kernel",
                )
            elif extension == ".vdc":
                gather(
                    used_key="ddc",
                    target_dir=vdc_dir,
                    name=file_name,
                    collision_cat="ddc",
                )
            elif extension in (".xml", ".json"):
                fmt = detect_format(
                    text=full_path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                )
                if fmt is not None:
                    subdir = FORMAT_DIRS[fmt]
                    gather(
                        used_key=subdir,
                        target_dir=preset_dirs[subdir],
                        name=resolve_preset_name(file_name=file_name, root=root),
                        collision_cat="preset",
                    )

    return irs_dir, vdc_dir, presets_dir, collisions


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    filter_presets(
        input_dir=input_dir,
        output_dir=output_dir,
    )
