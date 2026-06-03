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
    counts: defaultdict[int],
) -> None:
    """Copy file to target directory with hash-based deduplication and name conflict resolution."""
    file_hash = sha256(root=full_path)

    if file_name not in hashes[file_hash]:
        hashes[file_hash].add(file_name)

        name_repeat_count = counts[file_name] + 1
        counts[file_name] = name_repeat_count

        if 1 < name_repeat_count:
            file_name = f"{file_name}_{name_repeat_count}"

        shutil.copy2(src=full_path, dst=f"{target_dir / file_name}{file_extension}")


def filter_irs_vdc_xml(input_dir: Path, output_dir: Path) -> Path:
    """Filter IRSs, VDCs & XMLs from a given directory with hash-based deduplication and name conflict resolution."""
    print("Filtering IRSs, VDCs & XMLs ...")

    filter_dir = output_dir / "filtered"
    irs_dir = filter_dir / "irs"
    vdc_dir = filter_dir / "vdc"
    xml_dir = filter_dir / "xml"
    create_directories(directories=[filter_dir, irs_dir, vdc_dir, xml_dir])

    irs_hashes, irs_counts = defaultdict(set), defaultdict(int)
    vdc_hashes, vdc_counts = defaultdict(set), defaultdict(int)
    xml_hashes, xml_counts = defaultdict(set), defaultdict(int)

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
                    counts=irs_counts,
                )

            elif file_extension == ".vdc":
                copy_file(
                    full_path=full_path,
                    target_dir=vdc_dir,
                    file_name=file_name,
                    file_extension=file_extension,
                    hashes=vdc_hashes,
                    counts=vdc_counts,
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
                        counts=xml_counts,
                    )

    return (irs_dir, vdc_dir, xml_dir)


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    filter_irs_vdc_xml(
        input_dir=input_dir,
        output_dir=output_dir,
    )
