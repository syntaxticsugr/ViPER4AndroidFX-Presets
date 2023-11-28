"""
Fast duplicate file finder.
Usage: duplicates.py <folder> [<folder>...]
Based on https://stackoverflow.com/a/36113168/300783
Modified for Python3 with some small code improvements.
"""
import os
import hashlib
from collections import defaultdict



def chunk_reader(fobj, chunk_size=1024):
    """ Generator that reads a file in chunks of bytes """
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk



def get_hash(filename, first_chunk_only=False, hash_algo=hashlib.sha1):
    hashobj = hash_algo()
    with open(filename, "rb") as f:
        if first_chunk_only:
            hashobj.update(f.read(1024))
        else:
            for chunk in chunk_reader(f):
                hashobj.update(chunk)
    return hashobj.digest()



def check_for_duplicates(path):
    files_by_size = defaultdict(list)
    files_by_small_hash = defaultdict(list)
    files_by_full_hash = defaultdict(list)

    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            try:
                # if the target is a symlink (soft one), this will
                # dereference it - change the value to the actual target file
                full_path = os.path.realpath(full_path)
                file_size = os.path.getsize(full_path)
            except OSError:
                # not accessible (permissions, etc) - pass on
                continue
            files_by_size[file_size].append(full_path)

    # For all files with the same file size, get their hash on the first 1024 bytes
    for file_size, files in files_by_size.items():
        if len(files) < 2:
            continue  # this file size is unique, no need to spend cpu cycles on it

        for filename in files:
            try:
                small_hash = get_hash(filename, first_chunk_only=True)
            except OSError:
                # the file access might've changed till the exec point got here
                continue
            files_by_small_hash[(file_size, small_hash)].append(filename)

    # For all files with the hash on the first 1024 bytes, get their hash on the full
    # file - collisions will be duplicates
    for files in files_by_small_hash.values():
        if len(files) < 2:
            # the hash of the first 1k bytes is unique -> skip this file
            continue

        for filename in files:
            try:
                full_hash = get_hash(filename, first_chunk_only=False)
            except OSError:
                # the file access might've changed till the exec point got here
                continue

            files_by_full_hash[full_hash].append(filename)

    return files_by_full_hash



# Function to Write Duplicate File Names in Respective Text Files
def save_duplicate_names(folder_path, dup_txt_file):
    files_by_full_hash = check_for_duplicates(folder_path)
    duplicate_files = {k: v for k, v in files_by_full_hash.items() if len(v) > 1}
    with open(dup_txt_file, 'w+', encoding='utf-8') as dup_txt:
        for hash_value, files in duplicate_files.items():
            dup_txt.write(f"Hash: {hash_value}\n")
            for file_path in files:
                dup_txt.write(f"  - {file_path}\n")
            dup_txt.write("\n")



# Function to Save Unique Files in a different folder
def save_unique_files(folder_path, new_save_path):
    files_by_full_hash = check_for_duplicates(folder_path)
    for _, files in files_by_full_hash.items():
        for file_path in files:
            os.rename(file_path, r'{}/{}'.format(new_save_path, (file_path.split("\\"))[-1]))
            break



# Path to Text Files for saving Names of Duplicate files
dup_vdc_txt_file = r'C:/Users/aditya/Desktop/New folder/utils/dup_vdc.txt'
dup_irs_txt_file = r'C:/Users/aditya/Desktop/New folder/utils/dup_irs.txt'
dup_xml_txt_file = r'C:/Users/aditya/Desktop/New folder/utils/dup_xml.txt'

# Path to Folders where need to check Duplicates
vdc_path = r'C:/Users/aditya/Desktop/New folder/DDC'
irs_path = r'C:/Users/aditya/Desktop/New folder/Kernel'
xml_path = r'C:/Users/aditya/Desktop/New folder/XML-Converted'

# Path to Folder where to save Unique files
new_vdc_path = r'C:/Users/aditya/Desktop/New folder/DDC-Unique'
new_irs_path = r'C:/Users/aditya/Desktop/New folder/Kernel-Unique'
new_xml_path = r'C:/Users/aditya/Desktop/New folder/XML-Unique'

# Function Call
save_duplicate_names(vdc_path, dup_vdc_txt_file)
save_duplicate_names(irs_path, dup_irs_txt_file)
save_duplicate_names(xml_path, dup_xml_txt_file)

# Function Call
save_unique_files(vdc_path, new_vdc_path)
save_unique_files(irs_path, new_irs_path)
save_unique_files(xml_path, new_xml_path)
