import os
import math
import numpy as np
import matplotlib.pyplot as plt

def trough_standardization(column, dev_min, dev_max):
    
    #************************************************************************************************************
    #
    # Standardizes the voltage data for each channel by identifying large deviances in voltages as troughs.
    #
    # INPUT:    List of voltage values as floats.
    #
    # PROCESS:  Voltage values are rounded to two decimal places and appended to the volt_column. A confidence
    #           interval is defined around the mean voltage value using a low (min_value) and high (max_value)
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
            if int_list[j-3] >= int_list[j] or int_list[j-5] >= int_list[j] or int_list[j-7] >= int_list[j]: # double troughs
                troughs.append(0)
                for i in range(j, j + 100): # 100 = sample rate - 100 time points/s # peaks can be anywhere from 4-30 points
                    try:
                        int_list[i] = 0
                    except IndexError:
                        continue 
            else:
                troughs.append(1)
        else:
            troughs.append(0)

    troughs.append(0)

#    print("   Num of 1's:", sum(int_list), "   Num of troughs:", sum(troughs),
#          "   Min Dev: ", dev_min, "   Max Dev: ", dev_max)
    
    return troughs 

def write_to_file(path, file_name, lines, time_col, trough_col):
    
    #************************************************************************************************************
    #
    # Write txt file for the standardized troughs.
    #
    # INPUT:    path as a string, file name as a string, lines as an integer, time column as floats, and
    #           trough column as floats. 
    #
    # PROCESS:  Output file is opened with its designated outpath. Then, line by line, the time and trough rows
    #           are written.
    #
    # OUTPUT:   A txt file with two columns: a time column and a trough column of 0's and 1's.
    #
    #************************************************************************************************************
    
        #outpath = path + "standardized_files/"
        OutputFile = open(path + "standardized_" + str(file_name), mode="w")
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

if __name__=="__main__":
    
    #main_path = r"/Users/anastasiabernat/Desktop/git_repositories/undergrad-collabs/max_speed/" # input the path to the Flight_scripts directory here 
    main_path = r"/Users/anastasiabernat/Desktop/Dispersal/Trials-Winter2020/" 
    path = main_path + "split_files/"
    dir_list = sorted(os.listdir(path))

    print("Files in '", path, "' :")

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

        #************************************************************************************************************
        #   After running diagnostics, define the trough_column with specific min and max deviation values in the
        #   trough_standardization function below. The default here is a min deviation and max deviation value of 
        #   0.01 V.
        #************************************************************************************************************
        
        trough_column = trough_standardization(voltage_column, 0.1, 0.1) 

        out_path = r"/Users/anastasiabernat/Desktop/Dispersal/Trials-Winter2020/standardize_files/"
        #out_path = r"/Users/anastasiabernat/Desktop/"
        write_to_file(out_path, file, Lines, time_column, trough_column) 

#**********************************************************************************************
# This file has been modified from Attisano et al. 2015.
#**********************************************************************************************
