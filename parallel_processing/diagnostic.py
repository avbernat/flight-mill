import os
import csv
import sys
import math
import time

import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt

from standardize_troughs import trough_standardization
from flight_analysis import time_list, speed_list, distance
from flight_analysis import blockPrint, enablePrint

def standardize(filepath, min_dev, max_dev, trough_standardization):

    #************************************************************************************************************
    #
    # Standardizes the voltage data for each channel by identifying large deviances in voltages as troughs.
    #
    # INPUT:    List of voltage values as floats.
    #
    # PROCESS:  Voltage values are rounded to two decimal places and appended to the volt_column. A confidence
    #           interval is defined around the mean voltage value using a low (min_dev) and high (max_dev)
    #           threshold. These values can be defined by the user according to the characteristics of the
    #           voltage recording data. Voltages at or higher than the min value of the confidence interval
    #           are set to 0 while voltages far below the min_value are set to 1 and identity the presence
    #           of a trough. Thus, a trough can be defined as any large deviance in voltage that is due to
    #           noise or chance. Finally, a list of troughs is created after compressing sequences of 
    #           trough-like identifiers into a single identifier (e.g. compressed sequences of 1s to a single
    #           1 to denote a trough).
    #
    #           Threshold values can be modified accordingly. They are labeled with a '*'. The default values
    #           are set to deliver a fine tune signal standardization.
    #
    # OUTPUT:   A list of time values as floats and a list of 1s and 0s where 1 designates the presence of a 
    #           trough and 0 designates no trough.
    #
    #************************************************************************************************************

    InputFile = open(filepath, mode="r", encoding='latin-1')
    Lines = InputFile.readlines()
    
    time_column = []
    voltage_column = []

    for i in range(0, len(Lines)):
        raw = Lines[i]
        a,b,c = raw.split(",") 
        time_column.append(float(a)) 
        voltage_column.append(float(b)) 

    InputFile.close()
    
    trough_column = trough_standardization(voltage_column, min_dev, max_dev) 

    return (time_column, trough_column)

def analyze(time_column, trough_column, time_list, speed_list, distance):

    time_channel = time_list(time_column, trough_column)
    speed_channel = speed_list(time_channel)
    time_n, speed_n, dist, av_speed = distance(time_channel, speed_channel)
    
    return (round(av_speed,2), round(dist,2))

def get_changes(file_name, dstat, statistic):

    chamber_ID = None
    dsmall_count = 0
    dlarge_count = 0

    if statistic == "trough" or statistic == "distance":
        if dstat > 0 and dstat < 25: # small change
            dsmall_count = 1
            stat = "trough" 

        if dstat >= 25: # large change
            chamber_ID = file_name.split("-")[-1].split(".")[0]
            dlarge_count = 1

    if statistic == "speed":
        if dstat > 0 and dstat < 0.1: # small change
            dsmall_count = 1
            stat = "trough" 

        if dstat >= 0.1: # large change
            chamber_ID = file_name.split("-")[-1].split(".")[0]
            dlarge_count = 1

    return dsmall_count, dlarge_count, chamber_ID

def heat_map(deviations, f, heat_map, axs, matrix, filename, bar_title):

    #************************************************************************************************************
    #
    # Generate heat maps to diagnose files with noise or overly-sensitive troughs, distances, and speeds.
    #
    # INPUT:    deviations as a list of floats, file number (f) as an int, the figure, and axs as a subplot, 
    #           matrix as a matrix of troughs, speeds, or distances that correspond to each deviation value
    #           combination, filename as a string, and bar_title as a string of the heat map title. 
    #
    # PROCESS:  Files with little noise and large troughs will be durable to small changes in deviations. Default
    #           here is to test and plot how changes in the min and max deviation values change the number of
    #           troughs; however, there is another threshold value - the x value threshold.
    #
    # OUTPUT:   Returns the difference between the highest and lowest trough, speed, or distance values, and 
    #           returns a single count if the file exhibited a difference. This count can be used to calculate 
    #           the number of files that exhibited a difference.
    #
    #************************************************************************************************************
    
    a = np.array(matrix)
    axs = axs.flatten()
    im = axs[f].imshow(a, cmap='viridis', interpolation='nearest') # cmap='hot'

    delta_stat = np.max(matrix)-np.min(matrix)

    new_f = 0
    if delta_stat > 0: # quick way to get rid of empty plots 
        new_f = 1 # start a new count 

    axs[f].title.set_text(filename + '\nMax-Min=%.2f' %delta_stat)
    axs[f].set_xticks(np.arange(len(deviations)))
    axs[f].set_yticks(np.arange(len(deviations)))
    axs[f].set_xticklabels(deviations, fontsize=8)
    axs[f].set_yticklabels(deviations, fontsize=8)
    axs[f].set_xlabel("Max Dev Val", fontsize=12)
    axs[f].set_ylabel("Min Dev Val", fontsize=12)

    cbar = heat_map.colorbar(im, ax=axs[f], fraction=0.046, pad=0.03)
    cbar.ax.set_ylabel(bar_title, rotation=-90, va="bottom")
    
    rows, cols = a.shape
    for i in range(rows):
        for j in range(cols):
            text = axs[f].text(j, i, a[i, j], ha="center", va="center", color="w", fontsize=6)

    return delta_stat, new_f

