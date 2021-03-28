import os
import csv
import re
import pandas as pd
import numpy as np

from KeyError_checks import trial_check
from datetime import datetime, date

#************************************************************************************************************
# Merging 5 datasets together using csv.DictReader and pandas.
#************************************************************************************************************

#***************************************************************************************
#
#   MERGE 1. Demographics data (e.g. long, lat, sex, host, site) with trial data
#            (handwritten recordings).
#   
#   PROCESS: First, input the paths to each CSV file. Then, county_dict is written out
#            as a dictionary where population is the key and the county the bugs were
#            collected is the value.
#            Next, the demographics csv file is opened and read in order to store its
#            demographics information in two dictionaries. Finally, the trial csv file
#            is opened and extracts the demographics data from the dictionaries and
#            combines the information into a single csv file.
#
#***************************************************************************************

main_path = r"/Users/anastasiabernat/Desktop/git_repositories/undergrad-collabs/max_speed/data/"
demographics_data = main_path + "1.demographic_data.csv"
trial_data = main_path + "1.trials-time-processed-Dec10.2020.csv"
                
county_dict = {"Gainesville": "Alachua",
               "Homestead": "Miami-Dade",
               "Key Largo": "Key Largo",
               "Lake Placid": "Highlands",
               "Lake Wales": "Polk",
               "Leesburg": "Lake",
               "North Key Largo": "North Key Largo",
               "Plantation Key": "Plantation Key"}

pop_dict = {} # this dictionary is used during egg data merging | 447 ID missed - no pop
demo_dict = {}

with open(demographics_data, "r") as demo_data:
    reader = csv.DictReader(demo_data)
    for row in reader:
        ID = row["ID"]
        sex = row["sex"]
        pop = row["population"]
        site = row["site"]
        host = row["host_plant"]
        lat = row["latitude"]
        long = row["longitude"]

        if ID not in pop_dict:
            pop_dict[ID] = pop
        if (ID, pop) not in demo_dict:
            demo_dict[(ID,pop)] = [sex, site, host, lat, long]

full_data = [] 
with open(trial_data, "r") as trials:
    reader = csv.DictReader(trials)
    for r in reader:
        if r["died?"] == 'Y' or r["NOTES"].startswith("BUG: short"):
            continue

        row_data = {}
        ID_num = r["ID"]
        population = r["population"]

        # Extract Demographic Data
        try:
            demographics = demo_dict[(ID_num, population)]
            sex, site, host_plant, lat, long = demographics[0], demographics[1], demographics[2], \
                                               demographics[3], demographics[4]
            
            county = county_dict[population]
            
        except KeyError:
            print("KeyError for ID, ", ID_num)
            continue

        row_data["ID"] = ID_num
        row_data["set_number"] = r["set_number"]
        row_data["chamber"] = r["chamber"]
        row_data["test_date"] = r["test_date"]

        # Time Calculations to Check Total Duration
        row_data["time_start"] = r["time_start"]
        row_data["time_end"] = r["time_end"]
        
        t_start_str = r['time_start']
        t_end_str = r['time_end']
        t_start_obj = datetime.strptime(t_start_str , '%H:%M:%S').time()
        t_end_obj = datetime.strptime(t_end_str , '%H:%M:%S').time()

        duration = (datetime.combine(date.min, t_end_obj) -
                    datetime.combine(date.min, t_start_obj)).total_seconds()

        row_data["duration_check"] = duration

        # Rest of the Trial Data
        row_data["sex"] = sex
        row_data["population"] = population
        row_data["county"] = county
        row_data["site"] = site
        row_data["host_plant"] = host_plant
        row_data["flew"] = r["flew"]
        row_data["flight_type"] = r["flight_type"]
        row_data["NOTES"] = r["NOTES"]
        row_data["mass"] = r["mass"]
        row_data["EWM"] = r["eggs"]
        row_data["trial_type"] = r["trial_type"]
        row_data["latitude"] = lat
        row_data["longitude"] = long

        full_data.append(row_data)

outpath = main_path + "2.trial-demographics.csv"

with open(outpath, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = row_data.keys())
    writer.writeheader()
    for r in full_data:
        writer.writerow(r)

#***************************************************************************************
#
#   MERGE 2. Trial-demographics data with flight-stats data.
#
#   PROCESS: Using the KeyError_check function imported at the top of the file, check
#            to see that the ID and set from the handwritten data matches the ID
#            and set of the recorded data. If so, then do an inner merge the data based
#            on ID, set number, trial_type, and chamber.
#
#***************************************************************************************

path1 = main_path + "2.trial-demographics.csv"
path1copy = main_path + "2.trial-demographics.csv"
path2 = main_path + "2.flight_stats_summary.csv"

df_trial_demo = pd.read_csv(path1, parse_dates = ['test_date'])
df_analyses = pd.read_csv(path2)

bugs_tested_dict = trial_check(path1, path2)         
    
stats_data = pd.merge(left=df_analyses, right=df_trial_demo,
                       left_on=['ID', 'set_number', 'trial_type', 'chamber'],
                       right_on=['ID', 'set_number', 'trial_type', 'chamber'],
                       how='inner')

#***************************************************************************************
#
#   MERGE 3. Stats data with egg data.
#
#   PROCESS: Grouped individual recordings of egg count by ID in order to get the total
#            number of eggs laid by a female bug during the entire experiment. Total egg
#            count is then grouped with the original egg datasheet. Finally, the egg
#            datasheet is merged with the rest of the flight statistics data.
#
#***************************************************************************************

egg_data = main_path + "3.egg_data-initial.csv"

