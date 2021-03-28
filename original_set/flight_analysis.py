import os
import sys
import csv

import time
start = time.time()

#**********************************************************************************************
# Call blockPrint() before function to disable print statements. Call enableprint() when want
# print statements to continue.To disable all printing, start blocking at the top of the file
#**********************************************************************************************

def blockPrint():
    sys.stdout = open(os.devnull, 'w')

def enablePrint():
    sys.stdout = sys.__stdout__

def time_list(time, channel):
    
    #***************************************************************************************************************************
    #
    # Identify times of trough occurances.
    #
    # INPUT:    A channel as a list of floats where 1.00 indicates a trough and 0.00 no trough; time as a list of floats of TBF.
    #
    # OUTPUT:   A time list of when each trough event occurs.
    #
    #***************************************************************************************************************************

    time_channel=[]
    for i in range(0, len(channel)):
        if float(channel[i]) == 1.00:
            time_channel.append(float(time[i]))

    return time_channel

def speed_list(time, circ_flight_path):
    
    #***************************************************************************************************************************
    #
    # Calculate flight speed between troughs.
    #
    # INPUT:    A time list of when trough event occurs, time; a float of the circular flight path distance covered by
    #           the insect, circ_flight_path.
    #
    # PROCESS:  For instances where more than 2 flight events occured, the flight speed in m/s is calculated between the trough
    #           events. This calculation depends on the mill's arm radius (i.e. the distance between the tethered insect
    #           and the rotational pivot) choosen by the user. 
    #
    #           Moreover, due to the low friction of the magnetic bearing, the mill's arm stops rotating some time after the
    #           insect ends its flying bout. This function includes an optional speed correction loop to account for these
    #           additional rotations. It does so by using a threshold speed value which sets those additional rotations to zero.
    #           The threshold speed value needs to be choosen with care when working with slow flying insects.
    #   
    #           Finally, this function automatically accounts for unused or empty channels and for instances in which only one
    #           flight event occurred.
    #
    # OUTPUT:   A list of speed values as floats.
    #
    #***************************************************************************************************************************

    speed_t=0
    speed_channel=[]
    speed_channel.append(0)
    
    if len(time) > 0:
        if len(time) > 2:
            for i in range(1, len(time)):
                if float(time[i]) != float(time[i-1]):
                    speed_t = circ_flight_path/(float(time[i]) - float(time[i-1]))
                    speed_channel.append(float(speed_t))
                else:
                    speed_channel.append(9999) 
            
            for x in range(0, len(speed_channel)): # Optional speed correction.
                if float(speed_channel[x]) < 0.1: 
                    speed_channel[x] = 0

        else:
            print ("Has only one peak - impossible to calculate motion stats")
    else:
        print ("Channel is empty")
        
    return speed_channel


def distance(time, speed, circ_flight_path):
    
    #***************************************************************************************************************************
    #
    # Calculate flight distance and average speed.
    #
    # INPUT:    A list of times and a list of speeds as floats.   
    #
    # PROCESS:  First, the function corrects for false readings in the voltage signal by filtering out speed values higher than
    #           1.4 m/s and negative speed values. These threshold values can be modified by the user to account for very slow
    #           or very fast flying insects to create a more fine-tuned threshold. Then, for every iteration in the speed list,
    #           the circular distance in which an insect traveled is incrementally added to a running sum.
    #
    #           Then, the following loop filters out long gaps (greater than 7s in this example) that occur between two
    #           consecutive flying bouts. This gap value can also be modified by the user.
    #
    #           Finally, the average speed is calculated.
    #
    # OUTPUT:   The fully filtered time lists and speed lists, the total distance the insect traveled during its flight trial,
    #           and the average flight speed.
    #
    #***************************************************************************************************************************

    distance=0
    average_speed=0
    time_new=[]
    speed_new=[]
    time_final=[]
    speed_final=[]

    if len(time) > 2:
        
        for i in range(1, len(speed)):
            if float(speed[i]) > 0 and float(speed[i]) < 1.4: # Modify the threshold value accordingly
                time_new.append(float(time[i]))
                speed_new.append(float(speed[i]))
                distance += circ_flight_path

        if len(time_new) > 2:
            time_final.append(time_new[0])
            speed_final.append(speed_new[0])
            for j in range(0, len(time_new)-1):
                if float(time_new[j+1]) - float(time_new[j]) <= 7: # The gap value can be changed accordingly
                    time_final.append(time_new[j+1])
                    speed_final.append(speed_new[j+1])
            average_speed = sum(speed_final)/len(speed_final)
            
        else:
            print('Cannot calculate distance and average speed')
    else:
        print('Cannot calculate distance and average speed')
        
    return (time_final, speed_final, distance, average_speed)  

  
