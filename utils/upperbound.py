import os



def upperbound(old_xml_directory):
    # Loading List of Old XMLs
    old_xml_files = os.listdir(old_xml_directory)

    list = []

    # Looping through Each File in Old XMLs folder
    for old_xml_file in old_xml_files:

        with open(old_xml_directory + '/' + old_xml_file) as old_xml:

            # Loading Old XML Content
            old_xml_content = old_xml.readlines()

            for old_line in old_xml_content:
                old_line = old_line.strip()

                if ("" in old_line):
                    old_line = old_line.split('"')
                    list.append(int(old_line[3]))
                    break   
    
    list.sort()
    print(list)



# Path to Old XMLs folder
old_xml_directory = r'C:/Users/aditya/Desktop/New folder/XML-Renamed'

# Function Call
upperbound(old_xml_directory)
