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
    
    # 2.
    GCAM_withd_total = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)    
    GCAM_withd_nonAG = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)
    GCAM_withd_irr   = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)
    GCAM_withd_liv   = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)
    GCAM_withd_dom   = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)    
    GCAM_withd_elec  = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)
    GCAM_withd_mfg   = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)
    GCAM_withd_min   = np.zeros((rgnmapData['nrgnNONAG'], OUT.wdnonag.shape[1]), dtype=float)
    
    ls = np.where(rgnmapData['map_rgn_nonag'] > 0)[0]    
    for y in range(0,OUT.wdnonag.shape[1]):
        for index in ls:                                    
            GCAM_withd_total[rgnmapData['map_rgn_nonag'][index]-1,y] += OUT.wdtotal[index,y]
            GCAM_withd_nonAG[rgnmapData['map_rgn_nonag'][index]-1,y] += OUT.wdnonag[index,y]
            GCAM_withd_irr[rgnmapData['map_rgn_nonag'][index]-1,y]   += OUT.wdirr[index,y]
            GCAM_withd_liv[rgnmapData['map_rgn_nonag'][index]-1,y]   += OUT.wdliv[index,y]
            GCAM_withd_dom[rgnmapData['map_rgn_nonag'][index]-1,y]   += OUT.wddom[index,y]
            GCAM_withd_elec[rgnmapData['map_rgn_nonag'][index]-1,y]  += OUT.wdelec[index,y]
            GCAM_withd_mfg[rgnmapData['map_rgn_nonag'][index]-1,y]   += OUT.wdmfg[index,y]
            GCAM_withd_min[rgnmapData['map_rgn_nonag'][index]-1,y]   += OUT.wdmin[index,y]
                        
                        
    OUT.rtotal     = GCAM_withd_total
    OUT.rnonag     = GCAM_withd_nonAG
    OUT.rirr       = GCAM_withd_irr
    OUT.rliv       = GCAM_withd_liv
    OUT.rdom       = GCAM_withd_dom
    OUT.relec      = GCAM_withd_elec
    OUT.rmfg       = GCAM_withd_mfg
    OUT.rmin       = GCAM_withd_min
    
    if Settings.OutputUnit: # convert the original unit km3/yr to new unit mm
        mapindex    = GISData['mapindex']
        area        = GISData['mapAreaExt'][mapindex]
        conversion  = 1e6 # km -> mm

        OUT.wdtotal[mapindex,:]  = np.transpose(np.divide(np.transpose(OUT.wdtotal[mapindex,:]), area)*conversion)
        OUT.wdnonag[mapindex,:]  = np.transpose(np.divide(np.transpose(OUT.wdnonag[mapindex,:]), area)*conversion)
        OUT.wddom[mapindex,:]    = np.transpose(np.divide(np.transpose(OUT.wddom[mapindex,:]), area)*conversion)
        OUT.wdelec[mapindex,:]   = np.transpose(np.divide(np.transpose(OUT.wdelec[mapindex,:]), area)*conversion)
        OUT.wdmfg[mapindex,:]    = np.transpose(np.divide(np.transpose(OUT.wdmfg[mapindex,:]), area)*conversion)
        OUT.wdmin[mapindex,:]    = np.transpose(np.divide(np.transpose(OUT.wdmin[mapindex,:]), area)*conversion)
        OUT.wdirr[mapindex,:]    = np.transpose(np.divide(np.transpose(OUT.wdirr[mapindex,:]), area)*conversion)
        OUT.wdliv[mapindex,:]    = np.transpose(np.divide(np.transpose(OUT.wdliv[mapindex,:]), area)*conversion)