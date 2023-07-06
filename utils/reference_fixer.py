import os


# Path to Text Files
dup_vdc_txt_file = r''
dup_irs_txt_file = r''

# Path to XML's Directory
preset_xml_directory = r''

# Loading List of XML's
preset_xml_files = os.listdir(preset_xml_directory)


# Total Number XML's 
count = len(preset_xml_files)

# Opening Files to work upon
# dup_vdc.txt
with open(dup_vdc_txt_file) as dup_vdc_txt:

    # Getting Entries in Log Text file
    content = dup_vdc_txt.readlines()

    # Looping through Each entry
    for n in range(0, len(content), 3):

        # Looping though Each XML file
        for preset_xml_file in preset_xml_files:

            # Getting XML data
            with open(preset_xml_directory + '/' + preset_xml_file, 'r') as file :
                filedata = file.read()

            # Updating XML dta
            filedata = filedata.replace(content[n].strip().replace("&", "&amp;"), content[n+1].strip().replace("&", "&amp;"))

            # Rewriting New Data in XML
            with open(preset_xml_directory + '/' + preset_xml_file, 'w') as file:
                file.write(filedata)

            # Printing Number of Remaining XML's to Process
            count-=1
            print("Remaining: ", count)

        # Resetting to Orignal Count
        count = len(preset_xml_files)


# Total Number XML's 
count = len(preset_xml_files)

# Opening Files to work upon
# dup_irs.txt
with open(dup_irs_txt_file) as dup_irs_txt:

    # Getting Entries in Log Text file
    content = dup_irs_txt.readlines()

    # Looping through Each entry
    for n in range(0, len(content), 3):

        # Looping though Each XML file
        for preset_xml_file in preset_xml_files:

            # Getting XML data
            with open(preset_xml_directory + '/' + preset_xml_file, 'r') as file :
                filedata = file.read()

            # Updating XML dta
            filedata = filedata.replace(content[n].strip().replace("&", "&amp;"), content[n+1].strip().replace("&", "&amp;"))

            # Rewriting New Data in XML
            with open(preset_xml_directory + '/' + preset_xml_file, 'w') as file:
                file.write(filedata)

            # Printing Number of Remaining XML's to Process
            count-=1
            print("Remaining: ", count)

        # Resetting to Orignal Count
        count = len(preset_xml_files)
