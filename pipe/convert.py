from pathlib import Path

from utils.convert.convert_json import convert_json_presets
from utils.convert.convert_xml import convert_xml_presets


def convert_presets(input_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    """Convert ViPER presets to both supported formats.

    Orchestrates the two standalone converters in sequence: first
    :func:`utils.convert.convert_xml.convert_xml_presets` (legacy/older XML ->
    2.7.2+ ``<map>`` XML), then
    :func:`utils.convert.convert_json.convert_json_presets`
    (2.7.2+ XML -> modern ``com.llsl.viper4android`` JSON).

    Both outputs live under a single ``<output_dir>/preset-converted`` container:
    the XMLs in its ``xml/`` subdir and the JSON presets in its ``json/`` subdir.

    Returns ``(preset_xml_dir, preset_json_dir)``.
    """
    print("Converting Presets ...")

    preset_converted_dir = output_dir / "preset-converted"
    preset_xml_dir = preset_converted_dir / "xml"
    preset_json_dir = preset_converted_dir / "json"

    convert_xml_presets(input_dir=input_dir, output_dir=preset_xml_dir)
    convert_json_presets(input_dir=preset_xml_dir, output_dir=preset_json_dir)

    return preset_xml_dir, preset_json_dir


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    convert_presets(
        input_dir=input_dir,
        output_dir=output_dir,
    )