def diagnose(set_list, path, q1, q2, standardize=standardize, analyze=analyze, heat_map=heat_map, 
                    get_change=get_changes, blockPrint=blockPrint, enablePrint=enablePrint):

    small_troughs_count = 0
    large_troughs_count = 0
    small_speeds_count = 0
    large_speeds_count = 0
    small_dist_count = 0
    large_dist_count = 0

    large_chamber_troughs = []
    large_chamber_speeds = []
    large_chamber_dist = []

    # trough heat map
    rows = math.ceil(len(set_list) / 5) 
    fig, axes = plt.subplots(rows, 5, figsize=(20, 4*rows), facecolor='w', edgecolor='k')
    fig.tight_layout(pad=6.0)

    # speed and distance heat map
    r = rows * 2
    hmap, haxes = plt.subplots(r, 5, figsize=(20, 4*r), facecolor='w', edgecolor='k')
    hmap.tight_layout(pad=6.0)

    f=0
    h=0
    big_list =[]

    for file in set_list:
        
        start = time.time()

        file_path = path + str(file)
        set_n = file.split("_")[1].split("-")[0]
        file_abbrev = set_n + "-" + file.split("-")[-1]
        
        devs = [0.02, 0.04, 0.06, 0.08, 0.1]
        all_troughs = []
        all_speeds = []
        all_distances = []

        n_combos = len(devs)**2
        print(f"     Calculating...{file_abbrev}, {n_combos} troughs, speeds, and distances")

        for min_dev_val in devs:
            
            troughs = []
            speeds = []
            distances = []

            for max_dev_val in devs:
                
                (time_col, trough_col) = standardize(file_path, min_dev_val, max_dev_val, trough_standardization)
                
                blockPrint() # temp
                (avg_speed, total_dist) = analyze(time_col, trough_col, time_list, speed_list, distance)
                enablePrint() # temp
                
                troughs.append(sum(trough_col))
                speeds.append(avg_speed)
                distances.append(total_dist)

            all_troughs.append(troughs)
            all_speeds.append(speeds)
            all_distances.append(distances)
        
        delta_trough, nf = heat_map(devs, f, fig, axes, all_troughs, file, "Number of Troughs")
        f+=1
        delta_speed, nh = heat_map(devs, h, hmap, haxes, all_speeds, file, "Average Speed (m/s)")
        h+=1
        delta_dist, nh = heat_map(devs, h, hmap, haxes, all_distances, file, "Distance (m/s)")
        h+=1

        troughs_flat = sum(all_troughs, [])
        speeds_flat = sum(all_speeds, [])
        distances_flat = sum(all_distances, [])

        stat_dict = {"trough": troughs_flat, "speed": speeds_flat, "distance": distances_flat}
        stats = ["trough", "speed", "distance"]

        combo_list = []

        for stat in stats:
            row_combo = {}
            row_combo["stat"] = stat
            row_combo["filename"] = file_abbrev
            row_combo["set"] = set_n.split("t0")[-1]

            i = 0
            for val in stat_dict[stat]:
                i += 1
                row_combo[f"combo_{i}"] = val

            combo_list.append(row_combo)

        big_list.append(combo_list)

        dt_small, dt_large, ct_id = get_changes(file, delta_trough, "trough")
        ds_small, ds_large, cs_id = get_changes(file, delta_speed, "speed")
        dd_small, dd_large, cd_id = get_changes(file, delta_dist, "distance")

        total = f

        small_troughs_count += dt_small
        large_troughs_count += dt_large
        small_speeds_count += ds_small
        large_speeds_count += ds_large
        small_dist_count += dd_small
        large_dist_count += dd_large

        large_chamber_troughs.append(ct_id)
        large_chamber_speeds.append(cs_id)
        large_chamber_dist.append(cd_id)
        
        end = time.time()
        minutes = round((end - start)/60, 2)
        print(f"     Time elapsed: {minutes} min")

    no_change_troughs = total - (small_troughs_count + large_troughs_count)
    no_change_speeds = total - (small_speeds_count + large_speeds_count)
    no_change_dist = total - (small_dist_count + large_dist_count)

    large_prop_troughs = large_troughs_count / total
    large_prop_speeds = large_speeds_count / total
    large_prop_dist = large_dist_count / total

    d = {"trough": [no_change_troughs, small_troughs_count, large_troughs_count, large_prop_troughs, large_chamber_troughs, troughs_flat],
            "speed": [no_change_speeds, small_speeds_count, large_speeds_count, large_prop_speeds, large_chamber_speeds, speeds_flat],
            "distance": [no_change_dist, small_dist_count, large_dist_count, large_prop_dist, large_chamber_dist, distances_flat]}
    
    trows = []

    for stat in stats:
        
        row_data = {}

        row_data["stat"] = stat
        row_data["set"] = set_n.split("t0")[-1]
        row_data["total"] = total
        row_data["no_change"] = d[stat][0]
        row_data["small_changes"] = d[stat][1]
        row_data["large_changes"] = d[stat][2]
        row_data["large_prop"] = d[stat][3]
        row_data["large_cIDs"] = d[stat][4]

        trows.append(row_data)

    outpath = r"/home/avbernat/Desktop/diagnostics/"
    #outpath = r"/Users/anastasiabernat/Desktop/git_repositories/undergrad-collabs/max_speed/diagnostics/"
    #outpath = r"/Users/anastasiabernat/Desktop/"
    fig.savefig(outpath + f"trough_diagnostic-{set_n}.png")
    hmap.savefig(outpath + f"stats_diagnostics-{set_n}.png")

    #return rows
    q1.put(trows)
    q2.put(big_list)

