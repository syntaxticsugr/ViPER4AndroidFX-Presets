import sys
from pathlib import Path

sys.path.append(str(object=Path(__file__).resolve().parent.parent))

import re
import shutil

from scripts.format import format_codebase

# Prefix for the published GitHub release archives (zip artifacts).
ARCHIVE_PREFIX = "ViPER4Android-Presets"

# The pipeline's output directory - the source of truth for a standalone run.
OUTPUT_DIR = Path("out")

# Root README and its auto-generated "Release Info" table.
README = Path("README.md")
RELEASES_URL = "https://github.com/syntaxticsugr/ViPER4Android-Presets/releases/latest"
VARIANTS = ("Full", "Lite", "Recommended")
# Static blurb describing what each variant contains (one cell per variant).
VARIANT_BLURB = {
    "Full": "All `Preset`s<br>All `Kernel`s<br>All `DDC`s",
    "Lite": "Unique `Preset`s<br>Required `Kernel`s<br>Required `DDC`s",
    "Recommended": "Unique `Preset`s<br>Unique `Kernel`s<br>Unique `DDC`s",
}


def create_archives(release_dir: Path, output_dir: Path, version: str) -> list[Path]:
    """Package a built release into GitHub-style zip artifacts.

    One archive per variant folder found in ``release_dir``
    (``<prefix>-v<version>-<Variant>.zip`` - e.g. ``...-Full.zip``) plus a
    combined archive of the whole release (``<prefix>-v<version>.zip``). Each
    archive carries that scope's ``Kernel``/``DDC``/``Preset`` tree and its
    ``.txt`` diagnostics.

    All archives land inside ``release_dir``. They are built in ``output_dir`` (a
    sibling) first and moved in afterwards: the combined archive zips
    ``release_dir`` wholesale, so building in place would make it swallow the
    per-variant zips (or itself).

    Returns the created archive paths (inside ``release_dir``).
    """
    print("Creating Archives ...")

    # Drop archives from a previous run so a re-run's combined zip (which zips
    # release_dir wholesale) doesn't swallow them.
    for stale in release_dir.glob(f"{ARCHIVE_PREFIX}-v*.zip"):
        stale.unlink()

    base = f"{ARCHIVE_PREFIX}-v{version}"
    # The variant folders (Full/Lite/Recommended) are the only subdirectories of
    # a freshly built release; the diagnostics are loose ``.txt`` files.
    variant_names = sorted(p.name for p in release_dir.iterdir() if p.is_dir())

    # Build outside release_dir so the combined archive (which zips release_dir)
    # never contains a zip: one per variant (its tree + diagnostics at the root),
    # then the combined one (every variant folder + the root diagnostics).
    staged: list[Path] = [
        Path(
            shutil.make_archive(
                base_name=str(object=output_dir / f"{base}-{variant_name}"),
                format="zip",
                root_dir=release_dir / variant_name,
            )
        )
        for variant_name in variant_names
    ]
    staged.append(
        Path(
            shutil.make_archive(
                base_name=str(object=output_dir / base),
                format="zip",
                root_dir=release_dir,
            )
        )
    )

    # Move the finished archives into release_dir.
    archives: list[Path] = []
    for archive in staged:
        dest = release_dir / archive.name
        shutil.move(src=str(object=archive), dst=str(object=dest))
        archives.append(dest)

    return archives


def _count(directory: Path, suffix: str) -> int:
    """Number of ``*suffix`` files directly inside ``directory`` (0 if absent)."""
    if not directory.is_dir():
        return 0
    return sum(1 for p in directory.glob(pattern=f"*{suffix}") if p.is_file())


def _variant_counts(release_dir: Path, variant: str) -> tuple[int, int, int]:
    """``(presets, kernels, ddcs)`` for one built variant.

    Presets are counted from ``Preset/XML`` (the JSON twin is 1:1).
    """
    base = release_dir / variant
    return (
        _count(directory=base / "Preset" / "XML", suffix=".xml"),
        _count(directory=base / "Kernel", suffix=".irs"),
        _count(directory=base / "DDC", suffix=".vdc"),
    )


def _release_table(release_dir: Path, version: str) -> str:
    """Render the README "Release Info" table from a built release."""
    counts = {
        variant: _variant_counts(release_dir=release_dir, variant=variant)
        for variant in VARIANTS
    }
    rows = [
        [f"[v{version}]({RELEASES_URL})", *VARIANTS],
        ["⭐", *(VARIANT_BLURB[variant] for variant in VARIANTS)],
        ["**Preset**", *(str(object=counts[v][0]) for v in VARIANTS)],
        ["**Kernel**", *(str(object=counts[v][1]) for v in VARIANTS)],
        ["**DDC**", *(str(object=counts[v][2]) for v in VARIANTS)],
    ]
    widths = [max(len(row[col]) for row in rows) for col in range(4)]

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join(
        [
            line(cells=rows[0]),
            separator,
            line(cells=rows[1]),
            line(cells=rows[2]),
            line(cells=rows[3]),
            line(cells=rows[4]),
        ]
    )


def update_readme(release_dir: Path, version: str, readme: Path = README) -> None:
    """Refresh the root README's "Release Info" table from a built release.

    Rewrites the version header and the Preset/Kernel/DDC counts (read from each
    ``<release_dir>/<variant>`` tree) so the README always matches the latest
    release. Idempotent; a no-op (with a warning) if the table can't be located.
    """
    print("Updating README ...")

    text = readme.read_text(encoding="utf-8")
    table = _release_table(release_dir=release_dir, version=version)
    new_text, replaced = re.subn(
        pattern=r"(### Release Info\n\n)(?:\|.*\n)+",
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
    folder is discovered there (its name is the version); its zip artifacts are
    written, the README's "Release Info" table is refreshed to match, and the
    codebase (incl. the rewritten README) is formatted.
    """
    release_dir, version = find_release(output_dir=output_dir)
    create_archives(release_dir=release_dir, output_dir=output_dir, version=version)
    update_readme(release_dir=release_dir, version=version, readme=readme)
    format_codebase()


if __name__ == "__main__":
    github_release()