def recording_duration(file_path):
    
    #***************************************************************************************************************************
    #
    # Calculates the duration of the recording.
    #
    # INPUT:    File path as a string.
    #
    # PROCESS:  The function reads all the data, splits the data out as a list of strings (each string is a row), retrieves
    #           the last line of the data, and gets the first element in the list of strings, which is the recording duration.
    #
    # OUTPUT:   The file's recording duration as a float.
    #
    #***************************************************************************************************************************
  
    with open(file_path, "r") as txtfile:
        data = txtfile.readlines()         
        tot_duration = float(data[-1].split(",")[0]) - float(data[0].split(",")[0])

    return tot_duration


def flying_bouts(time, speed, recording_duration):
    
    #***************************************************************************************************************************
    #
    # Calculates flight bout lengths in seconds and percentage of time spent flying over recording duration.
    #
    # INPUT:    Fltered time and speed lists as well as the total duration of the flight recording.
    #
    # PROCESS:  Part 1. The time difference between troughs are assessed. If the difference between the second and the first
    #           times are less than 20 seconds, then the first time value is stored in the bout_time list because it indicates
    #           the start of the first bout. However, if they are more than 20 seconds then each time is a different bout
    #           and their differences are evaluated like all other time differences. Thus, any consecutive time gap that
    #           is greater than 20 seconds will have both values are appended to bout_time where the the earlier value
    #           indicates the end of one bout and the later value indicates the beginning of new bout. The last time value
    #           is also stored in bout_time in order to store the end time value of the last bout.
    #
    #           Part 2. To calculate the bout durations, the even index values are subtracted by the odd index values of the
    #           bout_list since they indicate the final and initial times of the bout. Then, the total time spent flying is
    #           calculated by taking the sum of the bout durations. The total percentage spent flying is also calculated as
    #           well as the longest bout. Finally, a series of specific duration ranges are use to calculate the number of
    #           bout events, the percentage of total flight time, and the total duration within the range. Below, the bout
    #           durations were set at ranges 60-300s, 300-900s, 900-3600s, 3600-14400s and >14400s.
    #
    # OUTPUT:   Returns all flight statistics calculated in Part 2.
    #
    #***************************************************************************************************************************
    
    bout_time = [] 
    
    t_odd = []
    t_even = []
    bout_durations = [] 
    
    last_time = 0
    diff = 0
    flight_time = 0
    longest_bout = 0
    shortest_bout = 0
    
    
    fly_time=0 
    flight_60_300=[]
    sum_60_300=0
    flight_300_900=[]
    sum_300_900=0
    flight_900_3600=[]
    sum_900_3600=0
    flight_3600_14400=[]
    sum_3600_14400=0
    flight_14400=[]
    
    sum_14400=0
    events_300=0
    events_900=0
    events_3600=0
    events_14400=0
    events_more_14400=0

    if len(time) > 2:
        
        #*********************************************************************************
        # Part 1. Identifying and storing the beginning and end time values of each bout.
        #*********************************************************************************

        if float(time[1]) - float(time[0]) < 20: 
            bout_time.append(time[0])

        for i in range(0, len(time)-1):
            if float(time[i+1]) - float(time[i]) >= 20: 
                bout_time.append(time[i])
                bout_time.append(time[i+1])
     
        if bout_time[-1] != time[-1]:
            bout_time.append(time[-1])

        for t in range(1, len(bout_time)):
            bout_time = sorted(list(set(bout_time))) # set() removes redundant values

        #*********************************************************************************
        # Part 2: Calculates the flight descriptive statistics.
        #*********************************************************************************

        if len(bout_time)%2 != 0: 
            last_time = float(bout_time[-1])
            del bout_time[-1]

        t_odd = bout_time[0::2] 
        t_even = bout_time[1::2] 
        for j in range(0, len(t_odd)):
            diff = float(t_even[j]) - float(t_odd[j])
            bout_durations.append(diff) 

        if float(last_time) != 0: 
            diff = float(last_time) - float(t_even[-1])
            bout_durations.append(diff)

        flight_time = sum(float(i) for i in bout_durations)
        fly_time = flight_time/recording_duration
        longest_bout = max(bout_durations)
                
        for k in range(0, len(bout_durations)): 
            if float(bout_durations[k])>60 and float(bout_durations[k])<=300:
                flight_60_300.append(float(bout_durations[k])/flight_time)
            elif float(bout_durations[k])>300 and float(bout_durations[k])<=900:
                flight_300_900.append(float(bout_durations[k])/flight_time)
            elif float(bout_durations[k])>900 and float(bout_durations[k])<=3600:
                flight_900_3600.append(float(bout_durations[k])/flight_time)
            elif float(bout_durations[k])>3600 and float(bout_durations[k])<=14400:
                flight_3600_14400.append(float(bout_durations[k])/flight_time)
            elif float(bout_durations[k])>14400:
                flight_14400.append(float(bout_durations[k])/flight_time)
                
        if len(flight_60_300) > 0:
            sum_60_300=sum(float(a) for a in flight_60_300)
            shortest_bout = float(min(flight_60_300))*flight_time
        if len(flight_300_900) > 0:
            sum_300_900=sum(float(b) for b in flight_300_900)
        if len(flight_900_3600) > 0:
            sum_900_3600=sum(float(c) for c in flight_900_3600)
        if len(flight_3600_14400) > 0:
            sum_3600_14400=sum(float(d) for d in flight_3600_14400)
        if len(flight_14400) > 0:
            sum_14400=sum(float(e) for e in flight_14400)
            
        events_300=len(flight_60_300)
        events_900=len(flight_300_900)
        events_3600=len(flight_900_3600)
        events_14400=len(flight_3600_14400)
        events_more_14400=len(flight_14400)
        
    else:
        print('Channel has only one peak - cannot perform calculation')

    return (flight_time, shortest_bout, longest_bout, fly_time,
            sum_60_300, sum_300_900, sum_900_3600, sum_3600_14400, sum_14400,
            events_300, events_900, events_3600, events_14400, events_more_14400)       


