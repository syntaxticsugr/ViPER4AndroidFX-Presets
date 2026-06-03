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
    irs_dir: Path, vdc_dir: Path, xml_dir: Path, output_dir: Path
) -> tuple[Path, Path, Path]:
    """Check for duplicate IRSs, VDCs & XMLs and list them in dup.txt"""

    create_directories([output_dir])

    irs_hashes, dup_irs_txt = defaultdict(set), output_dir / "dup_irs.txt"
    vdc_hashes, dup_vdc_txt = defaultdict(set), output_dir / "dup_vdc.txt"
    xml_hashes, dup_xml_txt = defaultdict(set), output_dir / "dup_xml.txt"

    process_directory(directory=irs_dir, hashes=irs_hashes)
    process_directory(directory=vdc_dir, hashes=vdc_hashes)
    process_directory(directory=xml_dir, hashes=xml_hashes)

    write_duplicates_to_file(hashes=irs_hashes, filename=dup_irs_txt)
    write_duplicates_to_file(hashes=vdc_hashes, filename=dup_vdc_txt)
    write_duplicates_to_file(hashes=xml_hashes, filename=dup_xml_txt)

    return (dup_irs_txt, dup_vdc_txt, dup_xml_txt)
