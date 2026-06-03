import hashlib


def sha256(root) -> str:
    """
    Computes the SHA-256 hash of a file.

    This function reads the file in binary mode, processes it in chunks (to handle large files),
    and computes its SHA-256 hash.

    Args:
        root (str): The file path of the file to be hashed.

    Returns:
        str: The hexadecimal SHA-256 hash of the file content.
    """

    hasher = hashlib.sha256()

    with open(file=root, mode="rb") as f:
        for chunk in iter(lambda: f.read(1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()
