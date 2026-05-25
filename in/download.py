import sys
from pathlib import Path

sys.path.append(str(object=Path(__file__).resolve().parent.parent))


import gdown

from utils.create_directories import create_directories


def download_files(download_dir: Path, file_ids: dict) -> None:
    """
    Downloads files from Google Drive using their file IDs and saves them into
    a specified directory. It organizes the files by author, creating a separate
    folder for each author.

    Args:
        download_dir (str): The directory where the files should be saved.
        file_ids (dict): A dictionary where each key is an author name and the value
        is another dictionary with file names as keys and Google Drive file IDs as values.
    """

    for author, files in file_ids.items():
        author_dir = download_dir / author
        create_directories(directories=[author_dir])

        for file_name, file_id in files.items():
            out_file = author_dir / f"{file_name}.zip"
            if out_file.exists():
                print(f"Skipping (Already Downloaded): {out_file}")
                continue
            gdown.download(id=file_id, output=str(object=out_file))


if __name__ == "__main__":
    download_dir = Path("in")

    # {
    #     'author': {
    #         'file_name': 'file_id'
    #     }
    # }
    file_ids = {
        "jadilson12": {"Viper4Android-presets": "19pn29medRLzy8m9uPzkPmpvPSgHIsbz7"},
        "Joe0Bloggs": {"IRS": "19rEUl8QlBUWpgWrpaMxv2XnEVpZxXavV"},
        "JohnFawkes": {"ViperIRS": "19thPV8G2eOohh-ihUJadEL3bwqwgvd-G"},
        "programminghoch10": {
            "ViperIRS": "1mu3l2mLuRlpuIIKUoA6a6Eg2Y27xEcrl",
            "ViperVDC": "1oojAJp8ze7SzC5KHoGGGb6x1MIuSekjL",
        },
        "WSTxda": {
            "DDC": "1CKByuHZ_6AMHDC2NIo2H92ZEkR6Cv1SR",
            "Kernel": "1y1HiV-SvzmqoYEzAIuztV-tya6DkYQzO",
        },
    }

    download_files(download_dir=download_dir, file_ids=file_ids)
