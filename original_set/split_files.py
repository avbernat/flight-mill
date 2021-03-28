import csv
import os
import re

from datetime import datetime, timedelta

#*****************************************************************************************************
#
# Splitting recorded txt files based on event marker ID comments.
#
# Note: This file can be modified to split txt files on additional features such as the trial start
#       times or end times of each insect.
#
#*****************************************************************************************************

def define_dicts(datapath):
    
    #*****************************************************************************************************
    #
    # First, define dictionaries that will help map an insects' ID, set number, and channel letter
    # to its unique point of entry in a file.
    #
    # Input:    File path of data manually recorded during flight trials with the minimum following columns:
    #
    #                  ID:   the insect identification number (must match with the ID in the event marker)
    #               died?:   marked with a Y if an insect died before testing   
    #             chamber:   written as "A-n" or "B-n" where n is the channel number from 1-4
    #          set_number:   the recording set number formatted leading zeros (e.g. 001, 002)
    #
    # Process:  Assumes that no insect was tested twice in the same recording set. Uses DictReader
    #           to remap dictionary rows into two data-based dictionaries.  
    #
    # Output:   Two dictionaries. The first_flight_dict is used for the first 4 insects
    #           that enter the chamber (e.g. either chamber "A" or "B"), which have no
    #           event marker to designate them. Its keys are set_number, channel_letter,
    #           and channel_num and ID is its value. Per recording set, only the first 4
    #           insects for all eight channels are mapped in the dictionary.
    #
    #           The current_flight_dict holds the remaining insects that get swapped in and
    #           out of the chambers. Its keys are set_number, channel_letter, and ID, and the
    #           channel_num is its value. By later extracting the ID number from the event
    #           marker comment, the specific channel number can be accessed at the insect's
    #           unique point of entry, which is its unique row in the file.
    #
    #*****************************************************************************************************

    first_flight_dict = {}
    current_flight_dict = {}

    with open(datapath, "r") as data_file:
        reader = csv.DictReader(data_file)
        for row in reader:
            if row['died?'] == 'Y':
                continue
            
            ID = int(row['ID'])
            set_num = row['set_number'] 
            channel_letter = row['chamber'].split("-")[0] 
            channel_num = row['chamber'].split("-")[-1] 
            chamber = channel_letter + channel_num

            if (set_num, channel_letter, channel_num) not in first_flight_dict:
                first_flight_dict[(set_num, channel_letter, channel_num)] = ID
            if (set_num, channel_letter, ID) not in current_flight_dict:
                current_flight_dict[(set_num, channel_letter, ID)] = channel_num
            else:
                print('PROBLEM, BUG %s SHOWS UP AGAIN'%ID)
                
    return (first_flight_dict, current_flight_dict)

def map_IDs(path, outpath):
    
    #*****************************************************************************************************
    #
    # Map event marker IDs for an insect's channel number and its unique point of entry, or unique row in
    # a file.
    #
    # Input:    Txt file inpath and outpath. Input txt file has columns of the time from the beginning of
    #           the file (TBF), the voltage readings, date, time, and event marker information. Txt file
    #           also has at least the following in its filename: set_number and channel_letter. In this
    #           script, the code extracts information from this filename format: "T1_set006-2-24-2020-B.txt"
    #           where each sequence is the following,
    #
    #                  T1:   trial type number
    #              set006:   recording set number  formatted leading zeros to keep the files read in order 
    #           2-24-2020:   the date the recording occured 
    #                   B:   channel letter
    #
    #           *Lines 133-135 will need to be recoded for different filenames
    #
    # Process:  New dictionary rows are encoded that retain TBF, the voltages, the datetime, and the event
    #           number, but now include 4 new keys: channel1_bug, channel2_bug, channel3_bug, channel4_bug.
    #           The values in each new key are the IDs of the bug. To do this, an inplace dictionary called
    #           current_bugs is made. The ID in the event marker comment is extracted and used as one
    #           of the keys, along with keys set_number and channel_letter extracted from the filename,
    #           to access that bug's channel number. The 'new' bug then replaces the 'old' bug in the
    #           current bugs dict at its designated channel by reassigning ID values.
    #
    # Output:   A newly formatted file with 4 new columns of IDs that map out, based on the event marker,
    #           when bugs come in and out and to which channel.
    #
    #*****************************************************************************************************

    dir_list = sorted(os.listdir(path))

    header = ["TBF","1","2","3","4",
              "event_happened","event_num","buffer","date","time","event_marker"]

    for file in dir_list:
        if file.startswith("."):
            continue
        filepath = path + str(file)
        full_data = []
        before_first_event = True

        #***********************************************************************************************************
        #   Set the extraction of the set_number and channel_letter according to the filename on lines 133-135:
        #
        #   Use the split() function to split a string, in this case the filename, on any symbol.
        #   For example, if the filename is instead as simple as '6-B.txt' where 6 is the
        #   set number and B is the channel letter then the user can consider and write the following:
        #
        #   file.split("-")                     splits the filename into a list of ['6', 'B.txt']
        #   file.split("-")[0]                  extracts only '6', the value at the 0th index of list ['6', 'B.txt']
        #   file.split("-")[1]                  extracts 'B.txt', the value at the 1st index of list ['6', 'B.txt']
        #   file.split("-")[1].split(".")       splits the string into a list of ['B', 'txt']
        #   file.split("-")[1].split(".")[0]    extracts only 'B', the value at the 0th index of list ['B', 'txt']
        #
        #   This is not the only way to extract the set number or channel letter, but it is a example template. 
        #
        #***********************************************************************************************************
        
        set_num = file.split('-')[0][6:] 
        set_number = set_num.lstrip("0")
        channel_letter = file.split('.')[0][-1]
        
        print(file + "--------------------------------")
        
        with open(filepath, 'r', encoding='latin') as input_file:
            reader = csv.DictReader(input_file, delimiter = ',', fieldnames=header)
            for row in reader:
                if row['TBF'].startswith("Samples per sec."):
                    continue
                if (int(float(row['event_num'])) == 1) and (int(float(row['event_happened'])) == 3): # false event marker
                    row['event_num'] = '0'
                    row['event_happened'] = '0'
                
                new_row = {}
                new_row['TBF'] = row['TBF']
                new_row['channel1_voltage'] = row['1']
                new_row['channel2_voltage'] = row['2']
                new_row['channel3_voltage'] = row['3']
                new_row['channel4_voltage'] = row['4']
                new_row['event_num'] = row['event_num']
                
                datetime_str = row['date'] + ' ' + row['time']
                datetime_object = datetime.strptime(datetime_str,'%m-%d-%y %H:%M:%S')  
                new_row['datetime'] = datetime_object
                
                

                if before_first_event:

                    current_bugs = {'channel1': first_flight_dict[(set_num,channel_letter,'1')],
                                    'channel2': first_flight_dict[(set_num,channel_letter,'2')],
                                    'channel3': first_flight_dict[(set_num,channel_letter,'3')],
                                    'channel4': first_flight_dict[(set_num,channel_letter,'4')]}

                    before_first_event = False

                elif (not before_first_event) and (int(float(row['event_num'])) != 0):
                    if row["event_marker"] == '' or row["event_marker"] == None:
                        continue
                    new_bug = int(re.search(r'\d+', row['event_marker']).group())
                    new_channel = current_flight_dict[(set_num, channel_letter, new_bug)]

                    event_number = int(row['event_num']) - 1  # removes false first event marker count
                    new_row['event_num'] = event_number
                    print('     Event Marker %s:'%(event_number),
                          ' new bug %s replacing old bug %s at channel %s'%(new_bug,
                                                                            current_bugs['channel%s'%new_channel],
                                                                            new_channel))
                    current_bugs['channel%s'%new_channel] = new_bug
                
                new_row['channel1_bug'] = current_bugs['channel1']
                new_row['channel2_bug'] = current_bugs['channel2']
                new_row['channel3_bug'] = current_bugs['channel3']
                new_row['channel4_bug'] = current_bugs['channel4']

                full_data.append(new_row)
                
        with open(outpath + file,"w") as output_file:
            writer = csv.DictWriter(output_file, delimiter=',', fieldnames=new_row.keys())
            for r in full_data:
                writer.writerow(r)

