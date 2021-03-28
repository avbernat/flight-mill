import csv

def trial_check(path1, path2):

    #***************************************************************************************
    #   Check to see that the ID and set number from the handwritten data matches the ID
    #   and set number of the recorded data of the flight trials.
    #***************************************************************************************

    match_dict = {}
    with open(path2, "r") as data2:
        reader = csv.DictReader(data2)
        for row in reader:
            ID = row["ID"]
            set_num = row["set_number"].lstrip("0")

            if (ID, set_num) not in match_dict:
                match_dict[(ID, set_num)] = ' '

    with open(path1, "r") as data1:
        reader = csv.DictReader(data1)
        for r in reader:
            ID_num = r["ID"]
            set_num = r["set_number"].lstrip("0")

            try:
                success = match_dict[(ID_num, set_num)]
            except KeyError:
                print("KeyError for ID, ", ID_num, " and set num, ", set_num)

    return match_dict
