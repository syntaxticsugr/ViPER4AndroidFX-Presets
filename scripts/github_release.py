import sys
from pathlib import Path

sys.path.append(str(object=Path(__file__).resolve().parent.parent))

import re
import zipfile

from scripts.format import format_codebase

# Prefix for the published GitHub release archives (zip artifacts).
ARCHIVE_PREFIX = "ViPER4Android-Presets"

# The pipeline's output directory - the source of truth for a standalone run.
OUTPUT_DIR = Path("out")

# Root README (with its auto-generated "Release Info" table) and LICENSE - the
# two docs bundled into every release archive.
README = Path("README.md")
LICENSE = Path("LICENSE")
RELEASES_URL = "https://github.com/syntaxticsugr/ViPER4Android-Presets/releases/latest"
VARIANTS = ("Full", "Lite", "Recommended")
# Static blurb describing what each variant contains (one cell per variant).
VARIANT_BLURB = {
    "Full": "All `Preset`s<br>All `Kernel`s<br>All `DDC`s",
    "Lite": "Unique `Preset`s<br>Required `Kernel`s<br>Required `DDC`s",
    "Recommended": "Unique `Preset`s<br>Unique `Kernel`s<br>Unique `DDC`s",
}
# Preset formats, each its own row in the table: (label, Preset/ sub-folder, ext).
# The spokes are pruned & deduplicated independently, so their counts diverge and
# are worth showing separately; kernels/DDCs are format-independent (one row each).
PRESET_FORMATS = (
    ("XML", "XML", ".xml"),
    ("JSON_V1", "JSON_V1", ".json"),
    ("JSON_V2", "JSON_V2", ".json"),
)


def _add_tree(zf: zipfile.ZipFile, src_dir: Path, arc_root: str) -> None:
    """Write every file under ``src_dir`` into ``zf`` beneath ``arc_root/``."""
    for path in sorted(src_dir.rglob(pattern="*")):
        if path.is_file():
            zf.write(
                filename=path,
                arcname=f"{arc_root}/{path.relative_to(src_dir).as_posix()}",
            )


def _add_docs(zf: zipfile.ZipFile, docs: list[Path], arc_root: str) -> None:
    """Write each existing doc into ``zf`` at ``arc_root/<name>``."""
    for doc in docs:
        if doc.is_file():
            zf.write(filename=doc, arcname=f"{arc_root}/{doc.name}")


