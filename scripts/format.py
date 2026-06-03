import argparse
import platform
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_WINDOWS = platform.system() == "Windows"


def run(
    cmd: list[str],
    check: bool,
    capture: bool,
    prefix: str,
):
    label = f"{prefix}: "
    print(f"{label}Run: {' '.join(cmd)}")

    return subprocess.run(
        args=cmd,
        check=check,
        text=True,
        capture_output=capture,
        shell=_WINDOWS,
    )


def filter_ignored(paths: list[Path]) -> list[Path]:
    if not paths:
        return paths

    # NUL-delimited I/O (-z) so non-ASCII paths are echoed verbatim instead
    # of C-quoted, which would otherwise break the string match below.
    try:
        result = subprocess.run(
            args=["git", "check-ignore", "--stdin", "-z"],
            input="\0".join(str(object=path) for path in paths),
            text=True,
            capture_output=True,
            cwd=_ROOT,
            shell=_WINDOWS,
        )
    except FileNotFoundError:
        return paths  # format everything

    ignored = {entry for entry in result.stdout.split("\0") if entry}
    return [path for path in paths if str(object=path) not in ignored]


def format_xml_files() -> None:
    formatted = 0

    for file_path in filter_ignored(paths=sorted(_ROOT.rglob(pattern="*.xml"))):
        result = run(
            cmd=["xmllint", "--format", str(object=file_path)],
            check=False,
            capture=True,
            prefix="Format",
        )
        if result.returncode == 0 and result.stdout:
            file_path.write_text(data=result.stdout)
            formatted += 1

    print(f"Format: XmlFormat: {formatted} File(s) Formatted")


def sort_requirements_files():
    req_files = filter_ignored(paths=sorted(_ROOT.rglob(pattern="requirements*.txt")))
    for req_file in req_files:
        lines = req_file.read_text().splitlines()
        sorted_lines = sorted(lines, key=lambda line: line.lower())
        # Remove empty lines from sort, preserve a trailing newline
        sorted_lines = [line for line in sorted_lines if line.strip()]
        req_file.write_text(data="\n".join(sorted_lines) + "\n")
        print(f"Format: SortRequirements: {req_file.relative_to(_ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Format Python Code: RUFF")
    parser.add_argument(
        "folders",
        nargs="*",
        default=["."],
        help="Folders To Format (Default: Current Directory)",
    )
    args = parser.parse_args()

    targets = args.folders

    run(
        cmd=["ruff", "format", *targets],
        check=True,
        capture=False,
        prefix="Format",
    )
    run(
        cmd=["ruff", "check", "--select", "I", "--fix", *targets],
        check=True,
        capture=False,
        prefix="Format",
    )
    run(
        cmd=["ruff", "check", "--fix", *targets],
        check=True,
        capture=False,
        prefix="Format",
    )
    run(
        cmd=["npx", "prettier", "--write", "."],
        check=True,
        capture=False,
        prefix="Format",
    )
    format_xml_files()
    sort_requirements_files()
    print("Format: Complete")


if __name__ == "__main__":
    main()
