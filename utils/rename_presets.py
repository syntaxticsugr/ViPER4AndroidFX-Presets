import os
import pathlib
import re
import shutil



def regex_replace(string, replace_dict):
    new_string = re.sub("|".join(replace_dict.keys()), lambda match: replace_dict[match.string[match.start():match.end()]], string)
    return new_string



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
        files = os.listdir(f'{presets_folder}/{sub_folder}')

        # Accessing each file in subfolder
        for file in files:

            # Renaming Presets
            # Placing renamed Presets in renamed-presets folder
            preset_old_name = pathlib.Path(file).stem
            replace_dict = {
                "_" : "-",
                " " : "-",
                "headset" : "",
                "bluetooth" : "",
                "usb" : "",
                "speaker" : ""
            }
            preset_new_name = regex_replace(sub_folder, replace_dict)
            preset_new_name = f"{preset_new_name}-{preset_old_name}"
            replace_dict = {
                "---" : "-",
                "--" : "-",
                "bt_a2dp" : "bluetooth",
                "usb_device" : "usb"
            }
            preset_new_name = regex_replace(preset_new_name, replace_dict)

            source = f'{presets_folder}/{sub_folder}/{file}'
            destination = f'{renamed_presets_folder}/{preset_new_name}.xml'

            shutil.copyfile(source, destination)

        # Printing number of remaining subfolders to process
        count-=1
        print("Remaining: ", count)



# Path to Presets folder
presets_folder = r''

# Path to a new folder for saving Renamed Presets
renamed_presets_folder = r''

# Function Call
rename_presets(presets_folder, renamed_presets_folder)
