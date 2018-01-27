"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute



Perform diagnostics to ensure that the spatially downscaled results and initial aggregate results from GCAM are Consistent
"""

import numpy as np
from tethys.DataWriter.OUTWriter import OUTSettings
    
def compare_downscaled_GCAMinput(Settings, GCAMData, OUT):
    
    print '---Spatial Downscaling Diagnostics (Global): downscaled results vs. aggregated results from GCAM (Total Water, km3/yr)'
    
    NY = Settings.NY
    value   = np.zeros((NY,3), dtype=float)
    for y in range(0, NY): # Global Total For Each Year in log
        
        # Global_DS     Global Total [km3/yr] from downscaled results
        value[y,0]  = sum(OUT.rtotal[:,y])
        # Global_GCAM   Global Total [km3/yr] from GCAM inputs
        value[y,1]  = sum(GCAMData['rgn_wddom'][:,y]) + sum(GCAMData['rgn_wdelec'][:,y]) + sum(GCAMData['rgn_wdmfg'][:,y]) + sum(GCAMData['rgn_wdmining'][:,y]) \
                    + sum(GCAMData['irrV'][:,y+3]) + sum(GCAMData['wdliv'][:,y])
        value[y,2]  = value[y,0] - value[y,1]         
        if Settings.years:
            print '      Year ', Settings.years[y], ':   ', value[y,0], '     ', value[y,1], '     Diff= ', value[y,2]
        else:
            print '      Year Index ', y+1, ':   ', value[y,0], '     ', value[y,1], '     Diff= ', value[y,2]
            
 
    
    # Comprehensive Diagnostics information to file:
    
    category = ['Domestic', 'Electricity', 'Manufacturing', 'Mining', 'Livestock', 'Irrigation', 'Non-Agriculture', 'Agriculture', 'Total']
    group    = ['Downscaled_','GCAM_','Diff_']    
    Sector   = ['Year', 'Region ID', 'Region Name', 'GCAM Population (millions)']
    Unit     = " (km3/yr)"
    
    headerline = ",".join(Sector) + "," + ",".join([prefix + s + Unit for prefix in group for s in category ])
    extension = '.csv'  
    OutputFilename = Settings.OutputFolder + 'Diagnostics_Spatial_Downscaling' + extension   
    
    Regions    = Settings.regions_ordered
    NR         = len(Regions)
    Regions.insert(0,'Global') # Add "Global" to regions
    Years      = Settings.years    
    Population = GCAMData['pop_tot']/1e6
    # Add Global data to all
    Population = np.vstack([sum(Population), Population])
    OUT.rtotal = np.vstack([sum(OUT.rtotal), OUT.rtotal])
    OUT.rnonag = np.vstack([sum(OUT.rnonag), OUT.rnonag])
    OUT.rdom   = np.vstack([sum(OUT.rdom), OUT.rdom])
    OUT.relec  = np.vstack([sum(OUT.relec), OUT.relec])
    OUT.rmfg   = np.vstack([sum(OUT.rmfg), OUT.rmfg])
    OUT.rmin   = np.vstack([sum(OUT.rmin), OUT.rmin])
    OUT.rirr   = np.vstack([sum(OUT.rirr), OUT.rirr])
    OUT.rliv   = np.vstack([sum(OUT.rliv), OUT.rliv])
    
    GCAMOUT    = OUTSettings()
    wdliv      = np.zeros((NR,NY), dtype=float)
    irrV       = np.zeros((NR,NY), dtype=float)
    for IN in range(0, NR):
        wdliv[IN,:] = GCAMData['wdliv'][0*NR+IN,:] + GCAMData['wdliv'][1*NR+IN,:] + GCAMData['wdliv'][2*NR+IN,:] + \
                      GCAMData['wdliv'][3*NR+IN,:] + GCAMData['wdliv'][4*NR+IN,:] + GCAMData['wdliv'][5*NR+IN,:]
                      
        ls = np.where(GCAMData['irrV'][:,0].astype(int)-1 == IN)[0]
        irrV[IN,:] = sum(GCAMData['irrV'][ls,3:])
            
    nonAG = GCAMData['rgn_wddom'] + GCAMData['rgn_wdelec'] + GCAMData['rgn_wdmfg'] + GCAMData['rgn_wdmining']
    AG    = irrV + wdliv
    total = nonAG + AG
    GCAMOUT.rtotal = np.vstack([sum(total), total])
    GCAMOUT.rnonag = np.vstack([sum(nonAG), nonAG])
    GCAMOUT.rdom   = np.vstack([sum(GCAMData['rgn_wddom']), GCAMData['rgn_wddom']])
    GCAMOUT.relec  = np.vstack([sum(GCAMData['rgn_wdelec']), GCAMData['rgn_wdelec']])
    GCAMOUT.rmfg   = np.vstack([sum(GCAMData['rgn_wdmfg']), GCAMData['rgn_wdmfg']])
    GCAMOUT.rmin   = np.vstack([sum(GCAMData['rgn_wdmining']), GCAMData['rgn_wdmining']])
    GCAMOUT.rirr   = np.vstack([sum(irrV), irrV])
    GCAMOUT.rliv   = np.vstack([sum(wdliv), wdliv])
    
    
    values   = [] # 'Year', 'Region ID', 'Region Name', 'GCAM Population (millions)' and all the category*group
    for j in range(0,NY):
        for i in range(0, NR+1):            
            
            DS   = np.array([OUT.rdom[i,j], OUT.relec[i,j], OUT.rmfg[i,j], OUT.rmin[i,j], OUT.rliv[i,j], OUT.rirr[i,j], 
                           OUT.rnonag[i,j], OUT.rliv[i,j]+OUT.rirr[i,j], OUT.rtotal[i,j]])
            
            GCAM = np.array([GCAMOUT.rdom[i,j], GCAMOUT.relec[i,j], GCAMOUT.rmfg[i,j], GCAMOUT.rmin[i,j], GCAMOUT.rliv[i,j], GCAMOUT.rirr[i,j], 
                           GCAMOUT.rnonag[i,j], GCAMOUT.rliv[i,j]+GCAMOUT.rirr[i,j], GCAMOUT.rtotal[i,j]])
            
            Diff = DS.tolist() + GCAM.tolist() + (DS - GCAM).tolist()
            
            if Years is not None:
                data = [Years[j], str(i), Regions[i]] + ["%.2f" % Population[i,j]] + ["%.3f" % x for x in Diff]
            else:
                data = ['Index ' + str(j), str(i), Regions[i]] + ["%.2f" % Population[i,j]] + ["%.3f" % x for x in Diff]
            values.append(data)
    
    values = np.array(values)

    with open(OutputFilename, 'w') as outfile:   
        np.savetxt(outfile, values, delimiter=',', header=headerline, fmt='%s')
            
    print '------Diagnostics information is saved to:', OutputFilename