import os
from collections import defaultdict
from pathlib import Path

from utils.create_directories import create_directories
from utils.sha256 import sha256


def write_duplicates_to_file(hashes: defaultdict, filename: Path) -> None:
    with open(file=filename, mode="w") as dup_txt:
        duplicates = []

        for key, value in hashes.items():
            value = sorted(value)
            duplicates.append(f"{len(value)} : {key} : {value}\n")

        duplicates = sorted(
            duplicates,
            key=lambda x: (int(x.split(" : ")[0]), x.split(" : ")[1]),
            reverse=True,
        )
        dup_txt.writelines(duplicates)


def hash_groups(hashes: defaultdict) -> list[list[str]]:
    """Duplicate groups as in-code data: each a sorted list of file stems.

    Mirrors ``write_duplicates_to_file``'s ordering (largest group first) so the
    in-code groups and the ``dup_*.txt`` lines line up one-to-one.
    """
    groups = [sorted(names) for names in hashes.values()]
    groups.sort(key=lambda names: (len(names), names[0]), reverse=True)
    return groups


def process_directory(directory: Path, hashes: defaultdict) -> None:
    for root, _, files in os.walk(top=directory):
        root = Path(root)

        for file in files:
            full_path = root / file
            file_name = full_path.stem

            file_hash = sha256(root=full_path)

            if file_name not in hashes[file_hash]:
                hashes[file_hash].add(file_name)


def check_duplicates(
    irs_dir: Path,
    vdc_dir: Path,
    xml_dir: Path,
    output_dir: Path,
) -> dict[str, list[list[str]]]:
    """Check for duplicate Kernels, DDCs & Presets.

    Writes the human-readable ``dup_{kernel,ddc,preset}.txt`` into ``output_dir``
    and returns the same grouping in code as ``{"kernel": [...], "ddc": [...],
    "preset": [...]}`` - each value a list of duplicate groups (sorted file
    stems). Kernels are the ``.irs``, DDCs the ``.vdc``, Presets the ``.xml``.
    """

    create_directories([output_dir])

    kernel_hashes, dup_kernel_txt = defaultdict(set), output_dir / "dup_kernel.txt"
    ddc_hashes, dup_ddc_txt = defaultdict(set), output_dir / "dup_ddc.txt"
    preset_hashes, dup_preset_txt = defaultdict(set), output_dir / "dup_preset.txt"

    process_directory(directory=irs_dir, hashes=kernel_hashes)
    process_directory(directory=vdc_dir, hashes=ddc_hashes)
    process_directory(directory=xml_dir, hashes=preset_hashes)

    write_duplicates_to_file(hashes=kernel_hashes, filename=dup_kernel_txt)
    write_duplicates_to_file(hashes=ddc_hashes, filename=dup_ddc_txt)
    write_duplicates_to_file(hashes=preset_hashes, filename=dup_preset_txt)

    return {
        "kernel": hash_groups(hashes=kernel_hashes),
        "ddc": hash_groups(hashes=ddc_hashes),
        "preset": hash_groups(hashes=preset_hashes),
    }
