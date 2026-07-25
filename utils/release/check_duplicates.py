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
    categories: dict[str, Path],
    output_dir: Path,
) -> dict[str, list[list[str]]]:
    """Group each category's files by identical content.

    ``categories`` maps a name (``"kernel"``, ``"ddc"``, ``"xml"``, ``"v1"``,
    ``"v2"``, ...) to the directory holding that category's files. Each is hashed
    independently - which is the whole point for presets: the same tuning lands as
    identical bytes in one format and distinct bytes in another, so duplicates are
    a per-format question. Writes ``dup_<name>.txt`` into ``output_dir`` and
    returns ``{name: [duplicate groups]}`` (each group a list of sorted stems).
    """
    create_directories(directories=[output_dir])

    result: dict[str, list[list[str]]] = {}
    for name, directory in categories.items():
        hashes: defaultdict = defaultdict(set)
        process_directory(directory=directory, hashes=hashes)
        write_duplicates_to_file(hashes=hashes, filename=output_dir / f"dup_{name}.txt")
        result[name] = hash_groups(hashes=hashes)

    return result
