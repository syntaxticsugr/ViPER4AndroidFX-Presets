import sys
from pathlib import Path

from pipe.convert import convert_presets
from pipe.extract import extract_archives
from pipe.filter import filter_irs_vdc_xml
from pipe.release import create_release
from utils.create_directories import create_directories


def process(input_dir: Path, output_dir: Path, version: str) -> None:
    extract_dir = extract_archives(
        input_dir=input_dir,
        output_dir=output_dir,
    )
    irs_dir, vdc_dir, xml_dir = filter_irs_vdc_xml(
        input_dir=extract_dir,
        output_dir=output_dir,
    )
    preset_xml_dir, preset_json_dir = convert_presets(
        input_dir=xml_dir,
        output_dir=output_dir,
    )
    release_dir = create_release(
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
        xml_dir=preset_xml_dir,
        json_dir=preset_json_dir,
        output_dir=output_dir,
        version=version,
    )
    print(f"Files Saved In: {release_dir}")


def main(input_dir: Path, output_dir: Path, version: str) -> None:
    if not input_dir.is_dir():
        print(f"Error: The input directory '{input_dir}' does not exist.")
        sys.exit(status=1)

    create_directories(directories=[output_dir])
    process(
        input_dir=input_dir,
        output_dir=output_dir,
        version=version,
    )


if __name__ == "__main__":
    version = "2.2.0"

    input_dir = Path("in")
    output_dir = Path("out")

    main(
        input_dir=input_dir,
        output_dir=output_dir,
        version=version,
    )
