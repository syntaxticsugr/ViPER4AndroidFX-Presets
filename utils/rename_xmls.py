import os

# Passing the path to Preset folder
preset_folder = r'/home/adity/Downloads/Viper4Android-presets-4a-2.7/Preset'

# Path to new Directory for storing Renamed Presets
new_directory = r'/home/adity/Downloads/Viper4Android-presets-4a-2.7/RenamedPreset'

# Getting the list of folders within Preset folder
folders = os.listdir(preset_folder)

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
        # And placing them in New Preset Directory
        os.rename(r'{}/{}/{}'.format(preset_folder, folder, file),
                  r'{}/{}{}'.format(new_directory, folder.strip().replace("_", "-").replace(" ", "-"), extension))