egg_df = pd.read_csv(egg_data, parse_dates = ['date_collected'])
egg_df_sums = egg_df.groupby('ID')['eggs'].sum().reset_index()
egg_df_sums.rename(columns={'eggs':'total_eggs'}, inplace=True)
                                 
eggs = pd.merge(left=egg_df, right=egg_df_sums, left_on=['ID'], right_on=['ID'], how='left')
eggs['ID'] = eggs['ID'].apply(str)
eggs['pop'] = eggs['ID'].map(pop_dict)

egg_outpath = main_path + "3.egg_data-final.csv"
eggs.to_csv(egg_outpath, index=False, mode='w')

merged_data = pd.merge(left=stats_data, right=egg_df_sums, left_on=['ID'],
                       right_on=['ID'], how='left')

outpath = main_path + "4.main_data.csv"
merged_data.to_csv(outpath, index=False, mode='w')

#***************************************************************************************
#
#   MERGE 4. Egg-stats-demographics data with morphology data.
#
#   PROCESS: Store morphology measurements and sex recordings in dictionaries. Check to
#            see that the sexes typed on the flight trials datasheet matches the more
#            accurate sex recording from the morphology measurements. Merge and adjust
#            the morphology and sex data with the eggs-stats-demographics data. 
#
#***************************************************************************************

morphology_data = main_path + "4.tested-morph.csv"
main_data = main_path + "4.main_data.csv"

check_sex_dict = {} # Check if ID and sex match
update_sex_dict = {} 
morph_measurements = {}

with open(morphology_data, "r") as morph_data:
    reader = csv.DictReader(morph_data)
    for row in reader:
        ID = row["ID"]
        sex = row["sex"]
        pop = row["population"]
        
        beak = row["beak"]
        thorax = row["thorax"]
        wing = row["wing"]
        body = row["body"]
        w_morph = row["w_morph"]
        morph_notes = row["notes"]

        if (ID, sex) not in check_sex_dict:
            check_sex_dict[(ID, sex)] = pop
        if ID not in update_sex_dict:
            update_sex_dict[ID] = sex
        if (ID, pop) not in morph_measurements:
            morph_measurements[(ID,pop)] = [beak, thorax, wing, body, w_morph, morph_notes]
            
full_data = [] 
with open(main_data, "r") as main_data:
    reader = csv.DictReader(main_data)
    for r in reader:
        ID_num = r["ID"]
        population = r["population"]
        sex = r["sex"]
        pop = re.sub('[^A-Z]', '', population)
        if pop == "G":
            pop = "GV"
        if pop == "H":
            pop = "HS"
        if pop == "L":
            pop = "LB"
        
        try:
            pop = check_sex_dict[(ID_num, sex)]
        except KeyError:
            print("KeyError for ID, ", ID_num, "   wrong sex or no sex recorded in the trials datasheet")
            print("     Old sex: ", sex)
            sex = update_sex_dict[ID]
            print("     New sex: ", sex)

        r["sex"] = sex
        
        try:
            r["beak"] = morph_measurements[(ID_num,pop)][0]
            r["thorax"] = morph_measurements[(ID_num,pop)][1]
            r["wing"] = morph_measurements[(ID_num,pop)][2]
            r["body"] = morph_measurements[(ID_num,pop)][3]
            r["w_morph"] = morph_measurements[(ID_num,pop)][4]
            r["morph_notes"] = morph_measurements[(ID_num,pop)][-1]
        except KeyError:
            print("KeyError for ID and pop, ", ID_num, pop)
            r["beak"] = ''
            r["thorax"] = ''
            r["wing"] = ''
            r["body"] = ''
            r["w_morph"] = ''
            r["morph_notes"] = 'missing tube'           

        full_data.append(r)

outpath = main_path + "5.complete_flight_data.csv"

with open(outpath, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = r.keys())
    writer.writeheader()
    for r in full_data:
        writer.writerow(r)

#***************************************************************************************
#
#   MERGE 5. Tested bugs with non-tested bugs.
#
#   PROCESS: All the short-wing bugs were not flight tested, but we can still add their
#            morpholgy data to to tested data. To do so, a vertical merge is encoded and
#            a new column is created that marks whether the bug has been tested or not.
#
#***************************************************************************************

tested_data = main_path + "5.complete_flight_data.csv"
nontested_data = main_path + "5.not_tested-morph.csv"

df_tested = pd.read_csv(tested_data)
df_nontested = pd.read_csv(nontested_data)
df_nontested = df_nontested.drop(['month', 'year', 'months_since_start',
                                  'season', 'diapause', 'field_date_collected',
                                  'date_measured', 'date_recorded'], axis=1)

vertical_merge = pd.concat([df_tested, df_nontested.rename(
                                    columns={'pophost':'host_plant',
                                             'lat': 'latitude',
                                             'long': 'longitude',
                                             'notes': 'morph_notes'})],
                                               sort=True,
                                               ignore_index=True)


col_names_order = list(df_tested.columns)
vertical_merge = vertical_merge[col_names_order]
vertical_merge['tested'] = np.where(vertical_merge['ID'] > 0, 'yes', 'no')

vertical_merge['ID'] = np.where(vertical_merge['ID'] > 0,
                                vertical_merge['ID'], 0).astype(int)
vertical_merge[('channel_num')] = np.where(vertical_merge['channel_num'] > 0,
                                vertical_merge[('channel_num')], 0).astype(int)
vertical_merge[('set_number')] = np.where(vertical_merge['set_number'] > 0,
                                vertical_merge[('set_number')], 0).astype(int)


flight_outpath = main_path + "all_flight_data.csv"
vertical_merge.to_csv(flight_outpath, index=False, mode='w')
