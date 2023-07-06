import os

# Path to Preset folder
preset_folder = r''

# Path to New Directory for storing Renamed Presets
renamed_xml_directory = r''

# Getting the list of folders within Preset folder
folders = os.listdir(preset_folder)

# Total Number of XML Folders 
count = len(folders)

# Accessing each folder
for folder in folders:

    # Getting list of files in folder
    # Only one file in each folder in this case
    files = os.listdir(r'{}/{}'.format(preset_folder, folder))

    # Accessing each file
    for file in files:

        # Getting the file extension
        extension_pos = file.rfind(".")
        extension = file[extension_pos:]

        # Renaming file to folder name
        # Changing "_" and " " to "-" in XML's Name
        # And placing them in new Renamed XML Directory
        os.rename(r'{}/{}/{}'.format(preset_folder, folder, file),
                  r'{}/{}{}'.format(renamed_xml_directory, folder.strip().replace("_", "-").replace(" ", "-"), extension))

    # Printing Number of Remaining Folders to Process
    count-=1
    print("Remaining: ", count)
