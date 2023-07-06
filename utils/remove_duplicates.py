#!/usr/bin/env python
"""
Fast duplicate file finder.
Usage: duplicates.py <folder> [<folder>...]
Based on https://stackoverflow.com/a/36113168/300783
Modified for Python3 with some small code improvements.
"""
import os
import sys
import hashlib
from collections import defaultdict


# Path to Text Files
dup_vdc_txt_file = r''
dup_irs_txt_file = r''
dup_xml_txt_file = r''


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


def check_for_duplicates(paths):
    files_by_size = defaultdict(list)
    files_by_small_hash = defaultdict(list)
    files_by_full_hash = dict()

    for path in paths:
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

    # Opening Files To Work Upon
    # dup_ddc.txt
    # dup_irs.txt
    # dup_xml.txt
    # Collecting Duplicate File Names In Respective Text File
    with open(dup_vdc_txt_file, 'w+') as dup_vdc_txt, open(dup_irs_txt_file, 'w+') as dup_irs_txt, open(dup_xml_txt_file, 'w+') as dup_xml_txt:
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

                if full_hash in files_by_full_hash:
                    duplicate = files_by_full_hash[full_hash]

                    print("Duplicate found:\n - %s\n - %s\n" % (filename, duplicate))

                    if (".vdc" in os.path.basename(filename)):
                        # Collecting Duplicate File Names In Respective Text File
                        dup_vdc_txt.write("{}\n{}\n".format(os.path.basename(filename), os.path.basename(duplicate)))
                        # Deleting Duplicate VDC's
                        try:
                            os.remove(filename)
                        except: pass

                    if (".irs" in os.path.basename(filename)):
                        # Collecting Duplicate File Names In Respective Text File
                        dup_irs_txt.write("{}\n{}\n".format(os.path.basename(filename), os.path.basename(duplicate)))
                        # Deleting Duplicate IRS's
                        try:
                            os.remove(filename)
                        except: pass

                    if (".xml" in os.path.basename(filename)):
                        # Collecting Duplicate File Names In Respective Text File
                        dup_xml_txt.write("{}\n{}\n\n".format(os.path.basename(filename), os.path.basename(duplicate)))
                        # Deleting Duplicate XML's
                        try:
                            os.remove(filename)
                        except: pass

                else:
                    files_by_full_hash[full_hash] = filename


if __name__ == "__main__":
    if sys.argv[1:]:
        check_for_duplicates(sys.argv[1:])
    else:
        print("Usage: %s <folder> [<folder>...]" % sys.argv[0])
