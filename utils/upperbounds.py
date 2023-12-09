import os



def upperbound(old_presets_folder, search_keys):

    # Getting list of old format Preset
    old_preset_files = os.listdir(old_presets_folder)

    count = 0
    uni_set = set()

    # Looping through each file in old format Presets folder
    for old_preset_file in old_preset_files:

        with open("{}/{}".format(old_presets_folder, old_preset_file)) as old_preset:

            # Loading old format Preset content
            old_xml_content = old_preset.read().splitlines()

            for old_line in old_xml_content:
                old_line = old_line.strip()

                if any(key in old_line for key in search_keys):
                    count+=1
                    old_line = old_line.split('"')
                    uni_set.add(int(old_line[3]))
                    break

    print(sorted(uni_set))
    print(count)



# Path to old format Presets folder
old_presets_folder = r''

# Preset XML key to search values for
search_keys = []

# Function Call
upperbound(old_presets_folder, search_keys)
