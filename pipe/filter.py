import os
import shutil
from collections import defaultdict
from pathlib import Path

from utils.create_directories import create_directories
from utils.sha256 import sha256


def verify_xml(xml_path: Path) -> bool:
    """
    Check if XML file contains ViPER-specific features.
    Returns True if the XML is ViPER-compatible, False otherwise.
    """
    with open(file=xml_path, mode="r") as xml_file:
        xml_data = [line.strip() for line in xml_file.readlines()]
        check_features = ['<boolean name="36868"']  # [Master Switch]
        verify_result = all(
            any(feature in xml_line for xml_line in xml_data)
            for feature in check_features
        )

    if not verify_result:
        print(f"XML not for ViPER: {xml_path}")

    return verify_result


def copy_file(
    full_path: Path,
    target_dir: Path,
    file_name: str,
    file_extension: str,
    hashes: defaultdict[set],
    used: set[str],
) -> None:
    """Copy file into ``target_dir``, de-duplicating identical files and resolving
    name conflicts case-insensitively.

    A file is skipped only when an identical copy (same sha256) under the same
    name was already taken. Otherwise it is written as ``file_name``; if that name
    is already used - compared case-insensitively, so it is collision-safe on
    case-insensitive filesystems (macOS/Windows) too - a ``_2``, ``_3``, ... suffix
    is appended until the name is free. This guarantees no file is ever silently
    overwritten (e.g. ``SHURE SE215`` and ``Shure SE215`` both survive).
    """
    file_hash = sha256(root=full_path)

    if file_name in hashes[file_hash]:
        return

    hashes[file_hash].add(file_name)

    unique_name = file_name
    repeat = 1
    while unique_name.lower() in used:
        repeat += 1
        unique_name = f"{file_name}_{repeat}"
    used.add(unique_name.lower())

    shutil.copy2(src=full_path, dst=f"{target_dir / unique_name}{file_extension}")


def filter_irs_vdc_xml(input_dir: Path, output_dir: Path) -> Path:
    """Filter IRSs, VDCs & XMLs from a given directory with hash-based deduplication and name conflict resolution."""
    print("Filtering IRSs, VDCs & XMLs ...")

    filter_dir = output_dir / "filtered"
    irs_dir = filter_dir / "irs"
    vdc_dir = filter_dir / "vdc"
    xml_dir = filter_dir / "xml"
    create_directories(directories=[filter_dir, irs_dir, vdc_dir, xml_dir])

    irs_hashes, irs_used = defaultdict(set), set()
    vdc_hashes, vdc_used = defaultdict(set), set()
    xml_hashes, xml_used = defaultdict(set), set()

    for root, _, files in os.walk(top=input_dir):
        root = Path(root)

        for file in files:
            full_path = root / file

            file_name = full_path.stem.strip()
            file_extension = full_path.suffix

            if file_extension == ".irs":
                copy_file(
                    full_path=full_path,
                    target_dir=irs_dir,
                    file_name=file_name,
                    file_extension=file_extension,
                    hashes=irs_hashes,
                    used=irs_used,
                )

            elif file_extension == ".vdc":
                copy_file(
                    full_path=full_path,
                    target_dir=vdc_dir,
                    file_name=file_name,
                    file_extension=file_extension,
                    hashes=vdc_hashes,
                    used=vdc_used,
                )

            elif file_extension == ".xml":
                verify_result = verify_xml(xml_path=full_path)

                if verify_result:
                    if file_name in ["bt_a2dp", "headset", "speaker", "usb_device"]:
                        if file_name == "bt_a2dp":
                            file_name = "bluetooth"
                        elif file_name == "usb_device":
                            file_name = "usb"

                        new_file_name = f"{root.stem}{root.suffix}".strip()

                        if not (
                            any(
                                keyword in new_file_name.lower()
                                for keyword in [
                                    "bluetooth",
                                    "headset",
                                    "speaker",
                                    "usb",
                                ]
                            )
                        ):
                            new_file_name = f"{new_file_name}-{file_name}"

                    else:
                        new_file_name = file_name

                    copy_file(
                        full_path=full_path,
                        target_dir=xml_dir,
                        file_name=new_file_name,
                        file_extension=file_extension,
                        hashes=xml_hashes,
                        used=xml_used,
                    )

    return (irs_dir, vdc_dir, xml_dir)


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    filter_irs_vdc_xml(
        input_dir=input_dir,
        output_dir=output_dir,
    )