def split_files(path, outpath):
    
    #*****************************************************************************************************
    #
    # Split files according to ID.
    #
    # Input:    The newly formatted txt file with 4 new columns of intermittent ID numbers.
    #
    # Process:  New dictionary rows are encoded that retain the TBF, voltages specific to the channel
    #           number the insect flew in, and the datetime. These dictionary rows become the data
    #           values of the ID_data dict where the keys are the IDs. Looping through the items in
    #           this embedded dictionary, each key value or insect ID gets written into its own txt
    #           file with the rows specific to its flight trial.
    #
    #           * Here as well, lines 232 and 233 will need to be recoded for different filenames.
    #
    # Output:   New txt files. the filename contains additional information now: the insect ID number
    #           located at the end of the filename as well as its chamber name (e.g. "B1", "A3", etc.).
    #           The file istelf contains the TBF and voltage readings rows specific to when the bug
    #           entered and left the flight mill chamber.
    #
    #*****************************************************************************************************         

    dir_files = sorted(os.listdir(path))

    col_names = ["TBF","1","2","3","4", "event_num", "datetime",
                 "chn1_ID","chn2_ID","chn3_ID","chn4_ID"]

    for f in dir_files:
        if f.startswith("."):
            continue
        
        filepath = path + str(f)
        
        # Set the extraction of the set_num and channel_letter according to filename in lines 232-233:
        set_num = f.split('-')[0][6:]
        channel_letter = f.split('.')[0][-1]
        
        print("File splitting: " + f + "--------------------------------")

        for channel in range(1,5):
            ID_data = {}
            with open(filepath, "r") as input_file:
                reader = csv.DictReader(input_file,fieldnames=col_names)
                for row in reader:
                    ID = row['chn' + str(channel) + '_ID']

                    new_row = {}
                    new_row['TBF'] = row['TBF']
                    new_row['voltage'] = row[str(channel)]
                    new_row['datetime'] = row['datetime']

                    if ID not in ID_data:
                        ID_data[ID] = []
                    ID_data[ID].append(new_row)
        
            for key_ID, data in ID_data.items():
                print("     Making file for ID, " + str(key_ID))
                with open(outpath + f.split(".")[0] + str(channel) + \
                          '_' + str(key_ID) + ".txt","w") as output_file:
                    writer = csv.DictWriter(output_file, fieldnames=new_row.keys())
                    for r in data:
                        writer.writerow(r)


#*****************************************************************************************************
#   Write file main path down below. An example path is r"/Users/username/Desktop/Flight_scripts/".
#*****************************************************************************************************

main_path = # input the path to the Flight_scripts directory here 

# Defining dictionaries:
datafile = main_path + "data/datasheet.csv"
first_flight_dict, current_flight_dict = define_dicts(datafile)

# Mapping event marker IDs:
txt_inpath = main_path + "recordings/"
txt_outpath = main_path + "files2split/"
map_IDs(txt_inpath, txt_outpath) 

# Splitting files by ID:
split_inpath = main_path + "files2split/"
split_outpath = main_path + "split_files/"
split_files(split_inpath, split_outpath)
