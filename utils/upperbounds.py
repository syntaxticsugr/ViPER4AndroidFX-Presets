import os



def upperbound(old_presets_folder, search_key):

    # Getting list of old format Preset
    old_preset_files = os.listdir(old_presets_folder)

    list = []

    # Looping through each file in old format Presets folder
    for old_preset_file in old_preset_files:

        with open("{}/{}".format(old_presets_folder, old_preset_file)) as old_preset:

            # Loading old format Preset content
            old_xml_content = old_preset.read().splitlines()

            for old_line in old_xml_content:
                old_line = old_line.strip()

                if (search_key in old_line):
                    old_line = old_line.split('"')
                    list.append(int(old_line[3]))
                    break   
    
    list.sort()
    print(list)



# Path to old format Presets folder
old_presets_folder = r''

# Preset XML key to search values for
search_key = ""

# Function Call
upperbound(old_presets_folder)
