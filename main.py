import shutil
import sys
from pathlib import Path

from pipe.convert import convert_presets
from pipe.extract import extract_archives
from pipe.filter import filter_presets
from pipe.prune import prune_noop_presets
from pipe.release import create_release
from utils.create_directories import create_directories


def process(input_dir: Path, output_dir: Path, version: str) -> None:
    release_dir = output_dir / version
    create_directories(directories=[release_dir])

    extract_dir = extract_archives(
        input_dir=input_dir,
        output_dir=output_dir,
    )
    irs_dir, vdc_dir, presets_dir, collisions = filter_presets(
        input_dir=extract_dir,
        output_dir=output_dir,
    )
    preset_xml_dir, preset_json_v1_dir, preset_json_v2_dir = convert_presets(
        input_dir=presets_dir,
        output_dir=output_dir,
    )

    prune_noop_presets(
        xml_dir=preset_xml_dir,
        json_v1_dir=preset_json_v1_dir,
        json_v2_dir=preset_json_v2_dir,
        report_dir=release_dir,
    )
    create_release(
        irs_dir=irs_dir,
        vdc_dir=vdc_dir,
        xml_dir=preset_xml_dir,
        json_v1_dir=preset_json_v1_dir,
        json_v2_dir=preset_json_v2_dir,
        collisions=collisions,
        output_dir=output_dir,
        version=version,
    )
    print(f"Files Saved In: {release_dir}")


def main(input_dir: Path, output_dir: Path, version: str) -> None:
    if not input_dir.is_dir():
        print(f"Error: The input directory '{input_dir}' does not exist.")
        sys.exit(status=1)

    if output_dir.exists():
        shutil.rmtree(path=output_dir)

    create_directories(directories=[output_dir])
    process(
        input_dir=input_dir,
        output_dir=output_dir,
        version=version,
    )


if __name__ == "__main__":
    version = "4.0.0"

    input_dir = Path("in")
    output_dir = Path("out")

    main(
        input_dir=input_dir,
        output_dir=output_dir,
        version=version,
    )
