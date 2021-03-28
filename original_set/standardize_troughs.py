import os
import math
import numpy as np
import matplotlib.pyplot as plt

def trough_standardization(column, dev_min, dev_max, sample_rate):
    
    #************************************************************************************************************
    #
    # Standardizes the voltage data for each channel by identifying large deviances in voltages as troughs.
    #
    # INPUT:    List of voltage values as floats, the minimum deviation value as a float, the maximum deviation
    #           value as a float, and the sampling rate (S/s) as an integer.
    #
    # PROCESS:  Voltage values are rounded to two decimal places and appended to the volt_column. A confidence
    #           interval is defined aroudn the mean voltage value using a low (min_value) and high (max_value)
    #           threshold. These values can be defined by the user according to the characteristics of the
    #           voltage recording data. Voltages at or higher than the min value of the confidence interval
    #           are set to 0 while voltages far below the min_value are set to 1 and identity the presence
    #           of a trough. Thus, a trough can be defined as any large deviance in voltage that is due to
    #           noise or chance. Finally, double troughs are corrected (see below) and a list of troughs is 
    #           created after compressing sequences of trough-like identifiers into a single identifier 
    #           (e.g. compressed sequences of 1s to a single 1 to denote a trough).
    #
    #           Threshold values can be modified accordingly. They are labeled with a '*'. The default values
    #           are set to deliver a fine tune signal standardization.
    #
    #           Double Trough Case: The case of a 'double trough' is corrected in lines 60-68. Instead of a 
    #           clean trough that dips and then rises in voltage when the IR beam is broken, a 'double trough' is 
    #           when the voltage dips, rises, and then quickly dips and rises again to create what looks like two 
    #           merged troughs in one beam-breaking event. To correct this, the code identifies int sequences in 
    #           the int_list that would mistakenly mark this single event as two beam-breaking events, or two 
    #           troughs. Once the code identifies those sequences, it erases the false second trough by overriding 
    #           its 1's to 0's in the int_list.
    #
    # OUTPUT:   List of 1s and 0s where 1 designates the presence of a trough and 0 designates no trough.
    #
    #************************************************************************************************************

    volt_column = [] 
    int_list =[] # sequences of 0s and 1s. 
    troughs=[]
    
    for i in range(0, len(column)): 
        volt_column.append(round(column[i], 2))
    
    channel_mean = (sum(volt_column)/len(volt_column))
    min_val=round(channel_mean - dev_min, 2) # * 
    max_val=round(channel_mean + dev_max, 2) # *
 
    for v in range(0, len(volt_column)):  
        x=(volt_column[v]-min_val)/(max_val-min_val) 
        if x < -2:  # *
            int_list.append(1)  
        else:
            int_list.append(0)

    for j in range(0, len(int_list)-1): 
        if int_list[j] > int_list[j-1] and int_list[j] >= int_list[j+1]: 
            if int_list[j-3] >= int_list[j] or int_list[j-5] >= int_list[j] or int_list[j-7] >= int_list[j]: # double troughs correction
                troughs.append(0)
                for i in range(j, j + sample_rate): 
                    try:
                        int_list[i] = 0
                    except IndexError:
                        continue 
            else:
                troughs.append(1)
        else:
            troughs.append(0)

    troughs.append(0)

    print("   Num of 1's:", sum(int_list), "   Num of troughs:", sum(troughs),
          "   Min Dev: ", dev_min, "   Max Dev: ", dev_max)
    
    return troughs 

