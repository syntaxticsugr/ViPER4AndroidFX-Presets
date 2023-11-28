import os



# Function to Rename Preset XMLs
def rename_xmls(preset_folder, renamed_xml_directory):
    # Getting the list of folders within Preset folder
    folders = os.listdir(preset_folder)

    # Accessing each folder
    for folder in folders:

        # Getting list of files in folder
        # Here only one file in each folder in most cases
        files = os.listdir(r'{}/{}'.format(preset_folder, folder))

        # Accessing each file
        for file in files:

            # Getting the file extension
            _, extension = os.path.splitext(file)

            # Renaming file to folder name
            # Changing "_" and " " to "-" in XMLs Name
            # And placing them in new Renamed XML Directory
            os.rename(r'{}/{}/{}'.format(preset_folder, folder, file),
                    r'{}/{}{}'.format(renamed_xml_directory, folder.strip().replace("_", "-").replace(" ", "-"), extension))



# Path to XMLs folder
preset_folder = r''

# Path to a new folder for saving Renamed XMLs
renamed_xml_directory = r''

# Function Call
rename_xmls(preset_folder, renamed_xml_directory)
