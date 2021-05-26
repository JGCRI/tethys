"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


Perform diagnostics to ensure that the temporally downscaled results of electricity, domestic and irrigation are reasonable
Livestock, Mining and Manufacturing Sectors are uniformly downscaled, thus diagnostics are not needed.

"""
import os
import numpy as np
from tethys.utils.logging import Logger


def compare_temporal_downscaled(Settings, OUT, GISData):

    mainlog = Logger.getlogger()

    ## The outputs produced in this function are an extension of the debugging
    ## logs; therefore, if the logging level is set above DEBUG, we skip the
    ## calculations and the output
    if mainlog.minlvl > Logger.DEBUG:
        return
    
    mapindex   = GISData['mapindex']
    BasinIDs   = GISData['BasinIDs']
    BasinNames = GISData['BasinNames']
    NB         = np.max(BasinIDs)
    years      = Settings.TDYears
    NY         = len(years)
    NM         = len(mapindex)
    mainlog.write(
        '---Temporal Downscaling diagnostics (Global): downscaled results vs. results before temporal downscaling (Total Water, km3/yr)\n',
        Logger.DEBUG)
    
    mainlog.write('------Irrigation------\n')
    W = OUT.WIrr[:,:]
    value   = np.zeros((NY,3), dtype=float)
    for j in years: 
        N = years.index(j)
        value[N,0]  = np.sum(OUT.twdirr[:,N*12:(N+1)*12])
        value[N,1]  = np.sum(W[:,N])
        value[N,2]  = value[N,0] - value[N,1]
        mainlog.write(
            '                Year {0[0]:4d}:   {0[1]:.6f}    {0[2]:.6f}    Diff= {0[3]:.6e}\n'.format([j, value[N,0],
                                                                        value[N,1], value[N,2]]),
            Logger.DEBUG)
    
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
                
    with open(os.path.join(Settings.OutputFolder, 'Diagnostics_Temporal_Downscaling_Irrigation.csv'), 'w') as outfile:
        np.savetxt(outfile, values, delimiter=',', header=headerline, fmt='%s', comments='')
        
        
    mainlog.write('------Domestic------\n', Logger.DEBUG)
    W = OUT.WDom[:, :]
    value   = np.zeros((NY,3), dtype=float)
    for j in years: 
        N = years.index(j)
        value[N,0]  = np.sum(OUT.twddom[:,N*12:(N+1)*12])
        value[N,1]  = np.sum(W[:,N])
        value[N,2]  = value[N,0] - value[N,1]
        mainlog.write(
            '                Year {0[0]:4d}:   {0[1]:.6f}    {0[2]:.6f}    Diff= {0[3]:.6e}\n'.format([j, value[N,0],
                                                                        value[N,1], value[N,2]]),
            Logger.DEBUG)

        
    mainlog.write('------Electricity Generation------\n')
    W = OUT.WEle[:,:]
    value   = np.zeros((NY,3), dtype=float)
    for j in years: 
        N = years.index(j)
        value[N,0]  = np.sum(OUT.twdelec[:,N*12:(N+1)*12])
        value[N,1]  = np.sum(W[:,N])
        value[N,2]  = value[N,0] - value[N,1]         
        mainlog.write(
            '                Year {0[0]:4d}:   {0[1]:.6f}    {0[2]:.6f}    Diff= {0[3]:.6e}\n'.format([j, value[N,0],
                                                                        value[N,1], value[N,2]]),
            Logger.DEBUG)