def map_diagnostics(deviations, f, heat_map, axs, sampling_rate):

    #************************************************************************************************************
    #
    # Generate heat maps to diagnose files with noise or overly-sensitive troughs.
    #
    # INPUT:    deviations as a list of floats, file number (f) as an int, the figure (heat_map), axs as a
    #           subplot, and the sampling rate of the recording (S/s) as an int. 
    #
    # PROCESS:  Files with little noise and large troughs will be durable to small changes in deviations. Default
    #           here is to test and plot how changes in the min and max deviation values change the number of
    #           troughs; however, other threshold values such as max deviation and the x value threshold.
    #
    # OUTPUT:   Returns the standardized voltage column as a list of 1s and 0s where 1 designates the presence
    #           of a trough and 0 designates no trough. Generates heat map diagnostics of all the recoridng files
    #           in a directory.
    #
    #************************************************************************************************************
    
    all_troughs = []
    for volt_dev_min in deviations:
        num_troughs = []
        for volt_dev_max in deviations:
            troughs_col = trough_standardization(voltage_column, volt_dev_min, volt_dev_max, sampling_rate)
            num_troughs.append(sum(troughs_col))
        all_troughs.append(num_troughs)

    a = np.array(all_troughs)
    axs = axs.flatten()
    im = axs[f].imshow(a, cmap='viridis', interpolation='nearest')

    axs[f].title.set_text(file + '\nMax-Min Troughs=%i' %(max(all_troughs)[0]-min(all_troughs)[-1]))
    axs[f].set_xticks(np.arange(len(deviations)))
    axs[f].set_yticks(np.arange(len(deviations)))
    axs[f].set_xticklabels(deviations, fontsize=8)
    axs[f].set_yticklabels(deviations, fontsize=8)
    axs[f].set_xlabel("Max Dev Val", fontsize=12)
    axs[f].set_ylabel("Min Dev Val", fontsize=12)

    cbar = heat_map.colorbar(im, ax=axs[f], fraction=0.046, pad=0.03)
    cbar.ax.set_ylabel("Number of Troughs", rotation=-90, va="bottom")
    
    rows, cols = a.shape
    for i in range(rows):
        for j in range(cols):
            text = axs[f].text(j, i, a[i, j], ha="center", va="center", color="w", fontsize=5.5)
    
    return troughs_col

def write_to_file(outpath, file_name, lines, time_col, trough_col):
    
    #************************************************************************************************************
    #
    # Write txt file for the standardized troughs.
    #
    # INPUT:    outpath as a string, file name as a string, lines as an integer, time column as floats, and
    #           trough column as floats. 
    #
    # PROCESS:  Output file is opened with its designated outpath. Then, line by line, the time and trough rows
    #           are written.
    #
    # OUTPUT:   A txt file with two columns: a TBF column and a trough column of 0's and 1's.
    #
    #************************************************************************************************************
    
        OutputFile = open(outpath + "standardized_" + str(file_name), mode="w")
        for i in range(0, len(lines)):
            OutputFile.write('%.2f' % time_col[i] + ", " +
                             '%.2f' % trough_col[i] + "\n")
        OutputFile.close()

#************************************************************************************************************
#   To call the recording data file, write the complete file directory path below. An example path is
#   r"/Users/username/Desktop/Flight_scripts/". The number of columns processed below depends on the number
#   of channels used to record the flight data. For individual insects with only two columns per file,
#   only the TBF and voltage reading columns are processed. However, if the number of channels is different
#   the script needs to be edited accordingly.
#************************************************************************************************************

sampling_freq = # Hz
main_path = # input the path to the Flight_scripts directory here 
path = main_path + "split_files/"
dir_list = sorted(os.listdir(path))

hrows = math.ceil(len(dir_list) / 5)  
hmap, haxes = plt.subplots(hrows,5, figsize=(20, 4*hrows), facecolor='w', edgecolor='k')
hmap.tight_layout(pad=5.1) 

print("Files in '", path, "' :")

file_num = 0
for file in dir_list:
    
    print("\n", file)
    filepath = path + str(file)
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

    devs = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    trough_column = map_diagnostics(devs, file_num, hmap, haxes, sampling_freq) # Comment out this line after running diagnostics
    file_num += 1

    #************************************************************************************************************
    #   After running diagnostics, define the trough_col with specific min and max deviation values in the
    #   trough_standardization function below. The default here is a min deviation and max deviation value
    #   of 0.1 V.
    #************************************************************************************************************
    
    #trough_column = trough_standardization(voltage_column, 0.1, 0.1, sampling_freq) # * Uncomment this line after running diagnostics
    out_path = main_path + "standardized_files/"
    write_to_file(out_path, file, Lines, time_column, trough_column) 

hmap.savefig("trough_diagnostic.png") # Comment out this line after running diagnostics

#**********************************************************************************************
# This file has been adopted from Attisano et al. 2015.
#**********************************************************************************************
