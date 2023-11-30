import os
import shutil



# Function to rename Presets (XMLs)
def rename_presets(presets_folder, renamed_presets_folder):

    # Getting the list of subfolders within Presets folder
    sub_folders = os.listdir(presets_folder)

    # Total number of subfolders in Presets folder 
    count = len(sub_folders)

    # Accessing each subfolder
    for sub_folder in sub_folders:

        # Getting list of files in subfolder
        # Only one file in each subfolder in most cases
        files = os.listdir(r'{}/{}'.format(presets_folder, sub_folder))

        # Accessing each file in subfolder
        for file in files:

            # Renaming file to subfolder name
            # Changing "_" and " " to "-" in Presets Name
            # Placing renamed Presets in renamed-presets folder
            source = r'{}/{}/{}'.format(presets_folder, sub_folder, file)
            destination = r'{}/{}.xml'.format(renamed_presets_folder, sub_folder.strip().replace("_", "-").replace(" ", "-"))
            try:
                shutil.copyfile(source, destination)
            except:
                pass

        # Printing number of remaining subfolders to process
        count-=1
        print("Remaining: ", count)



# Path to Presets folder
presets_folder = r''

# Path to a new folder for saving Renamed Presets
renamed_presets_folder = r''

# Function Call
rename_presets(presets_folder, renamed_presets_folder)
