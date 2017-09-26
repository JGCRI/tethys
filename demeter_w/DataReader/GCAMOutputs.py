"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""


import os
import GCAMutil as util
import GCAMSupport as Support

 
def get_dir_prepender(dir):
    if dir[-1]=='/':
        return lambda file: dir+file
    else:
        return lambda file: dir+'/'+file
        
def GCAMData(settings):
    
    outfiles   = ['land-alloc.csv', 'population.csv', 'water-ag.csv',
                  'water-dom.csv', 'water-elec.csv', 'water-livestock.csv',
                  'water-mfg.csv', 'water-mining.csv']
    

    tempdirprep   = get_dir_prepender(settings.GCAM_CSV)
    outfiles      = map(tempdirprep, outfiles)

    #util.gcam_reader_query_database(settings, outfiles)
    
    #initialize global parameter in GCAMSupoort
    Support.init_rgn_tables(settings, outfiles[3]) # used outfiles[1]
    settings.regions_ordered = Support._regions_ordered
    #settings.pop_gis2000     = Support._gis2000
    rgndirprep    = get_dir_prepender(settings.rgnmapdir)
    
    # non-ag withdrawals 
    Support.proc_wdnonag(outfiles[3], tempdirprep("withd_dom.csv"))
    Support.proc_wdnonag(outfiles[4], tempdirprep("withd_elec.csv"))
    Support.proc_wdnonag(outfiles[6], tempdirprep("withd_manuf.csv"))
    Support.proc_wdnonag(outfiles[7], tempdirprep("withd_mining.csv"))

    # population data
    #Support.proc_pop(outfiles[1], tempdirprep("pop_fac.csv"), tempdirprep("pop_tot.csv"))
    Support.proc_pop(outfiles[1], tempdirprep("pop_tot.csv"))

    #livestock withdrawals
    Support.proc_wdlivestock(outfiles[5], tempdirprep("withd_liv.csv"), tempdirprep('rgn_tot_withd_liv.csv'))
    settings.years     = Support._years
    
    
    # agricultural withdrawals and auxiliary quantities
    Support.proc_ag_vol(outfiles[2], tempdirprep("withd_irrV.csv"))
    if "aez" in os.path.basename(settings.aez).lower():
        gcam_irr = Support.proc_ag_area(outfiles[0], tempdirprep("irrA.csv"))
    else: # If use basins, no irrigation-frac.csv files for basins
        gcam_irr = True
        
    if not gcam_irr:
            ## If GCAM didn't produce endogenous irrigated and
            ## rain-fed land allocations, then we need to read in some
            ## pre-calculated irrigation shares.
            Support.proc_irr_share(rgndirprep('irrigation-frac.csv'), tempdirprep("irrS.csv"))
            settings.read_irrS = 1
    else:
            settings.read_irrS = 0