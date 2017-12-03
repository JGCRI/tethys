"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute



Perform diagnostics to ensure that the temporally downscaled results of electricity, domestic and irrigation are reasonable
Livestock, Mining and Manufacturing Sectors are uniformly downscaled, thus diagnostics are not needed.

"""
import os
import numpy as np
from demeter_w.Utils.DataParser import GetArrayCSV
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FormatStrFormatter
    
def compare_temporal_downscaled(Settings, OUT, GISData):
    
    mapindex   = GISData['mapindex']
    BasinIDs   = GISData['BasinIDs']
    BasinNames = GISData['BasinNames']
    NB         = np.max(BasinIDs)
    years      = Settings.TDYears
    NY         = len(years)
    NM         = len(mapindex)
    print '---Temporal Downscaling Diagnostics (Global): downscaled results vs. results before temporal downscaling (Total Water, km3/yr)'
    
    
    print '------Irrigation------'
    W = OUT.WIrr[:,:]
    value   = np.zeros((NY,3), dtype=float)
    for j in years: 
        N = years.index(j)
        value[N,0]  = np.sum(OUT.twdirr[:,N*12:(N+1)*12])
        value[N,1]  = np.sum(W[:,N])
        value[N,2]  = value[N,0] - value[N,1]         
        print '                Year ', j, ':     ', value[N,0], '     ', value[N,1], '     Diff= ', value[N,2]
    
    # Print out the basin level comparison
    Sector   = ['Year', 'Basin ID', 'Basin Name', 'After Spatial Downscaling', 'After Temporal Downscaling', 'Diff']
    Unit     = " (km3/yr)"
    headerline = ",".join(Sector) + Unit
    
    Wtd_basin = np.zeros((NB,NY),dtype = float)
    W_basin = np.zeros((NB,NY),dtype = float)
    for index in range(0, NM):
        for y in range(0, NY): 
            if not np.isnan(W[index, y]) and BasinIDs[index] > 0:
                W_basin[BasinIDs[index] - 1, y]   += W[index, y]  
                Wtd_basin[BasinIDs[index] - 1, y] += np.sum(OUT.twdirr[index,y*12:(y+1)*12])
                
    values = []
    for j in years:
        N = years.index(j)
        for i in range(0,NB):
            data = [str(j), str(i+1), BasinNames[i]] + ["%.3f" % W_basin[i,N]] + ["%.3f" % Wtd_basin[i,N]] + ["%.3f" % (W_basin[i,N] - Wtd_basin[i,N])]
            values.append(data) 
                
    with open(Settings.OutputFolder + 'Diagnostics_Temporal_Downscaling_Irrigation.csv', 'w') as outfile:   
        np.savetxt(outfile, values, delimiter=',', header=headerline, fmt='%s')
        
        
        
    print '------Domestic------'
    W = OUT.WDom[:,:]
    value   = np.zeros((NY,3), dtype=float)
    for j in years: 
        N = years.index(j)
        value[N,0]  = np.sum(OUT.twddom[:,N*12:(N+1)*12])
        value[N,1]  = np.sum(W[:,N])
        value[N,2]  = value[N,0] - value[N,1]         
        print '                Year ', j, ':     ', value[N,0], '     ', value[N,1], '     Diff= ', value[N,2]
    #
    Domestic_TD__Diagnostics_Plot(OUT.twddom, GISData, Settings.OutputFolder)
        
        
    print '------Electricity Generation------'
    W = OUT.WEle[:,:]
    value   = np.zeros((NY,3), dtype=float)
    for j in years: 
        N = years.index(j)
        value[N,0]  = np.sum(OUT.twdelec[:,N*12:(N+1)*12])
        value[N,1]  = np.sum(W[:,N])
        value[N,2]  = value[N,0] - value[N,1]         
        print '                Year ', j, ':     ', value[N,0], '     ', value[N,1], '     Diff= ', value[N,2]
    #
    Electricity_TD__Diagnostics_Plot(OUT.twdelec, GISData, Settings.OutputFolder)
    
def Electricity_TD__Diagnostics_Plot(data, GISData, OutputFolder):
    # Aggregate data into country scale and get the mean for each month of 12 months
    CountryIDs = GISData['CountryIDs']
    NC = np.max(GISData['CountryIDs'])
    NG = np.shape(data)[0]
    NM = np.shape(data)[1]
    new_data = np.zeros((NC,12),dtype = float)
    for index in range(NG): 
        for m in range(12):
            if CountryIDs[index] > 0:
                new_data[CountryIDs[index] - 1, m] += np.mean(data[index, range(m,NM,12)])
    
	# IEA_9_Countries_Monthly_AvgElectricity_2000_2015.csv is in the reference folder
    Ele_gen_data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reference/IEA_9_Countries_Monthly_AvgElectricity_2000_2015.csv')
    Ele_gen_data      = GetArrayCSV(Ele_gen_data_file, 1)
                    
    CountryID   = Ele_gen_data[0,1:].astype(int)
    
    # Normalize the simulated
    new_data2 = new_data[CountryID,:]
    obv_data = np.zeros((9,12),dtype = float)
    sim_data = np.zeros((9,12),dtype = float)
    for m in range(9):
        obv_data[m,:] = Ele_gen_data[1:, m+1]/np.sum(Ele_gen_data[1:,m+1])
        sim_data[m,:] = new_data2[m, :]/np.sum(new_data2[m, :])
    
    fig = plt.figure()
    
    # Add 9 subplots
    ax1 = fig.add_subplot(3,3,1)
    ax2 = fig.add_subplot(332)
    ax3 = fig.add_subplot(333)
    ax4 = fig.add_subplot(334)
    ax5 = fig.add_subplot(335)
    ax6 = fig.add_subplot(336)
    ax7 = fig.add_subplot(337)
    ax8 = fig.add_subplot(338)
    ax9 = fig.add_subplot(339)
    
    # Plot primary y axis
    ax1.plot(range(1,13), sim_data[0,:], 'r-')
    ax2.plot(range(1,13), sim_data[1,:], 'r-')
    ax3.plot(range(1,13), sim_data[2,:], 'r-')
    ax4.plot(range(1,13), sim_data[3,:], 'r-')
    ax5.plot(range(1,13), sim_data[4,:], 'r-')
    ax6.plot(range(1,13), sim_data[5,:], 'r-')
    ax7.plot(range(1,13), sim_data[6,:], 'r-')
    ax8.plot(range(1,13), sim_data[7,:], 'r-')
    ax9.plot(range(1,13), sim_data[8,:], 'r-')     
    
    ax1.plot(range(1,13),obv_data[0,:],'b-')
    ax2.plot(range(1,13),obv_data[1,:],'b-')
    ax3.plot(range(1,13),obv_data[2,:],'b-')
    ax4.plot(range(1,13),obv_data[3,:],'b-')
    ax5.plot(range(1,13),obv_data[4,:],'b-')
    ax6.plot(range(1,13),obv_data[5,:],'b-')
    ax7.plot(range(1,13),obv_data[6,:],'b-')
    ax8.plot(range(1,13),obv_data[7,:],'b-')
    ax9.plot(range(1,13),obv_data[8,:],'b-')
    
    # Set xticks
    xi = np.arange(2, 13, 2.0)
    ax1.set_xticks(xi)
    ax2.set_xticks(xi)
    ax3.set_xticks(xi)
    ax4.set_xticks(xi)
    ax5.set_xticks(xi)
    ax6.set_xticks(xi)
    ax7.set_xticks(xi)
    ax8.set_xticks(xi)
    ax9.set_xticks(xi)
    
    # Set yticks
    yi = np.arange(0.06, 0.12, 0.02)
    ax1.set_yticks(yi)
    ax2.set_yticks(yi)
    ax3.set_yticks(yi)
    ax4.set_yticks(yi)
    ax5.set_yticks(yi)
    ax6.set_yticks(yi)
    ax7.set_yticks(yi)
    ax8.set_yticks(yi)
    ax9.set_yticks(yi)
    
    # Set titles
    ax1.set_title("AUSTRALIA")
    ax2.set_title("CANADA")
    ax3.set_title("CHILE")
    ax4.set_title("FRANCE")
    ax5.set_title("JAPAN")
    ax6.set_title("MEXICO")
    ax7.set_title("SWEDEN")
    ax8.set_title("TURKEY")
    ax9.set_title("UNITED STATES")
    
    # Set common labels
    fig.text(0.5, 0.01, 'Month', ha='center', va='center', fontsize = 8)
    fig.text(0.01, 0.5, 'Normalized Monthly Averaged Electricity Generation', ha='center', va='center', rotation='vertical', fontsize = 6)    
    
    # Add legend
    ax8.legend(['Simulated', 'Observed'],loc='lower center', bbox_to_anchor=(0.5, -0.05),fontsize = 6, frameon=False)
    plt.tight_layout()
    fig.savefig(OutputFolder + 'Diagnostics_Temporal_Downscaling_Electricity' + '.png', dpi=300)
    plt.close(fig)
    
def Domestic_TD__Diagnostics_Plot(data, GISData, OutputFolder):
    # obv_dom.csv is in the reference folder
    obv_dom_data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reference/obv_dom.csv')

    with open(obv_dom_data_file, 'r') as f:
        Alllines = f.read().splitlines()
    obv_dom_data = [Alllines[l].split(',') for l in range(1,len(Alllines))]
    obv_dom_month = np.array(obv_dom_data)[:,6:].astype(float)
    
    NM = np.shape(data)[1]
    new_data = np.zeros((len(Alllines)-1,12),dtype = float)
    for index in range(len(Alllines)-1): 
        for m in range(12):
            new_data[index, m] = np.mean(data[int(obv_dom_data[index][3]), range(m,NM,12)])
            
    # Normalize the simulated
    obv_data = np.zeros((5,12),dtype = float)
    sim_data = np.zeros((5,12),dtype = float)

    for m in range(5):
        obv_data[m,:] = obv_dom_month[m,:]/np.sum(obv_dom_month[m,:])
        sim_data[m,:] = new_data[m, :]/np.sum(new_data[m, :])
    
    fig = plt.figure()
    
    # Set the font size globally
    mpl.rcParams['axes.titlesize'] = 8
    mpl.rcParams['xtick.labelsize']= 8
    mpl.rcParams['ytick.labelsize']= 8
    
    # Add 5 sub plots
    ax1 = fig.add_subplot(321)
    ax2 = fig.add_subplot(322)
    ax3 = fig.add_subplot(323)
    ax4 = fig.add_subplot(324)
    ax5 = fig.add_subplot(325)
    
    # Plot primary y axis
    ax1.plot(range(1,13), sim_data[0,:], 'r-')
    ax2.plot(range(1,13), sim_data[1,:], 'r-')
    ax3.plot(range(1,13), sim_data[2,:], 'r-')
    ax4.plot(range(1,13), sim_data[3,:], 'r-')
    ax5.plot(range(1,13), sim_data[4,:], 'r-')

    ax1.plot(range(1,13),obv_data[0,:], 'b-')
    ax2.plot(range(1,13),obv_data[1,:], 'b-')
    ax3.plot(range(1,13),obv_data[2,:], 'b-')
    ax4.plot(range(1,13),obv_data[3,:], 'b-')
    ax5.plot(range(1,13),obv_data[4,:], 'b-')
    
    # Set xticks
    xi = np.arange(2, 13, 2.0)
    ax1.set_xticks(xi)
    ax2.set_xticks(xi)
    ax3.set_xticks(xi)
    ax4.set_xticks(xi)
    ax5.set_xticks(xi)
    
    # Set yticks
    yi = np.arange(0.05, 0.13, 0.02)
    ax1.set_yticks(yi)
    ax2.set_yticks(yi)
    ax3.set_yticks(yi)
    ax4.set_yticks(yi)
    ax5.set_yticks(yi)
    
    # Set titles
    ax1.set_title(obv_dom_data[0][0]+","+obv_dom_data[0][1]+"("+ obv_dom_data[0][2]+")")
    ax2.set_title(obv_dom_data[1][0]+","+obv_dom_data[1][1]+"("+ obv_dom_data[1][2]+")")
    ax3.set_title(obv_dom_data[2][0]+","+obv_dom_data[2][1]+"("+ obv_dom_data[2][2]+")")
    ax4.set_title(obv_dom_data[3][0]+","+obv_dom_data[3][1]+"("+ obv_dom_data[3][2]+")")
    ax5.set_title(obv_dom_data[4][0]+","+obv_dom_data[4][1]+"("+ obv_dom_data[4][2]+")")
    
    # Set common labels
    fig.text(0.5, 0.01, 'Month', ha='center', va='center', fontsize = 8)
    fig.text(0.01, 0.5, 'Normalized Monthly Averaged Domestic Water Withdrawal', ha='center', va='center', rotation='vertical', fontsize = 6)
    
    #Add legend
    ax4.legend(['Simulated', 'Observed'],loc='lower center', bbox_to_anchor=(0.5, -1.0),fontsize = 6, frameon=False)
    plt.tight_layout()
    fig.savefig(OutputFolder + 'Diagnostics_Temporal_Downscaling_Domestic' + '.png', dpi=300)
    plt.close(fig)