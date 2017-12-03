"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


1. Add agriculture, livestock, and non-agriculture water withdrawal into one withdrawal map
withd_nonAg_map, OUT.wdirr, OUT.wdliv have no nan

2. Output downscaled results by region and time

3. Perform the  conversion from km3/yr to the output unit
"""

import numpy as np

def TotalWaterUse(Settings, GISData, rgnmapData, OUT):
       
# We use the grid-level representations of all the water withdrawal sources to aggregate them all into a total withdrawal. 
# When we go to re-aggregate them, we use the non-ag region map, since it will typically be the most detailed.
    # 1.
    OUT.wdtotal = OUT.wdnonag + OUT.wdirr + OUT.wdliv
    
    sectorstrs = ['total', 'nonag', 'irr', 'liv', 'dom', 'elec', 'mfg', 'min']
    # 2.
    for item in sectorstrs:
        exec("OUT.r" + item + "= np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)")
    
    ls = np.where(rgnmapData['map_rgn_nonag'] > 0)[0]    
    for y in range(0,OUT.wdnonag.shape[1]):
        for index in ls:
            for item in sectorstrs:
                exec("OUT.r" + item + "[rgnmapData['map_rgn_nonag'][index]-1,y] += OUT.wd"+ item +"[index,y]")                                  
    
    if Settings.OutputUnit: # convert the original unit km3/yr to new unit mm
        mapindex    = GISData['mapindex']
        area        = GISData['mapAreaExt'][mapindex]
        conversion  = 1e6 # km -> mm
        
        for item in sectorstrs:
            exec("OUT.wd" + item + "[mapindex,:]  = np.transpose(np.divide(np.transpose(OUT.wd" + item + "[mapindex,:]), area)*conversion)")