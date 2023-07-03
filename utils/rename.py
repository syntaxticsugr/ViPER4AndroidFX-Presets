import os

# Passing the path to Preset folder
path = r''

# Getting the list of folders within Preset folder
folders = os.listdir(path)

# Accessing each folder
for folder in folders:

    # Getting list of files in folder
    # Only one file in each folder in this case
    files = os.listdir(r'{}/{}'.format(path, folder))

    # Accessing each file
    for file in files:

        # Getting the file extension
        extension_pos = file.rfind(".")
        extension = file[extension_pos:]

        # Renaming file to folder name
        os.rename(r'{}/{}/{}'.format(path, folder, file),
                  r'{}/{}/{}{}'.format(path, folder, folder.strip(), extension))
