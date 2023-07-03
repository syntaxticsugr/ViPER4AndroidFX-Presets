import os

# ID1 = Headset, Bluetooth, USB
# ID2 = Speaker

# Path to ViPER Default XML's
default_id1_xml_file = ''
default_id2_xml_file = ''

# Path to Old XML's Directory
old_xml_directory = ''
new_xml_directory = ''


# Loading List of Old XML's
files = os.listdir(old_xml_directory)

# Total Number of Old XML's 
count = len(files)

# Looping through Each File in Default XML's Directory
for file in files:

    # Opening Files to Work Upon
    # Default ID1 XML
    # Default ID2 XML
    # Old XML
    # New XML
    with open(default_id1_xml_file) as default_id1_file, open(default_id2_xml_file) as default_id2_file, open(file) as old_xml_file, open(new_xml_directory + "/" + os.path.basename(file), 'w+') as new_xml_file:

        # Selecting the Appropriate Default XML
        # Loading Default XML Content
        if("speaker" in os.path.basename(file).lower()):
            default_xml_content = default_id2_file.readlines()
        else:
            default_xml_content = default_id1_file.readlines()

        # Loading Old XML Content
        old_xml_content = old_xml_file.readlines()

        # Looping through Each Line of Default XML
        for default_line in default_xml_content:
            default_line = default_line.strip()

            # Mode
            # Master Limiter
            # Playback Gain Control
            # Master Limiter & Playback Gain Control kept to ViPER Defaults
            if any(key in default_line for key in ("32775", "36868", "65586", "65587", "65588", "65565", "65566", "65567", "65568")):
                new_xml_file.write(default_line + "\n")

            # FET Compressor
            # ViPER DDC
            # Spectrum Extension
            # FIR Equalizer
            # Convolver
            # Field Surround
            # Headphone Surround +
            # Reverberation
            # Dynamic System
            # Tube Simulator (6N1J)
            # ViPER Bass
            # ViPER Clarity
            # Auditory System Protection
            # AnalogX
            # Speaker Optimization
            else:
                for input_line in old_xml_content:
                    input_line = input_line.strip()
                    
                    # FET Compressor

                    if ("65610" in default_line):
                        if (("65610" in input_line) or ("65627" in input_line)):
                            new_xml_file.write(input_line.replace("65627", "65610") + "\n")
                            break

                    if ("65611" in default_line):
                        if (("65611" in input_line) or ("65628" in input_line)):
                            new_xml_file.write(input_line.replace("65628", "65611") + "\n")
                            break                   

                    if ("65612" in default_line):
                        if (("65612" in input_line) or ("65629" in input_line)):
                            new_xml_file.write(input_line.replace("65629", "65612") + "\n")
                            break  

                    if ("65613" in default_line):
                        if (("65613" in input_line) or ("65630" in input_line)):
                            new_xml_file.write(input_line.replace("65630", "65613") + "\n")
                            break  

                    if ("65614" in default_line):
                        if (("65614" in input_line) or ("65631" in input_line)):
                            new_xml_file.write(input_line.replace("65631", "65614") + "\n")
                            break  

                    if ("65615" in default_line):
                        if (("65615" in input_line) or ("65632" in input_line)):
                            new_xml_file.write(input_line.replace("65632", "65615") + "\n")
                            break  

                    if ("65616" in default_line):
                        if (("65616" in input_line) or ("65633" in input_line)):
                            new_xml_file.write(input_line.replace("65633", "65616") + "\n")
                            break  

                    if ("65617" in default_line):
                        if (("65617" in input_line) or ("65634" in input_line)):
                            new_xml_file.write(input_line.replace("65634", "65617") + "\n")
                            break  

                    if ("65618" in default_line):
                        if (("65618" in input_line) or ("65635" in input_line)):
                            new_xml_file.write(input_line.replace("65635", "65618") + "\n")
                            break  

                    if ("65619" in default_line):
                        if (("65619" in input_line) or ("65636" in input_line)):
                            new_xml_file.write(input_line.replace("65636", "65619") + "\n")
                            break  

                    if ("65620" in default_line):
                        if (("65620" in input_line) or ("65637" in input_line)):
                            new_xml_file.write(input_line.replace("65637", "65620") + "\n")
                            break  

                    if ("65621" in default_line):
                        if (("65621" in input_line) or ("65638" in input_line)):
                            new_xml_file.write(input_line.replace("65638", "65621") + "\n")
                            break  

                    if ("65622" in default_line):
                        if (("65622" in input_line) or ("65639" in input_line)):
                            new_xml_file.write(input_line.replace("65639", "65622") + "\n")
                            break  

                    if ("65623" in default_line):
                        if (("65623" in input_line) or ("65640" in input_line)):
                            new_xml_file.write(input_line.replace("65640", "65623") + "\n")
                            break  

                    if ("65624" in default_line):
                        if (("65624" in input_line) or ("65641" in input_line)):
                            new_xml_file.write(input_line.replace("65641", "65624") + "\n")
                            break                          

                    if ("65625" in default_line):
                        if (("65625" in input_line) or ("65642" in input_line)):
                            new_xml_file.write(input_line.replace("65642", "65625") + "\n")
                            break  

                    if ("65626" in default_line):
                        if (("65626" in input_line) or ("65643" in input_line)):
                            new_xml_file.write(input_line.replace("65643", "65626") + "\n")
                            break  

                    # FIR Equalizer

                    if ("65551" in default_line):
                        if (("65551" in input_line) or ("65595" in input_line)):
                            new_xml_file.write(input_line.replace("65595", "65551") + "\n")
                            break

                    if ("65552" in default_line):
                        if (("65552" in input_line) or ("65596" in input_line)):
                            new_xml_file.write(input_line.replace("65596", "65552") + "\n")
                            break
                    
                    # Convolver

                    if ("65538" in default_line):
                        if (("65538" in input_line) or ("65589" in input_line)):
                            new_xml_file.write(input_line.replace("65589", "65538") + "\n")
                            break
                    
                    if ("65540;65541;65542" in default_line):
                        if (("65540;65541;65542" in input_line) or ("65591;65592;65593" in input_line)):
                            new_xml_file.write(input_line.replace("65591;65592;65593", "65540;65541;65542") + "\n")
                            break
                    
                    if ("65543" in default_line):
                        if (("65543" in input_line) or ("65594" in input_line)):
                            new_xml_file.write(input_line.replace("65594", "65543") + "\n")
                            break
                    
                    # Reverberation

                    if ("65559" in default_line):
                        if (("65559" in input_line) or ("65597" in input_line)):
                            new_xml_file.write(input_line.replace("65597", "65559") + "\n")
                            break
                    
                    if ("65560" in default_line):
                        if (("65560" in input_line) or ("65598" in input_line)):
                            # Normalizing to range of 0 - 10
                            input_line = input_line.split('"')
                            if 10 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//10)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line.replace("65598", "65560") + "\n")
                            break                    

                    if ("65561" in default_line):
                        if (("65561" in input_line) or ("65599" in input_line)):
                            # Normalizing to range of 0 - 10
                            input_line = input_line.split('"')
                            if 10 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//10)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line.replace("65599", "65561") + "\n")
                            break

                    if ("65562" in default_line):
                        if (("65562" in input_line) or ("65600" in input_line)):
                            new_xml_file.write(input_line.replace("65600", "65562") + "\n")
                            break

                    if ("65563" in default_line):
                        if (("65563" in input_line) or ("65601" in input_line)):
                            new_xml_file.write(input_line.replace("65601", "65563") + "\n")
                            break

                    if ("65564" in default_line):
                        if (("65564" in input_line) or ("65602" in input_line)):
                            new_xml_file.write(input_line.replace("65602", "65564") + "\n")
                            break                      
                    
                    # ViPER DDC
                    # Spectrum Extention
                    # Field Surround
                    # Differential Surround
                    # Headphone Surround +
                    # Dynamic System
                    # Tube Simulator (6N1J)
                    # ViPER Bass
                    # ViPER Clarity
                    # Auditory System Protection
                    # AnalogX
                    if (default_line[default_line.find('"')+1:default_line.find('"', default_line.find('"')+1)] == input_line[input_line.find('"')+1:input_line.find('"', input_line.find('"')+1)]):

                        # Field Surround Value Normalization

                        if ("65554;65556" in default_line):
                            # Normalizing to range of 0 - 8
                            input_line = input_line.split('"')
                            if 80 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//8)
                            if 8 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//8)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line + "\n")
                            break  

                        if ("65555" in default_line):
                            # Normalizing to range of 0 - 11
                            input_line = input_line.split('"')
                            if 110 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//11)
                            if 11 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//11)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line + "\n")
                            break

                        # Differential Surround Value Normalization

                        if ("65558" in default_line):
                            # Normalizing to range of 0 - 19
                            input_line = input_line.split('"')
                            if 1900 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//19)
                            if 190 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//19)
                            if 19 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//19)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line + "\n")
                            break                      

                        # Dynamic System Value Normalization

                        if ("65573" in default_line):
                            # Normalizing to range of 0 - 100
                            input_line = input_line.split('"')
                            if 1000 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//10)
                            if 100 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//10)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line + "\n")
                            break   

                        # ViPER Bass Value Normalization

                        if ("65577" in default_line):
                            # Normalizing to range of 0 - 11
                            input_line = input_line.split('"')
                            if 110 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//11)
                            if 11 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//11)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line + "\n")
                            break    

                        # ViPER Clarity Value Normalization

                        if ("65580" in default_line):
                            # Normalizing to range of 0 - 9
                            input_line = input_line.split('"')
                            if 90 <= int(input_line[3]) : input_line[3] = str(int(input_line[3])//9)
                            if 9 < int(input_line[3]) : input_line[3] = str(int(input_line[3])//9)
                            input_line = '"'.join(input_line)
                            new_xml_file.write(input_line + "\n")
                            break 
                        
                        # Other Remaining Lines
                        new_xml_file.write(input_line + "\n")
                        break

                # Other Remaining Lines
                # Speaker Optimization
                else:
                    new_xml_file.write(default_line + "\n")
    
    # Printing Number of Remaining XML's to Process
    count-=1
    print("Remaining: ", count)
