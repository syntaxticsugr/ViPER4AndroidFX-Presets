from pathlib import Path

from utils.convert.parse import parse


def preset_deps(path: Path) -> tuple[str | None, str | None]:
    """Return the (kernel, ddc) companion stems a preset references, if any.

    Reads them from the canon, so it works for any format - a v2 or v1 preset's
    convolver kernel and DDC device are found the same way as an xml's. This is
    the single extractor shared by release selection (which companions a variant
    must ship) and the missing-companion report (which of them are absent), so
    the two can never disagree about what a preset references.
    """
    canon, _mode = parse(path.read_text(encoding="utf-8", errors="replace"))
    kernel = canon.get("convolver.kernelFile") or ""
    ddc = canon.get("ddc.device") or ""
    return (
        Path(kernel).stem if kernel else None,
        Path(ddc).stem if ddc else None,
    )
