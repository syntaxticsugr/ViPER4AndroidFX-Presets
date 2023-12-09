import os
import hashlib
from collections import defaultdict
import shutil



def get_file_hash(file_path):
    # Function to calculate the SHA-256 hash of a file
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 1K
        for byte_block in iter(lambda: f.read(1024), b""):
            hash_sha256.update(byte_block)
    return hash_sha256.hexdigest()

def check_for_duplicates(folder_path):
    # Function to find duplicate files in a folder
    file_hash_dict = defaultdict(list)
    
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_hash = get_file_hash(file_path)
            file_hash_dict[file_hash].append(file_path)
    
    return file_hash_dict



# Function to Write Duplicate File Names in Respective Text Files
def save_duplicate_names(folder_path, dup_txt_file):
    file_hash_dict = check_for_duplicates(folder_path)
    duplicate_files = {k: v for k, v in file_hash_dict.items() if len(v) > 1}
    with open(dup_txt_file, 'w', encoding='utf-8') as dup_txt:
        for hash_value, files in duplicate_files.items():
            dup_txt.write(f"Hash: {hash_value}\n")
            for file in sorted(files):
                # dup_txt.write(f"\t- {file}\n")
                dup_txt.write(f"{os.path.basename(file)}\n")
            dup_txt.write("\n")



# Function to Save Unique Files in a different folder
def save_unique_files(folder_path, unique_save_path):
    file_hash_dict = check_for_duplicates(folder_path)
    for _, files in file_hash_dict.items():
        for file in files:
            destination = r'{}/{}'.format(unique_save_path, os.path.basename(file))
            shutil.copyfile(file, destination)
            break



# Path to log text files for saving names of duplicate files
dup_DDCs_txt_file = r''
dup_Kernels_txt_file = r''
dup_Presets_txt_file = r''

# Path to folders where need to check duplicates
DDCs_path = r''
Kernels_path = r''
Presets_path = r''

# Path to folders where to save unique files
unique_DDCs_path = r''
unique_Kernels_path = r''
unique_Presets_path = r''

# Function Call
save_duplicate_names(DDCs_path, dup_DDCs_txt_file)
save_duplicate_names(Kernels_path, dup_Kernels_txt_file)
save_duplicate_names(Presets_path, dup_Presets_txt_file)

# Function Call
save_unique_files(DDCs_path, unique_DDCs_path)
save_unique_files(Kernels_path, unique_Kernels_path)
save_unique_files(Presets_path, unique_Presets_path)