def generate_set_lists(dir_list):
    
    # Rearranging the directory_list into list of files by set. 
    
    max_set_num = int(dir_list[-1].split("_")[1].split("-")[0].split("t0")[-1])

    sets = []
    for i in range(1, max_set_num + 1):
        if i < 10:
            s=f"00{i}"
        else:
            s=f"0{i}"
        set_name = f"set{s}"
        set_list = []
        for file in dir_list:
            if set_name in file:
                set_list.append(file)
        if set_list != []:
            sets.append(set_list)

    return sets

def write_summary_file(out_path, three_rows):

    with open(out_path + "diagnostics_summary.csv", "a+") as out_file: 
        writer = csv.DictWriter(out_file, fieldnames = three_rows[0].keys())
        if out_file.tell() == 0:
            writer.writeheader()
        for row in three_rows:
            writer.writerow(row)

def write_combos_file(out_path, combos):

    with open(out_path + "diagnostics_combos.csv", "a+") as out_file:
        writer = csv.DictWriter(out_file, fieldnames = combos[0][0].keys())
        if out_file.tell() == 0:
            writer.writeheader()
        for file in combos:
            for row in file:
                writer.writerow(row)

#************************************************************************************************************
#   To call the recording data file, write the complete file directory path below. An example path is
#   r"/Users/username/Desktop/Flight_scripts/". The number of columns processed below depends on the number
#   of channels used to record the flight data. For individual insects with only two columns per file,
#   only the TBF and voltage reading columns are processed. However, if the number of channels is different
#   the script needs to be edited accordingly.
#
#   Max number of items to population a Queue: 32767 items. (Stack Overflow: Multiprocessing Queue maxsize limit is 32767)
#************************************************************************************************************

if __name__ == "__main__":

    #main_path = r"/Users/anastasiabernat/Desktop/Dispersal/Trials-Winter2020/split_files/"
    main_path = r"/home/avbernat/Desktop/split_files/"
    path = main_path # + "small_test/"
    directory_list = sorted(os.listdir(path))
    sets = generate_set_lists(directory_list)

    #sets =sets[0:1]
    #set_number = 2
    #sets =[sets[set_number-1]] # or set_list?

    print("\nSet files: ", sets)
    count = sum([len(set_list) for set_list in sets])
    print("\nNumber of files: ", count)

    outpath = r"/home/avbernat/Desktop/diagnostics/"
    #outpath = r"/Users/anastasiabernat/Desktop/"
    with open(os.path.join(outpath, "diagnostics_summary.csv"), 'w') as file_out: 
        pass
    with open(os.path.join(outpath, "diagnostics_combos.csv"), 'w') as file_out: 
        pass

    qout = mp.Queue()
    qbig = mp.Queue()
    jobs = []
    for set_list in sets:
        set_num = set_list[0].split("_")[1].split("-")[0]
        print("\n", f"Job for {set_num} started!")
        p = mp.Process(target=diagnose, args=(set_list, path, qout, qbig))
        jobs.append(p)
        p.start()

    for process in jobs:
        set_rows = qout.get()
        set_combos = qbig.get()
        write_summary_file(outpath, set_rows)
        write_combos_file(outpath, set_combos)
        # process.join() # set 12 and 15 gets stuck in an infinite loop if uncomment
        # sys.stdout.flush() # https://stackoverflow.com/questions/10019456/usage-of-sys-stdout-flush-method