def create_archives(
    release_dir: Path,
    version: str,
    docs: list[Path] | None = None,
) -> list[Path]:
    """Package a built release into GitHub-style zip artifacts.

    One archive per variant (``<prefix>-v<version>-<Variant>.zip`` - e.g.
    ``...-Full.zip``) plus a combined one (``<prefix>-v<version>.zip``). Every
    archive wraps its payload in a single top-level folder named after the
    artifact - so extraction yields ``<prefix>-v<version>-Full/Kernel|DDC|Preset``
    rather than spilling those into the current directory. The combined archive
    nests the three variant folders under ``<prefix>-v<version>/``.

    The root ``README.md``, ``LICENSE`` and the loose per-spoke ``.txt``
    diagnostics (``dup_*``/``missing_*``/``pruned_*``) are bundled at the top
    level of every archive, beside the payload. Archives land in ``release_dir``;
    because each is built from an explicit file list that matches only ``.txt``
    (never a ``.zip``), the combined archive never swallows a sibling zip, so no
    out-of-tree staging is needed.

    Returns the created archive paths (inside ``release_dir``).
    """
    print("Creating Archives ...")

    if docs is None:
        docs = [README, LICENSE]
    # Ship the per-spoke diagnostics (dup_/missing_/pruned_*.txt) in every
    # archive too, at the top level beside the README and LICENSE.
    docs = [*docs, *sorted(release_dir.glob(pattern="*.txt"))]

    base = f"{ARCHIVE_PREFIX}-v{version}"
    variants = [variant for variant in VARIANTS if (release_dir / variant).is_dir()]

    archives: list[Path] = []

    # One zip per variant: <base>-<Variant>/ { Kernel, DDC, Preset, docs }.
    for variant in variants:
        arc_root = f"{base}-{variant}"
        zip_path = release_dir / f"{arc_root}.zip"
        with zipfile.ZipFile(
            file=zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zf:
            _add_tree(zf=zf, src_dir=release_dir / variant, arc_root=arc_root)
            _add_docs(zf=zf, docs=docs, arc_root=arc_root)
        archives.append(zip_path)

    # Combined zip: <base>/ { Full/, Lite/, Recommended/, docs }.
    zip_path = release_dir / f"{base}.zip"
    with zipfile.ZipFile(
        file=zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        for variant in variants:
            _add_tree(
                zf=zf,
                src_dir=release_dir / variant,
                arc_root=f"{base}/{variant}",
            )
        _add_docs(zf=zf, docs=docs, arc_root=base)
    archives.append(zip_path)

    return archives


def _count(directory: Path, suffix: str) -> int:
    """Number of ``*suffix`` files directly inside ``directory`` (0 if absent)."""
    if not directory.is_dir():
        return 0
    return sum(1 for p in directory.glob(pattern=f"*{suffix}") if p.is_file())


def _variant_counts(release_dir: Path, variant: str) -> tuple[dict[str, int], int, int]:
    """``(presets-by-format, kernels, ddcs)`` for one built variant.

    Presets are counted per format - the spokes diverge, since each is pruned and
    deduplicated on its own. Kernels and DDCs are format-independent, so a single
    count each.
    """
    base = release_dir / variant
    presets = {
        label: _count(directory=base / "Preset" / subdir, suffix=ext)
        for label, subdir, ext in PRESET_FORMATS
    }
    return (
        presets,
        _count(directory=base / "Kernel", suffix=".irs"),
        _count(directory=base / "DDC", suffix=".vdc"),
    )


def _md_code(text: str) -> str:
    """Turn markdown backtick code spans into HTML ``<code>`` for HTML cells."""
    return re.sub(pattern=r"`([^`]+)`", repl=r"<code>\1</code>", string=text)


def _release_table(release_dir: Path, version: str) -> str:
    """Render the README "Release Info" table as HTML (for merged cells).

    Markdown tables can't merge cells, so this emits an HTML ``<table>`` that
    GitHub renders inline: the ``Preset`` label spans its three per-format rows
    (``XML``/``JSON_V1``/``JSON_V2``, which diverge), while the format-independent
    ``Kernel`` and ``DDC`` labels span the label + format columns as single rows.
    """
    counts = {
        variant: _variant_counts(release_dir=release_dir, variant=variant)
        for variant in VARIANTS
    }

    def cell(value: object, tag: str = "td", **attrs: str) -> str:
        attr = "".join(f' {key}="{val}"' for key, val in attrs.items())
        return f"<{tag}{attr}>{value}</{tag}>"

    def tr(*cells: str) -> str:
        return "  <tr>" + "".join(cells) + "</tr>"

    header = tr(
        cell(f'<a href="{RELEASES_URL}">v{version}</a>', "th", colspan="2"),
        *(cell(variant, "th") for variant in VARIANTS),
    )
    blurb = tr(
        cell("⭐", colspan="2"),
        *(cell(_md_code(text=VARIANT_BLURB[variant])) for variant in VARIANTS),
    )

    preset_rows = []
    for index, (label, _subdir, _ext) in enumerate(PRESET_FORMATS):
        label_cell = (
            [cell("<b>Preset</b>", rowspan=str(object=len(PRESET_FORMATS)))]
            if index == 0
            else []
        )
        preset_rows.append(
            tr(
                *label_cell,
                cell(f"<code>{label}</code>"),
                *(cell(counts[variant][0][label]) for variant in VARIANTS),
            )
        )

    kernel = tr(
        cell("<b>Kernel</b>", colspan="2"),
        *(cell(counts[variant][1]) for variant in VARIANTS),
    )
    ddc = tr(
        cell("<b>DDC</b>", colspan="2"),
        *(cell(counts[variant][2]) for variant in VARIANTS),
    )

    return "\n".join(["<table>", header, blurb, *preset_rows, kernel, ddc, "</table>"])


def update_readme(release_dir: Path, version: str, readme: Path = README) -> None:
    """Refresh the root README's "Release Info" table from a built release.

    Rewrites the version header and the Preset/Kernel/DDC counts (read from each
    ``<release_dir>/<variant>`` tree) so the README always matches the latest
    release. Idempotent; a no-op (with a warning) if the table can't be located.
    """
    print("Updating README ...")

    text = readme.read_text(encoding="utf-8")
    table = _release_table(release_dir=release_dir, version=version)
    # Match the existing table whether it's HTML (current) or a markdown table
    # (pre-4.0.0), so a first run migrates it and later runs stay idempotent.
    new_text, replaced = re.subn(
        pattern=r"(### Release Info\n\n)(?:<table>[\s\S]*?</table>\n?|(?:\|.*\n)+)",
        repl=lambda m: m.group(1) + table + "\n",
        string=text,
    )
    if not replaced:
        print("  [readme] 'Release Info' table not found; skipped.")
        return
    readme.write_text(data=new_text, encoding="utf-8")


def find_release(output_dir: Path = OUTPUT_DIR) -> tuple[Path, str]:
    """Locate the built release under ``output_dir``.

    The release is the sub-directory that holds the variant folders
    (Full/Lite/Recommended); its name is the version. Returns
    ``(release_dir, version)``.
    """
    releases = [
        directory
        for directory in sorted(output_dir.iterdir())
        if directory.is_dir()
        and all((directory / variant).is_dir() for variant in VARIANTS)
    ]
    if not releases:
        raise FileNotFoundError(
            f"No release (a folder containing {', '.join(VARIANTS)}) found under "
            f"'{output_dir}'. Run the pipeline first."
        )
    release_dir = releases[-1]  # newest, if several
    return release_dir, release_dir.name


def github_release(output_dir: Path = OUTPUT_DIR, readme: Path = README) -> None:
    """Publish the built release: zip artifacts + a refreshed, formatted README.

    Standalone step - ``output_dir`` is the single source of truth. The release
    folder is discovered there (its name is the version); the README's "Release
    Info" table is refreshed to match and the codebase (incl. the rewritten
    README) is formatted, then the zip artifacts are written - in that order, so
    the README bundled into the archives is the finalised one.
    """
    release_dir, version = find_release(output_dir=output_dir)
    update_readme(release_dir=release_dir, version=version, readme=readme)
    format_codebase()
    create_archives(release_dir=release_dir, version=version, docs=[readme, LICENSE])


if __name__ == "__main__":
    github_release()