def graph(time, speed):
    
    #**********************************************************************************************
    #
    # Cleans up the final time and speed variation file in order to produce clearer graphs.
    #
    # INPUT:    Lists of time and speed as floats.
    #
    # PROCESS:  Between bouts, new time, speed data points are added to represent that the insect 
    #           stopped flying. These data points are a time value that is one second later than
    #           the last time value of the bout and a speed value of 0 m/s. Finally, each list
    #           ends with a time value of 0 and speed of 0.
    #
    # OUTPUT:   Lists of time and speed as floats, but with time and speed values between bouts 
    #           that drop to speeds of zero. This makes plotting the speed vs. time flight
    #           trajectories of the insects clearer.
    #
    #**********************************************************************************************

    time_new=[]
    speed_new=[]
    x=0
    y=0
    for i in range(0, len(time)-1):
        if float(time[i+1]) - float(time[i]) > 20:
            time_new.append(time[i])
            speed_new.append(speed[i])
            x=float(time[i]) + 1
            time_new.append(x)
            speed_new.append(0)
            y=float(time[i+1]) -1
            time_new.append(y)
            speed_new.append(0)
        else:
            time_new.append(time[i])
            speed_new.append(speed[i])
    time_new.append(0)
    speed_new.append(0)
    
    return time_new, speed_new

#************************************************************************************************************
# Call the flight data files by defining the filepath folder.
# An example path is r"/Users/username/Desktop/Flight_scripts/". Set the flight arm radius and define the
# time and distance SI units as strings.
#************************************************************************************************************

main_path = # input the path to the Flight_scripts directory here 
path = main_path + "/standardized_files/"

arm_radius = # input the radius length of the fligh mill radius arm here
flight_path = 2 * 3.1415 * arm_radius

# SI units
distance_units = # identify SI distance units as a string here (e.g. 'm', 'cm', 'mm')
time_units = # identify SI time units as a string here (e.g. 's', 'min', 'hrs')
speed_units = distance_units + '/' + time_units

