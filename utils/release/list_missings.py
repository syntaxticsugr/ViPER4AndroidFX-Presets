import os
from collections import defaultdict
from pathlib import Path

from utils.release.search_in_xml import search_in_xml


def list_missings(
    irs_dir: Path,
    vdc_dir: Path,
    xml_dir: Path,
    output_dir: Path,
) -> None:
    """List missing IRSs & VDCs in missing.txt"""

    missing_irs = defaultdict(set)
    missing_vdc = defaultdict(set)

    for root, _, files in os.walk(top=xml_dir):
        root = Path(root)

        for file in files:
            xml = root / file

            found = search_in_xml(
                xml=xml,
                keys=["65540;65541;65542", "65547"],
            )
            irs = found["65540;65541;65542"]
            vdc = found["65547"]

            if (irs is not None) and not os.path.isfile(path=irs_dir / irs):
                missing_irs[irs].add(file)

            if (vdc is not None) and not os.path.isfile(path=vdc_dir / vdc):
                missing_vdc[vdc].add(file)

    with open(file=output_dir / "missing.txt", mode="w") as file:
        missing = ["[IRS]\n"]

        temp_missing = []
        for key, value in missing_irs.items():
            value = sorted(value)
            temp_missing.append(f"{len(value)} : {key} : {value}\n")

        temp_missing = sorted(
            temp_missing,
            key=lambda x: (int(x.split(sep=" : ")[0]), x.split(sep=" : ")[1]),
            reverse=True,
        )
        missing.extend(temp_missing)

        missing.append("\n[VDC]\n")

        temp_missing = []
        for key, value in missing_vdc.items():
            value = sorted(value)
            temp_missing.append(f"{len(value)} : {key} : {value}\n")

        temp_missing = sorted(
            temp_missing,
            key=lambda x: (int(x.split(sep=" : ")[0]), x.split(sep=" : ")[1]),
            reverse=True,
        )
        missing.extend(temp_missing)

        file.writelines(missing)
