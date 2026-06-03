import xml.etree.ElementTree as ET
from pathlib import Path


def search_in_xml(xml: Path, keys: list[str]) -> dict[str, str | None]:
    """
    Search for one or more keys in ViPER XML.
    Returns a dict mapping each requested key to its value (or None if not found).
    """
    tree = ET.parse(source=xml)
    root = tree.getroot()

    remaining = set(keys)
    found: dict[str, str | None] = {key: None for key in keys}

    for elem in root.findall(path=".//"):
        name = elem.get(key="name")
        if name in remaining:
            found[name] = elem.text or elem.get(key="value")
            remaining.discard(name)
            if not remaining:
                break

    return found