print(path, "\n")

big_list=[]

dir_list = sorted(os.listdir(path))
for file in dir_list:

    filepath = path + str(file)
    tot_duration = recording_duration(filepath)

    input_file = open(filepath, mode="r")
    data_list = list(input_file)
    
    time_column = []
    trough_column = []
    
    for i in range(0, len(data_list)):
        raw = data_list[i]
        a,b = raw.split(",") 
        time_column.append(a)
        trough_column.append(b)
     
    input_file.close()

    output_data = []
    row_data = {}

    # Filename String Manipulation: Channel Letters, Channel Numbers, and IDs
    
    ID = str(file).split("_")[-1].split(".")[0]
    filename = str(file).split("_")[2] + "_" + ID + '.txt'
    trial_type = str(file).split("_")[1]
    channel_chamber = file.split("-")[-1].split("_")[0]
    channel_letter = channel_chamber[0]
    channel_num = channel_chamber[1]
    channel_chamber = channel_letter + "-" + channel_num
    set_number = file.split("_")[2].split("-")[0].split("t0")[-1]

    row_data["ID"] = ID
    row_data['filename'] = filename
    row_data['trial_type'] = trial_type
    row_data["chamber"] = channel_chamber
    row_data["channel_letter"] = channel_letter
    row_data["channel_num"] = channel_num
    row_data["set_number"] = set_number

    # Flight Stats and Print Statements
    
    print("ID: ", ID)     
    print('CHAMBER ' + channel_chamber + ' -------------------------------------------')
    
    time_channel = time_list(time_column, trough_column)
    speed_channel = speed_list(time_channel, flight_path)
    time_n, speed_n, dist, av_speed = distance(time_channel, speed_channel, flight_path)
    
    fly_time, short_bout, long_bout, flight, fly_to_300, fly_to_900,  \
        fly_to_3600, fly_to_14400, fly_more_14400, event_300, event_900, event_3600, \
        event_14400, event_more_14400 = flying_bouts(time_n, speed_n, tot_duration)
    
    print('Average speed (%s) -> ' %speed_units + '%.2f' % av_speed)
    print('Total flight time (%s) -> ' %time_units + '%.2f' % fly_time)
    print('Distance (%s) -> ' %distance_units + '%.2f' % dist)
    print('Shortest flying bout (%s) -> ' %time_units + '%.2f' % short_bout)
    print('Longest flying bout (%s) -> ' %time_units + '%.2f' %long_bout)
    print('This individual spent ' + '%.3f' %flight + ' of its time flying with this composition: ')
    print('  60s-300s = ' + '%.3f' %fly_to_300 + ' with ',event_300, 'events')
    print('  300s-900s = ' + '%.3f' %fly_to_900 + ' with ',event_900, 'events')
    print('  900s-3600s = ' + '%.3f' %fly_to_3600 + ' with ',event_3600, 'events')
    print('  3600s-14400s = ' + '%.3f' %fly_to_14400 + ' with ',event_14400, 'events')
    print('  +14400s = ' + '%.3f' %fly_more_14400 + ' with ',event_more_14400, 'events')
    print('\n')
    
    time_graph, speed_graph = graph(time_n, speed_n)

    row_data['average_speed'] = round(av_speed, 2)
    row_data['total_flight_time'] = round(fly_time, 2)
    row_data['distance'] = round(dist,2)
    row_data['shortest_flying_bout'] = round(short_bout, 2)      
    row_data['longest_flying_bout'] = round(long_bout, 2)        
    row_data['portion_flying'] = round(flight, 2)
    row_data['recording_duration'] = round(tot_duration, 2)
    row_data['max_speed'] = round(max(speed_graph), 2)
                
    big_list.append(row_data)
        
# All Flight Stats Summary File

outpath = main_path + "/data/"
with open(outpath + "flight_stats_summary.csv", "w") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames = big_list[1].keys())
    writer.writeheader()
    for row in big_list:
        writer.writerow(row)

#**********************************************************************************************
# Time it takes to execute the code.
#**********************************************************************************************

end = time.time()

print("---",(end - start), "seconds ---")
print("---",(end - start) / 60, "mintues ---")

#**********************************************************************************************
# This file has been modified from Attisano et al. 2015.
#**********************************************************************************************
