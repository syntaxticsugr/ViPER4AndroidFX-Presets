import os
import shutil


# Path to Preset Directory
xml_directory = r''

# Path to DDC & Kernel Directory
vdc_directory = r''
irs_directory = r''

# Path where to store Filtered DDC & Kernel
new_vdc_directory = r''
new_irs_directory = r''


# Loading List of XML's
xml_files = os.listdir(xml_directory)

# Looping through Each File in XML's Directory
for xml_file in xml_files:

    # Opening XML File  
    with open(xml_directory + '/' + xml_file, 'r') as xml:

        # Loading XML Content
        xml_content = xml.readlines()

        # Looping through Each Line of XML
        for line in xml_content:

            # Filtering DDC(.vdc)
            if ("65547" in line):
                vdc_name = line[(line.find(">")+1):line.find("<", line.find(">"))]
                if (vdc_name != ""):
                    try:
                        shutil.copyfile(vdc_directory + '/' + vdc_name, new_vdc_directory + '/' + vdc_name)
                    except: pass

            # Filtering Kernel(.irs)
            if ("65540;65541;65542" in line):
                irs_name = line[(line.find(">")+1):line.find("<", line.find(">"))]
                if (irs_name != ""):
                    try:
                        shutil.copyfile(irs_directory + '/' + irs_name, new_irs_directory + '/' + irs_name)
                    except: pass
