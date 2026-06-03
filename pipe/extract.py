import shutil
from pathlib import Path

import patoolib

from utils.create_directories import create_directories

# Supported archive formats
ARCHIVE_EXTENSIONS = {".rar", ".tar", ".zip", ".7z"}


def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """Extract a single archive to the specified directory."""
    try:
        patoolib.extract_archive(
            archive=str(object=archive_path),
            outdir=str(object=extract_to),
            verbosity=-1,
        )
        return True
    except Exception as e:
        print(f'Failed to extract "{archive_path}": {e}')
        return False


def copy_file(source: Path, destination: Path) -> None:
    """Copy a single file, creating parent directories if needed.

    Files extracted from archives already live inside the extract tree, so their
    destination resolves to themselves - those self-copies are skipped. When a
    *different* file already occupies the destination (including a case-only
    match on a case-insensitive filesystem, e.g. ``X.vdc`` vs ``x.vdc`` merged
    into one folder), a ``_2``, ``_3``, ... suffix is appended so the existing
    file is never overwritten.
    """
    # Self-copy: the file already lives at its destination.
    if source.resolve() == destination.resolve():
        return
    try:
        destination = get_unique_file(file_path=destination)
        create_directories(directories=[destination.parent])
        shutil.copy2(src=source, dst=destination)
    except Exception as e:
        print(f'Failed to copy "{source}": {e}')


def get_unique_directory(base_path: Path) -> Path:
    """Generate a unique directory path by appending a counter if needed."""
    if not base_path.exists():
        return base_path

    counter = 2
    while True:
        new_path = Path(f"{base_path}_{counter}")
        if not new_path.exists():
            return new_path
        counter += 1


def get_unique_file(file_path: Path) -> Path:
    """Generate a unique file path by appending a counter before the suffix.

    ``Path.exists`` is case-insensitive on macOS/Windows, so this also avoids
    overwriting a file whose name differs only by case.
    """
    if not file_path.exists():
        return file_path

    counter = 2
    while True:
        new_path = file_path.with_name(
            name=f"{file_path.stem}_{counter}{file_path.suffix}"
        )
        if not new_path.exists():
            return new_path
        counter += 1


def process_directory(
    current_dir: Path,
    extract_dir: Path,
    relative_path: Path,
    processed_archives: set[Path],
) -> None:
    """Process a directory recursively, handling both archives and target files."""
    # Process all items in the current directory
    for item in current_dir.iterdir():
        # Skip if item has been processed (prevents infinite loops)
        if item in processed_archives:
            continue

        if item.is_file():
            extension = item.suffix.lower()

            # Handle archives
            if extension in ARCHIVE_EXTENSIONS:
                processed_archives.add(item)
                extract_to = get_unique_directory(
                    base_path=extract_dir / relative_path / item.stem
                )

                if extract_archive(archive_path=item, extract_to=extract_to):
                    # Recursively process the extracted contents
                    process_directory(
                        current_dir=extract_to,
                        extract_dir=extract_dir,
                        relative_path=relative_path / item.stem,
                        processed_archives=processed_archives,
                    )

            # Handle files
            else:
                destination = extract_dir / relative_path / item.name
                copy_file(source=item, destination=destination)

        # Recursively process subdirectories
        elif item.is_dir():
            process_directory(
                current_dir=item,
                extract_dir=extract_dir,
                relative_path=relative_path / item.name,
                processed_archives=processed_archives,
            )


def extract_archives(input_dir: Path, output_dir: Path) -> Path:
    """Recursively extract archives."""
    print("Extracting Archives ...")

    extract_dir = output_dir / "extracted"
    create_directories(directories=[extract_dir])

    try:
        processed_archives: set[Path] = set()
        process_directory(
            current_dir=input_dir,
            extract_dir=extract_dir,
            relative_path=Path(),
            processed_archives=processed_archives,
        )
    except Exception as e:
        print(f"Error during processing: {e}")

    return extract_dir


if __name__ == "__main__":
    input_dir = Path("")
    output_dir = Path("")

    extract_archives(
        input_dir=input_dir,
        output_dir=output_dir,
    )
