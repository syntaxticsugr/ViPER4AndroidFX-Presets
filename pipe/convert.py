from pathlib import Path

from utils.convert.convert_json_v1 import convert_json_v1_presets
from utils.convert.convert_json_v2 import convert_json_v2_presets
from utils.convert.convert_xml import convert_xml_presets


def convert_presets(input_dir: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    """Convert ViPER presets to all three supported formats.

    Runs the standalone converters in sequence:
      1. :func:`utils.convert.convert_xml.convert_xml_presets`
         (legacy/older XML -> 2.7.2+ ``<map>`` XML),
      2. :func:`utils.convert.convert_json_v1.convert_json_v1_presets`
         (2.7.2+ XML -> v1 flat ``com.llsl.viper4android`` JSON), then
      3. :func:`utils.convert.convert_json_v2.convert_json_v2_presets`
         (v1 flat JSON -> v2 grouped JSON, the format the current app reads).

    All three outputs live under a single ``<output_dir>/preset-converted``
    container, in the ``xml/``, ``json_v1/`` and ``json_v2/`` subdirs.

    Returns ``(preset_xml_dir, preset_json_v1_dir, preset_json_v2_dir)``.
    """
    print("Converting Presets ...")

    preset_converted_dir = output_dir / "preset-converted"
    preset_xml_dir = preset_converted_dir / "xml"
    preset_json_v1_dir = preset_converted_dir / "json_v1"
    preset_json_v2_dir = preset_converted_dir / "json_v2"

    convert_xml_presets(input_dir=input_dir, output_dir=preset_xml_dir)
    convert_json_v1_presets(input_dir=preset_xml_dir, output_dir=preset_json_v1_dir)
    convert_json_v2_presets(input_dir=preset_json_v1_dir, output_dir=preset_json_v2_dir)

    return preset_xml_dir, preset_json_v1_dir, preset_json_v2_dir


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    convert_presets(
        input_dir=input_dir,
        output_dir=output_dir,
    )
