
def plot_diagnostics(deviations, file_number, figure, axs, trough_standarize, volt_col, file):
    
    #************************************************************************************************************
    #
    # Plot diagnostics to identity noise or files with overly-sensitive troughs.
    #
    # INPUT:    deviations as a list of floats, file_number as an int, the figure, and axs as a subplot. 
    #           To make it importable into the standardize_troughs.py script, arguments trough_standardize,
    #           volt_col, and file need to be included.
    #
    # PROCESS:  Files with little noise and large troughs will be durable to small changes in deviations. Default
    #           here is to test and plot how changes in the min and max deviation values change the number of
    #           troughs; however, other threshold values such as max deviation and the x value threshold.
    #
    # OUTPUT:   Returns the standardized voltage column as a list of 1s and 0s where 1 designates the presence
    #           of a trough and 0 designates no trough. Plots diagnositcs of all the recoridng files in a
    #           directory.
    #
    #************************************************************************************************************
    
    f = file_number*10
    
    for volt_dev_min in deviations:
        num_troughs = []
        for volt_dev_max in deviations:
            troughs_col = trough_standarize(volt_col, volt_dev_min, volt_dev_max)
            num_troughs.append(sum(troughs_col))
            
        axs = axs.flatten()
        axs[f].plot(deviations, num_troughs, linestyle='--', marker='o', color='b')
        axs[f].set_ylim([min(num_troughs)-1, max(num_troughs)+1])
        axs[f].title.set_text(file + '\nMax-Min=%i' %(max(num_troughs)-min(num_troughs)))
        axs[f].set_xlabel("Max Val")
        axs[f].set_ylabel("Number of Troughs")
        axs[f].text(0.75, 0.9, "Min Val=%.2f" %volt_dev_min, ha='center', va='center', transform=axs[f].transAxes)
        
        for x,y in zip(deviations, num_troughs):
            label=y
            axs[f].annotate(label,(x,y), textcoords="offset points", xytext=(10,5), ha='center')

        f += 1

    return troughs_col
