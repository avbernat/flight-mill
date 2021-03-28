import os
import csv
import shutil
import matplotlib
import numpy as np

from matplotlib import style
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d

plt.style.use('ggplot')

def color_palette(data_path):

   #**********************************************************************************************
   #
   # Builds intentional color palettes for categorical groups within the data.
   #
   # INPUT:    A path, data_path, as a string that leads to a file with ID, set number, chamber, 
   #           flight type, sex, population, mass, and host plant columns. 
   #
   # PROCESS:  Generates dictionaries of each categorical group using csv.DictReader where keys
   #           are unique bug identifies (e.g. ID, set number, and chamber) and values are colors
   #           legible to matplotlib plot objects. In this sense, each dictionary becomes a 
   #           'palette' where specific colors can be referenced to corresponding flight 
   #           trajectories. 
   #
   # OUTPUT:   'Palettes,' which are the dictionaries, are returned. 
   #
   # SOURCE:   https://matplotlib.org/3.2.1/tutorials/colors/colors.html
   #**********************************************************************************************
        
    flight_type_dict = {}
    sex_dict = {}
    pop_dict = {}
    mass_dict = {}
    host_dict = {}

    with open(data_path, "r") as flight_data:
        reader = csv.DictReader(flight_data)
        for row in reader:
            ID = row["ID"]
            set_num = row["set_number"]
            chamber = row["chamber"].split("-")[0] + row["chamber"].split("-")[-1]
            flight_type = row["flight_type"]
            sex = row["sex"]
            pop = row["population"]

            m = row["mass"]
            if m == '':
                m = "0.0"
            mass = float(m)
            
            if (ID, chamber, set_num) not in flight_type_dict:
                flight_type_dict[(ID, chamber, set_num)] = flight_type
                
            if (ID, set_num) not in sex_dict:
                if sex == "F":
                    sex_dict[(ID, set_num)] = "C0"
                if sex == "M":
                    sex_dict[(ID, set_num)] = "C1"
                    
            if (ID, set_num) not in host_dict:
                if pop == "North Key Largo" or pop == "Key Largo" or pop == "Plantation Key":
                    host_dict[(ID, set_num)] = "g"
                else:
                    host_dict[(ID, set_num)] = "b"
                    
            if (ID, set_num) not in pop_dict:
                if pop == "North Key Largo":
                    pop_dict[(ID, set_num)] = "b"
                if pop == "Key Largo":
                    pop_dict[(ID, set_num)] = "g"
                if pop == "Plantation Key":
                    pop_dict[(ID, set_num)] = "w"
                if pop == "Homestead":
                    pop_dict[(ID, set_num)] = "y"
                if pop == "Gainesville":
                    pop_dict[(ID, set_num)] = "k" #'tab:purple'
                if pop == "Lake Wales":
                    pop_dict[(ID, set_num)] = "r"
                if pop == "Lake Placid":
                    pop_dict[(ID, set_num)] = 'tab:orange'
                if pop == "Leesburg":
                    pop_dict[(ID, set_num)] = 'tab:pink'
                    
            if (ID, set_num) not in mass_dict:
                if mass < 0.0527: # 0.05271686 mean of mass, calculated in R
                    mass_dict[(ID, set_num)] = "k"
                if mass >= 0.0527: 
                    mass_dict[(ID, set_num)] = "r"
   
    return flight_type_dict, sex_dict, pop_dict, mass_dict, host_dict

