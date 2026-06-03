from pathlib import Path


def create_directories(directories: list[Path]) -> None:
    """
    Creates multiple directories specified in the input list.

    Args:
        directories (list[Path]): A list of Path objects representing the directories to be created.

    Each directory is created with the following options:
    - `parents=True`: This allows the creation of any intermediate directories if they do not exist.
    - `exist_ok=True`: This prevents an error if a directory already exists.
    """
    for dir in directories:
        dir.mkdir(parents=True, exist_ok=True)