def plot_trajectories(x, y, plt, filename, ID, set_n, chamber, flight_type_dictionary, sex_dictionary, pop_dictionary, 
                                mass_dictionary, host_dictionary, outpath, plot_spline=False, plot_speed=False, 
                                plot_acc=False, individual=False):

   #**********************************************************************************************
   # 
   # Plots either individual flight trajectories or a single graph of all flight trajectories.
   #
   # INPUT:    x, which represents time (s) as a list of floats; y, which represents speed (m/s) 
   #           as a list of floats; plt as the plot object(s); and filename for the labels of each
   #           plot object as a string. Several keys are also included for palette color retrieval, 
   #           which include ID, set_n, and chamber as strings. Dictionaries that require 
   #           aforementioned keys for palette retrieval are also included. Addititionally, an 
   #           outpathfor the generation of a plot or plots as .png files needs to be specified. 
   #           Finally, several boolean arguments that help the user decide which features to plot
   #           and how many: plot_spline, plot_speed, plot_acc, and individual.
   #
   # PROCESS:  Booleans determine what graph(s) are generated. The user can select the follwowing:
   #              1. Write 'True' for plot_spline for a first-order spline creation (linear). 
   #                 The last argument of np.linespace() determines the number of points to make 
   #                 per spline. It is currently set at 20, and it can be changed. Additionally,
   #                 to plot a second- or third-order spline the following can be added beneath
   #                 the 'if plot_spline:' conditional, respectively:
   #                       f2 = interp1d(x, y, kind = 'quadratic')
   #                       f3 = interp1d(x, y, kind = 'cubic')
   #              2. Write 'True' for plot_spline or plot_acc to plot either speed or acceleration
   #                 on the y-axis. 
   #              3. Write 'True' for individual to plot individual file plots. Write 'False' to 
   #                 only generate a plot with all flight trajectory data.
   #           Regardless of boolean inputs, time and speed lists are filtered to remove the last
   #           values of [0.0], [0.0] and transform the time values to have its start time at 0. 
   #           Time and speed lists are also screened to not plot any files that fail to have 2 or 
   #           more time and speed value pairs.
   #
   # OUTPUT:   Individual flight trajectory plot(s) (.png) of either speed or acceleration through 
   #           time.
   #
   # SOURCES:  Smoothing the data: https://stackoverflow.com/questions/5283649/plot-smooth-line-with-pyplot.
   #           Plot derivatives: https://stackoverflow.com/questions/52957623/how-to-plot-the-derivative-of-a-plot-python
   #
   #**********************************************************************************************
   
   # Palettes:
   # sex_color = sex_dictionary[(ID, set_n)]
   # pop_color = pop_dictionary[(ID, set_n)]
   # mass_color = mass_dictionary[(ID, set_n)]
   # host_color = host_dictionary[(ID, set_n)]  

   initial_time = x[0]
   for i in range(len(x)):
      x[i] = x[i] - initial_time

   x = x[0:len(x)-1]
   y = y[0:len(y)-1]

   if len(x) <= 1: 
      plot_spline=False
      plot_speed=False
      plot_acc=False
      individual=False

   plt.title('Flight Trajectories')
   plt.xlabel('Seconds from start') 
   plt.legend(['linear'], loc='best')     

   if plot_spline: 
      xnew = np.linspace(min(x), max(x), 20)
      x = np.array(x)
      y = np.array(y)
      f = interp1d(x, y) 
      if individual:
         plt.plot(x, y, 'c-',
                  xnew, f(xnew), 'k-', # xnew, f2(xnew), 'k--', # xnew, f3(xnew), 'r--',
                  markersize=1)
         plt.legend(['data', 'linear'], loc='best') # add 'quadratic' and 'cubic' if plotting those too
      
      plt.plot(xnew, f(xnew), 'k-', markersize=1, linewidth=0.35)

   if individual:
      plt.title('Flight Data' + str(' ') + str(filename))
   if plot_speed:
      plt.ylabel('Speed (m/s)')
   if plot_acc:
      plt.ylabel('Acceleration (m/s/s)')

   if individual:
      if plot_speed:
         output_filename = 'speed_' + str(filename).replace(".txt", ".png")
      if plot_acc:
         output_filename = 'acc_' + str(filename).replace(".txt", ".png")
      concatenated_path = os.path.join(outpath, output_filename)
      plt.savefig(concatenated_path, dpi=300, bbox_inches='tight')
      plt.clf()

########################################################################################################################

if __name__=="__main__":
   root_path = r"/Users/anastasiabernat/Desktop/Dispersal/Trials-Winter2020/"

   summary_file_path = root_path + "1.trials-time-processed-Dec10.2020.csv"
   flight_type_dict, sex_dict, pop_dict, mass_dict, host_dict = color_palette(summary_file_path)

   plt.figure()
   path = root_path = "flight_analyses/"
   dir_list = sorted(os.listdir(path))

   for filename in dir_list:
      ID_num = filename.split("_")[-1].replace(".txt", "")
      set_num = filename.split("-")[0].split("t")[-1].lstrip('0')
      chamber = filename.split("_")[0].split("-")[-1]

      filepath = path + filename
      input_file = open(filepath, mode="r", encoding='latin-1')
      
      times = []
      speeds = []
      for row in input_file:
         split = row.split(',')
         time = float(split[0])
         speed = float(split[1]) 
         times.append(time)
         speeds.append(speed)

      plot_trajectories(times, speeds, plt, filename, ID_num, set_num, chamber, 
                                flight_type_dict, sex_dict, pop_dict, mass_dict, host_dict, root_path, 
                                plot_spline=True, plot_speed=True, plot_acc=False, individual=False)

   outfile = root_path + "flight_trajectories-2.png"
   plt.savefig(outpath + outfile, dpi=300, bbox_inches='tight')
   plt.clf()
