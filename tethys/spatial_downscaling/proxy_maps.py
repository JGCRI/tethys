"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


This is the core of Water Disaggregation

    - mapsize     [360,720] for 0.5 degree
    - settings    class ConfigSettings(), required input and controlling parameters
    - OUT         class OUTSettings(), data for output, gridded results for each withdrawal category
    - GISData     structure GISData{}, GIS data on grid map of 360*720
    - GCAMData    structure GCAMData{}, GCAM outputs with dimension: NRegions X NYears
    - GISData  structure GISData{}, region names, region ID for each valid cell on grid map

"""
import logging

import numpy as np


def PopulationMap(mapsize, GISData, GCAMData, OUT, NY):
    """
    :param withd_dom_map: waer withdrawal domestic map
    :type withd_dom_map: matrix

    # Total Non-Agricultural Water withdrawal in 1990, 2005, ... 2050, and 2010
    # Population in millions in year 2000
    # Population density map is used to downscale Non-Agricultural Water withdrawal 
    """

    # non-agricultural (dom, elec, mfg, mining) total water withdrawals in (km3/yr) for each of the GCAM regions
    # population map for all years 1990, 2005:2100
    ms      = (mapsize[0]*mapsize[1],NY)
    # withd_nonAg_map   = np.full(ms, np.NaN, dtype=float)
    withd_dom_map     = np.full(ms, np.NaN, dtype=float)
    withd_elec_map    = np.full(ms, np.NaN, dtype=float)
    withd_mfg_map     = np.full(ms, np.NaN, dtype=float)
    withd_mining_map  = np.full(ms, np.NaN, dtype=float)    
    
    # use historical population maps
    for y in range (0,NY):
        # population map
        logging.info('{}'.format(GISData['pop']['years'][y]))

        yearstr = str(GISData['pop']['years_new'][y])
        pop = np.where(GISData['RegionIDs'] > 0, GISData['pop'][yearstr], 0)  # 67420 shape, filter out invalid regions

        # Adjust population map to be consistent with GCAM assumptions. We will use
        # the non-ag region map for this because in all current setups it is more detailed.
        pop_fac = np.zeros((GISData['nregions'], NY), dtype=float)
        # Correction to pop_fac`

        for i in range(GISData['nregions']):
            index = np.where(GISData['RegionIDs'] == i + 1)[0]
            pop_fac[i] = GCAMData['pop_tot'][i] / np.sum(pop[index])

        pop_tot_y = GCAMData['pop_tot'][:, y]  # single time slice regional pop
        pop_pro_rata = pop * pop_fac[GISData['RegionIDs'] - 1, y] / pop_tot_y[GISData['RegionIDs'] - 1]

        withd_dom_map[GISData['mapindex'], y] = pop_pro_rata * GCAMData['rgn_wddom'][:, y][GISData['RegionIDs'] - 1]
        withd_elec_map[GISData['mapindex'], y] = pop_pro_rata * GCAMData['rgn_wdelec'][:, y][GISData['RegionIDs'] - 1]
        withd_mfg_map[GISData['mapindex'], y] = pop_pro_rata * GCAMData['rgn_wdmfg'][:, y][GISData['RegionIDs'] - 1]
        withd_mining_map[GISData['mapindex'], y] = pop_pro_rata * GCAMData['rgn_wdmining'][:, y][GISData['RegionIDs'] - 1]

    # total non-ag withdrawal can be computed from these four maps
    withd_nonAg_map = withd_dom_map + withd_elec_map + withd_mfg_map + withd_mining_map
    
    # The maps have the nan values replaced by zero, if we want to keep the nans (for plotting), comment the following 5 lines
    withd_dom_map[np.isnan(withd_dom_map)]       = 0
    withd_elec_map[np.isnan(withd_elec_map)]     = 0
    withd_mfg_map[np.isnan(withd_mfg_map)]       = 0
    withd_mining_map[np.isnan(withd_mining_map)] = 0
    withd_nonAg_map[np.isnan(withd_nonAg_map)]   = 0
    
    OUT.wdnonag  = withd_nonAg_map
    OUT.wddom    = withd_dom_map
    OUT.wdelec   = withd_elec_map
    OUT.wdmfg    = withd_mfg_map
    OUT.wdmin    = withd_mining_map
    
    return withd_nonAg_map


def LivestockMap(mapsize, GISData, GCAMData, NY, OUT):     
    """
    Livestock gridded GIS data maps by six types are used to downscale livestock Water withdrawal 
    """

    # count how many animals live in each GCAM region first    
    nregions = GISData['nregions']
    tot_livestock = np.zeros((nregions, 6), dtype=float)  # Livestock totals at GCAM scale in year 2005

    for i in np.where(GISData['RegionIDs'] > 0)[0]:
        region = GISData['RegionIDs'][i] - 1
        tot_livestock[region, 0] += GISData['Buffalo'][i]
        tot_livestock[region, 1] += GISData['Cattle'][i]
        tot_livestock[region, 2] += GISData['Goat'][i]
        tot_livestock[region, 3] += GISData['Sheep'][i]
        tot_livestock[region, 4] += GISData['Poultry'][i]
        tot_livestock[region, 5] += GISData['Pig'][i]
  
    #  now create a spatial distribution for each GCAM region
    #  withd_liv: these are the GCAM results of total volume of livestock water withdrawal in
    #  km3 in each GCAM region per animal type in the years 1990, 2005:5:2095
    #  variables are nrgn GCAM regions x 6 animals (1:Buffalo, 2:Cattle, 3-Goat, 4-Sheep, 5-Poultry, 6-Pig)
    # 
    #  Next, we distribute those volumes using the spatial distribution of the gis maps
    # these will be the GIS downscaled matrices

    withd_liv_map_LAND = np.zeros((GISData['RegionIDs'].shape[0], NY), dtype=float)
    for y in range(0, NY):
        livestock = np.zeros((GISData['RegionIDs'].shape[0], 6), dtype=float)
        for i in np.where(GISData['RegionIDs'] > 0)[0]:
            region = GISData['RegionIDs'][i] - 1
            if GISData['Buffalo'][i] != 0:
                livestock[i, 0] = GCAMData['wdliv'][0*nregions + region, y] * GISData['Buffalo'][i] / tot_livestock[region, 0]
            if GISData['Cattle'][i] != 0:
                livestock[i, 1] = GCAMData['wdliv'][1*nregions + region, y] * GISData['Cattle'][i] / tot_livestock[region, 1]
            if GISData['Goat'][i] != 0:
                livestock[i, 2] = GCAMData['wdliv'][2*nregions + region, y] * GISData['Goat'][i] / tot_livestock[region, 2]
            if GISData['Sheep'][i] != 0:
                livestock[i, 3] = GCAMData['wdliv'][3*nregions + region, y] * GISData['Sheep'][i] / tot_livestock[region, 3]
            if GISData['Poultry'][i] != 0:
                livestock[i, 4] = GCAMData['wdliv'][4*nregions + region, y] * GISData['Poultry'][i] / tot_livestock[region, 4]
            if GISData['Pig'][i] != 0:
                livestock[i, 5] = GCAMData['wdliv'][5*nregions + region, y] * GISData['Pig'][i] / tot_livestock[region, 5]
        withd_liv_map_LAND[:, y] = np.sum(livestock, axis=1)

    withd_liv_map = np.zeros((mapsize[0] * mapsize[1], NY), dtype=float)
    withd_liv_map[GISData['mapindex']] = withd_liv_map_LAND
    OUT.wdliv = withd_liv_map

    # Diagnostic message
    fmtstr = '[Year Index, Region ID, {:7s} from GCAM not assigned (no GIS data)]:  {}  {}  {}'
    dat = GCAMData['wdliv']
    for y in range(0,NY):
        for IN in range(0,nregions):
            if GCAMData['wdliv'][0*nregions+IN,y] > 0 and tot_livestock[IN,0] == 0:
                logging.info(fmtstr.format('buffalo', y+1, IN+1, dat[0*nregions+IN,y]))

            if GCAMData['wdliv'][1*nregions+IN,y] > 0 and tot_livestock[IN,1] == 0:
                logging.info(fmtstr.format('cattle', y+1, IN+1, dat[1*nregions+IN,y]))

            if GCAMData['wdliv'][2*nregions+IN,y] > 0 and tot_livestock[IN,2] == 0:
                logging.info(fmtstr.format('goat', y+1, IN+1, dat[2*nregions+IN,y]))

            if GCAMData['wdliv'][3*nregions+IN,y] > 0 and tot_livestock[IN,3] == 0:
                logging.info(fmtstr.format('sheep', y+1, IN+1, dat[3*nregions+IN,y]))

            if GCAMData['wdliv'][4*nregions+IN,y] > 0 and tot_livestock[IN,4] == 0:
                logging.info(fmtstr.format('poultry', y+1, IN+1, dat[4*nregions+IN,y]))

            if GCAMData['wdliv'][5*nregions+IN,y] > 0 and tot_livestock[IN,5] == 0:
                logging.info(fmtstr.format('pig', y+1, IN+1, dat[5*nregions+IN,y]))

    return withd_liv_map

    
def IrrigationMap(mapsize, GISData, GCAMData, NY, OUT):

    # Need to downscale the agricultural water withdrawal data for GCAM years
    # using the existing map of areas equipped with irrigation as a proxy for disaggregation from
    # SubRegion to grid scale CHALLENGE: where to add new agricultural lands

    # STEP 1: read in Basin grid map
    nSubRegion = np.amax(GISData['BasinIDs'])

    # STEP 2: calculate the total amount of irrigated lands in each GCAM region from the GCAM output files.
    # The irrArea file from GCAM has the format:
    # 1: GCAM regions 1-nrgn
    # 2: SubRegions 1-18
    # 3: crops 1-17
    # 4 .. nyear+3: values for GCAM output years
    # We are going to reorganize this into irrArea(rgn,SubRegion,crop,year)(but the name irrArea is already taken, so we'll call it tempA_all)
    nregions = GISData['nregions']
    r1 = GCAMData['irrArea'].shape[0]
    try:
        r2, q2 = GCAMData['irrShare'].shape
    except:
        r2, q2 = 0, 0
    r3 = GCAMData['irrV'].shape[0]
    ncrops    = max(max(GCAMData['irrArea'][:,2].astype(int)),max(GCAMData['irrV'][:,2].astype(int)))
    tempA_all = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    tempS_all = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    tempV_all = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    
    for i in range(0, r1):
        for y in range(0, NY):
            tempA_all[GCAMData['irrArea'][i, 0].astype(int)-1, GCAMData['irrArea'][i, 1].astype(int)-1, GCAMData['irrArea'][i, 2].astype(int)-1, y] = GCAMData['irrArea'][i, y+3]*1000
            # convert from thousands of km2 to km2
            
    # if irrShare was read in, then reorganize the same way we did with irrArea.
    # Otherwise, set all irrigation shares to one (indicating that irrArea really is irrigated area,
    # as calculated in GCAM, not total planted area, as in older versions of GCAM.)
    if r2 > 1 or  q2 > 1:
        for i in range(0,r2):
            for y in range (0,NY):
                tempS_all[GCAMData['irrShare'][i,0].astype(int)-1,GCAMData['irrShare'][i,1].astype(int)-1,GCAMData['irrShare'][i,2].astype(int)-1,y] = GCAMData['irrShare'][i,y+3]
    else:
        tempS_all = np.ones((nregions,nSubRegion,ncrops,NY), dtype = float)

    # Same reorganization for irrVolume. Result goes to tempV_all
    for i in range(0,r3):
        for y in range(0,NY):
            tempV_all[GCAMData['irrV'][i,0].astype(int)-1,GCAMData['irrV'][i,1].astype(int)-1,GCAMData['irrV'][i,2].astype(int)-1,y] = GCAMData['irrV'][i,y+3]
               
    # STEP 3: now that we have computed the total irrigated lands, we can aggregate all
    # the numbers for all the crops; we only keep the value per gcam region and SubRegion
    irr_A = np.zeros((nregions,nSubRegion,NY), dtype = float)
    irr_V = np.zeros((nregions,nSubRegion,NY), dtype = float)
    
    for i in range (0,nregions):
        for j in range(0,nSubRegion):
            for y in range(0,NY):
                for k in range(0,ncrops):                            
                    irr_A[i,j,y] += tempA_all[i,j,k,y]*tempS_all[i,j,k,y]
                    irr_V[i,j,y] += tempV_all[i,j,k,y]
                    
    
    ms            = (mapsize[0]*mapsize[1],NY)
    ms67420 = (GISData['RegionIDs'].shape[0], NY)
    irrA_grid     = np.full(ms67420, np.NaN, dtype = float)
    #irrA_frac     = np.full(ms, np.NaN, dtype = float)
    withd_irr_map = np.full(ms67420, np.NaN, dtype = float) # GIS results
    
    # use historical irrigation area maps
    # STEP 4: read a grid map of the irrigated area in km2 in a certain year
    for y in range (0,NY):
        logging.info('{}'.format(GISData['irr']['years'][y]))
        yearstr = str(GISData['irr']['years_new'][y])
        irr = GISData['irr'][yearstr].copy()

        # STEP 5: calculate the total amount of irrigated lands from the GIS maps
    
        irrAx   = np.zeros((nregions,nSubRegion), dtype = float) # this is the max total available area of all grids with some irrigation
        irrA    = np.zeros((nregions,nSubRegion), dtype = float) # this is the existing area that is equipped with irrigation
        totA    = np.zeros((nregions,nSubRegion), dtype = float) # total land in each rgn, SubRegion combo
    
        for index in range(GISData['RegionIDs'].shape[0]):
            if GISData['area'][index] > 0 and GISData['RegionIDs'][index] > 0 and GISData['BasinIDs'][index] > 0:
                irrA[GISData['RegionIDs'][index]-1, GISData['BasinIDs'][index]-1] += irr[index]
                totA[GISData['RegionIDs'][index]-1, GISData['BasinIDs'][index]-1] += GISData['area'][index]
                if irr[index] > 0:
                    irrAx[GISData['RegionIDs'][index]-1, GISData['BasinIDs'][index]-1] += GISData['area'][index]
            else:
                irr[index] = 0
            
            
        # STEP 6:        
        for i in range(0,nregions):
            for j in range(0,nSubRegion):
                # To be efficient, the most important step in the loop is to identify the valid irr cell(index in 360*720 grid) for each region and each SubRegion
                ls = np.where((GISData['RegionIDs'] - 1 == i) & (GISData['BasinIDs'] - 1 == j))[0]
                if len(ls) > 0 and irr_A[i,j,y] > 0:                                    
                    ls1 = []
                    ls2 = []
                    for index in ls:                                    
                        if irr[index] == 0:
                            ls1.append(index)
                        else:
                            ls2.append(index)
                             
                    # if irrigation area appears in GCAM but not in GIS (none of the grids are equipped with irrigation in the selected year)
                    # uniformly distributed irrigation area based on the total area               
                    if irrA[i,j] == 0 or irrAx[i,j] == 0:
                        for index in ls:                        
                            irrA_grid[index, y] = GISData['area'][index]/totA[i,j]*irr_A[i,j,y]
                            #irrA_frac[index, y] = irr_A[i,j,y]/totA[i,j]                                
                    else:
                    # if irrigation area appears in both the GIS matrix and the GCAM output matrix, 
                    # then we need to scale up/down the values
                    # in the GIS grid map values to match GCAM total values                                                
                        diff = 99 
                        counter = 0
                        num_new = 0  
                        while diff > 0.00001:                       
                            # [i j counter diff]
                            cum_area = 0
                            cum_diff = 0
                            if counter == 0:
                                num = 0 
                                counter1 = 0
                                counter2 = 0
                                
                                for index in ls1:
                                    irrA_grid[index, y] = np.NaN
                                    #irrA_frac[index, y] = np.NaN
                                    counter2 += 1
                                
                                for index in ls2:
                                    z = irr[index]/irrA[i,j]*irr_A[i,j,y]
                                    irrA_grid[index, y] = min(z,GISData['area'][index])
                                    #irrA_frac[index, y] = irrA_grid[index, y]/mapAreaExt[index]
                                    if z > GISData['area'][index]:
                                        cum_diff += z - GISData['area'][index]
                                        counter1 += 1
                                    else:
                                        num  += 1
                                    cum_area += irrA_grid[index, y]
                                           
                                # if all irrigation grids (ls2) have irrigation area larger than total area (ls2)
                                # and no-irrigation grids (ls1) existed
                                # (total irrigation area (ls2) - total area) = irrigated areas are distributed uniformly over
                                # non-irrigated grids (ls1)
                                if num == 0 and counter2 > 0:
                                    cum_area1 = cum_area
                                    cum_diff = 0
                                    cum_area = 0
                                    cum_diff0 = 0
                                    z = (irr_A[i,j,y] - cum_area1)/counter2
                                    for index in ls1:                                        
                                        irrA_grid[index, y] = min(z,GISData['area'][index])
                                        #irrA_frac[index, y] = irrA_grid[index, y]/mapAreaExt[index]
                                        if z > GISData['area'][index]:
                                            cum_diff0 += z - GISData['area'][index]
                                        cum_area = cum_area1 + irrA_grid[index, y]
                                    if cum_diff0 > 0:
                                        # GCAM irr_A is too large, the redistributed ls1 still has grids that irrigated area > total area
                                        logging.info('{}  {}  {}  {} {} {} {} '.format(
                                            '[Year Index, Region ID,',
                                            GISData['SubRegionString'],
                                            'ID, irr from GCAM not assigned (km3) (condition 0)]         :',
                                            y+1, i+1, j+1,
                                            cum_diff0*irr_V[i,j,y]/irr_A[i,j,y]))
                            else: # if (num == 0 and counter2 == 0)  or num > 0 
                                for index in ls1:
                                    irrA_grid[index, y] = np.NaN
                                    #irrA_frac[index, y] = np.NaN
                                    
                                counter3 = 0     
                                for index in ls2:
                                    if irrA_grid[index, y] < GISData['area'][index]:
                                        z = irrA_grid[index, y] + diff/max(1,num)
                                        irrA_grid[index, y] = min(z,GISData['area'][index])
                                        #irrA_frac[index, y] = irrA_grid[index, y]/mapAreaExt[index]
                                        if z > GISData['area'][index]:
                                            cum_diff += z - GISData['area'][index]
                                            num_new  = num - 1
                                        cum_area += irrA_grid[index, y]   
                                    else:
                                        cum_area += irrA_grid[index, y]
                                        num_new  = num - 1
                                        counter3 += 1                                                                       
                                num = num_new
                                if cum_diff == 0 and counter3 == len(ls2):
                                    # GCAM irr_A is too large, the redistributed ls2 still has grids that irrigated area > total area
                                    logging.warning('{}  {}  {}  {} {} {} {} '.format(
                                        '[Year Index, Region ID,',
                                        GISData['SubRegionString'],
                                        'ID, irr from GCAM not assigned (km3) (condition 1)]         :',
                                        y+1, i+1, j+1,
                                        diff*irr_V[i,j,y]/irr_A[i,j,y]))
                            counter += 1
                            diff    = cum_diff
       
                    for index in ls:
                        if not np.isnan(irrA_grid[index, y]):                                      
                            withd_irr_map[index, y] = irrA_grid[index, y]*irr_V[i,j,y]/irr_A[i,j,y] 
                                                      
                elif len(ls) == 0 and irr_A[i,j,y] > 0 and irr_V[i,j,y] > 0:
                    # GCAM has irrigation data for a region and a SubRegion/basin.
                    # But from region map and SubRegion/basin map, there are no cells belong to both.
                    # Thus, GCAM data will not be included for downscaling.
                    # It will cause the difference in Spatial Downscaling diagnostics
                    logging.warning('{}  {}  {}  {} {} {} {} '.format('[Year Index, Region ID,',
                                        GISData['SubRegionString'],'ID, irr from GCAM not assigned (km3) (No overlapping cells)]:',
                                        y+1, i+1, j+1, irr_V[i,j,y]))

    withd_irr_map_259200 = np.full(ms, np.NaN, dtype=float)
    withd_irr_map_259200[GISData['mapindex']] = withd_irr_map

    # this loop will replace all the nan values with zeros to be able to take sums, if we want to keep the nans (for plotting), comment following 2 lines
    irrA_grid[np.isnan(irrA_grid)]         = 0
    withd_irr_map_259200[np.isnan(withd_irr_map_259200)] = 0
    
    # Total Agricultural Water withdrawal in years
    OUT.wdirr    = withd_irr_map_259200
    
    return withd_irr_map_259200
    
def IrrigationMapCrops(mapsize, GISData, GCAMData, NY, OUT):


    # Need to downscale the agricultural water withdrawal data for GCAM years
    # using the existing map of areas equipped with irrigation as a proxy for disaggregation from
    # SubRegion to grid scale CHALLENGE: where to add new agricultural lands

    # STEP 1: read in Basin grid map
    nSubRegion = np.amax(GISData['BasinIDs'])

    # STEP 2: calculate the total amount of irrigated lands in each GCAM region from the GCAM output files.
    # The irrArea file from GCAM has the format:
    # 1: GCAM regions 1-nrgn
    # 2: SubRegions 1-18
    # 3: crops 1-17
    # 4 .. nyear+3: values for GCAM output years
    # We are going to reorganize this into irrArea(rgn,SubRegion,crop,year)(but the name irrArea is already taken, so we'll call it tempA_all)
    nregions = GISData['nregions']
    r1 = GCAMData['irrArea'].shape[0]
    try:
        r2, q2 = GCAMData['irrShare'].shape
    except:
        r2, q2 = 0, 0
    r3 = GCAMData['irrV'].shape[0]
    ncrops    = max(max(GCAMData['irrArea'][:,2].astype(int)),max(GCAMData['irrV'][:,2].astype(int)))
    tempA_all = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    tempS_all = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    tempV_all = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    
    for i in range(0, r1):
        for y in range(0, NY):
            tempA_all[GCAMData['irrArea'][i, 0].astype(int)-1, GCAMData['irrArea'][i, 1].astype(int)-1, GCAMData['irrArea'][i, 2].astype(int)-1, y] = GCAMData['irrArea'][i, y+3]*1000
            # convert from thousands of km2 to km2
            
    # if irrShare was read in, then reorganize the same way we did with irrArea.
    # Otherwise, set all irrigation shares to one (indicating that irrArea really is irrigated area,
    # as calculated in GCAM, not total planted area, as in older versions of GCAM.)
    if r2 > 1 or  q2 > 1:
        for i in range(0,r2):
            for y in range (0,NY):
                tempS_all[GCAMData['irrShare'][i,0].astype(int)-1,GCAMData['irrShare'][i,1].astype(int)-1,GCAMData['irrShare'][i,2].astype(int)-1,y] = GCAMData['irrShare'][i,y+3]
    else:
        tempS_all = np.ones((nregions,nSubRegion,ncrops,NY), dtype = float)

    # Same reorganization for irrVolume. Result goes to tempV_all
    for i in range(0,r3):
        for y in range(0,NY):
            tempV_all[GCAMData['irrV'][i,0].astype(int)-1,GCAMData['irrV'][i,1].astype(int)-1,GCAMData['irrV'][i,2].astype(int)-1,y] = GCAMData['irrV'][i,y+3]
               
    # STEP 3: now that we have computed the total irrigated lands
    irr_A = np.zeros((nregions,nSubRegion,ncrops,NY), dtype = float)
    
    for i in range (0,nregions):
        for j in range(0,nSubRegion):
            for y in range(0,NY):
                for k in range(0,ncrops):                            
                    irr_A[i,j,k,y] = tempA_all[i,j,k,y]*tempS_all[i,j,k,y]
                    
    
    ms            = (mapsize[0]*mapsize[1],ncrops,NY)
    ms67420 = (GISData['RegionIDs'].shape[0], ncrops, NY)
    irrA_grid     = np.zeros(ms67420, dtype = float)
    #irrA_frac     = np.full(ms, np.NaN, dtype = float)
    withd_irr_map = np.zeros(ms67420, dtype = float) # GIS results
    
    # use historical irrigation area maps
    # STEP 4: read a grid map of the irrigated area in km2 in a certain year
    for y in range (0,NY):
        logging.debug('{}'.format(GISData['irr']['years'][y]))
        yearstr = str(GISData['irr']['years_new'][y])
        
        for k in range(0,ncrops): 
            irr = GISData['irr'][yearstr][:, k].copy()

            # STEP 5: calculate the total amount of irrigated lands from the GIS maps
    
            irrAx   = np.zeros((nregions,nSubRegion), dtype = float) # this is the max total available area of all grids with some irrigation
            irrA    = np.zeros((nregions,nSubRegion), dtype = float) # this is the existing area that is equipped with irrigation
            totA    = np.zeros((nregions,nSubRegion), dtype = float) # total land in each rgn, SubRegion combo

            for index in range(GISData['RegionIDs'].shape[0]):
                if GISData['area'][index] > 0 and GISData['RegionIDs'][index] > 0 and GISData['BasinIDs'][index] > 0:
                    irrA[GISData['RegionIDs'][index] - 1, GISData['BasinIDs'][index] - 1] += irr[index]
                    totA[GISData['RegionIDs'][index] - 1, GISData['BasinIDs'][index] - 1] += GISData['area'][index]
                    if irr[index] > 0:
                        irrAx[GISData['RegionIDs'][index] - 1, GISData['BasinIDs'][index] - 1] += GISData['area'][index]
                else:
                    irr[index] = 0
            
            
            # STEP 6:        
            for i in range(0,nregions):
                for j in range(0,nSubRegion):
                    # To be efficient, the most important step in the loop is to identify the valid irr cell(index in 360*720 grid) for each region and each SubRegion
                    ls = np.where((GISData['RegionIDs'] - 1 == i) & (GISData['BasinIDs'] - 1 == j))[0]
                    if len(ls) > 0 and irr_A[i,j,k,y] > 0:                                    
                        ls1 = []
                        ls2 = []
                        for index in ls:                                    
                            if irr[index] == 0:
                                ls1.append(index)
                            else:
                                ls2.append(index)
                                 
                        # if irrigation area appears in GCAM but not in GIS (none of the grids are equipped with irrigation in the selected year)
                        # uniformly distributed irrigation area based on the total area               
                        if irrA[i,j] == 0 or irrAx[i,j] == 0:
                            for index in ls:                        
                                irrA_grid[index, k, y] = GISData['area'][index]/totA[i,j]*irr_A[i,j,k,y]
                                #irrA_frac[index, y] = irr_A[i,j,y]/totA[i,j]                                
                        else:
                        # if irrigation area appears in both the GIS matrix and the GCAM output matrix, 
                        # then we need to scale up/down the values
                        # in the GIS grid map values to match GCAM total values                                                
                            diff = 99 
                            counter = 0
                            num_new = 0  
                            while diff > 0.00001:                       
                                # [i j counter diff]
                                cum_area = 0
                                cum_diff = 0
                                if counter == 0:
                                    num = 0 
                                    counter1 = 0
                                    counter2 = 0
                                    
                                    for index in ls1:
                                        irrA_grid[index, k, y] = 0
                                        #irrA_frac[index, y] = np.NaN
                                        counter2 += 1
                                    
                                    for index in ls2:
                                        z = irr[index]/irrA[i,j]*irr_A[i,j,k,y]
                                        irrA_grid[index,k,y] = min(z,GISData['area'][index])
                                        #irrA_frac[index, y] = irrA_grid[index, y]/mapAreaExt[index]
                                        if z > GISData['area'][index]:
                                            cum_diff += z - GISData['area'][index]
                                            counter1 += 1
                                        else:
                                            num  += 1
                                        cum_area += irrA_grid[index, k, y]
                                               
                                    # if all irrigation grids (ls2) have irrigation area larger than total area (ls2)
                                    # and no-irrigation grids (ls1) existed
                                    # (total irrigation area (ls2) - total area) = irrigated areas are distributed uniformly over
                                    # non-irrigated grids (ls1)
                                    if num == 0 and counter2 > 0:
                                        cum_area1 = cum_area
                                        cum_diff = 0
                                        cum_area = 0
                                        cum_diff0 = 0
                                        z = (irr_A[i,j,k,y] - cum_area1)/counter2
                                        for index in ls1:                                        
                                            irrA_grid[index, k, y] = min(z,GISData['area'][index])
                                            #irrA_frac[index, y] = irrA_grid[index, y]/mapAreaExt[index]
                                            if z > GISData['area'][index]:
                                                cum_diff0 += z - GISData['area'][index]
                                            cum_area = cum_area1 + irrA_grid[index, k, y]
                                        if cum_diff0 > 0:
                                            # GCAM irr_A is too large, the redistributed ls1 still has grids that irrigated area > total area
                                            logging.warning('{}  {}  {}  {} {} {} {} {}'.format(
                                                '[Year Index, Region ID,',
                                                GISData['SubRegionString'],
                                                'ID, Crop ID, irr from GCAM not assigned (km3) (condition 0)]         :',
                                                y+1, i+1, j+1, k+1,
                                                cum_diff0*tempV_all[i,j,k,y]/irr_A[i,j,k,y]))
                                else: # if (num == 0 and counter2 == 0)  or num > 0 
                                    for index in ls1:
                                        irrA_grid[index, k, y] = 0
                                        #irrA_frac[index, y] = np.NaN
                                        
                                    counter3 = 0     
                                    for index in ls2:
                                        if irrA_grid[index, k, y] < GISData['area'][index]:
                                            z = irrA_grid[index, k, y] + diff/max(1,num)
                                            irrA_grid[index, k, y] = min(z,GISData['area'][index])
                                            #irrA_frac[index, y] = irrA_grid[index, y]/mapAreaExt[index]
                                            if z > GISData['area'][index]:
                                                cum_diff += z - GISData['area'][index]
                                                num_new  = num - 1
                                            cum_area += irrA_grid[index, k, y]   
                                        else:
                                            cum_area += irrA_grid[index, k, y]
                                            num_new  = num - 1
                                            counter3 += 1                                                                       
                                    num = num_new
                                    if cum_diff == 0 and counter3 == len(ls2):
                                        # GCAM irr_A is too large, the redistributed ls2 still has grids that irrigated area > total area
                                        logging.warning('{}  {}  {}  {} {} {} {} {}'.format(
                                            '[Year Index, Region ID,',
                                            GISData['SubRegionString'],
                                            'ID, Crop ID, irr from GCAM not assigned (km3) (condition 1)]         :',
                                            y+1, i+1, j+1,  k+1,
                                            diff*tempV_all[i,j,k,y]/irr_A[i,j,k,y]))
                                counter += 1
                                diff    = cum_diff
           
                        for index in ls:
                            if irrA_grid[index,k, y] > 0:                                      
                                withd_irr_map[index, k, y] = irrA_grid[index, k, y]*tempV_all[i,j,k,y]/irr_A[i,j,k,y] 
                                                          
                    elif len(ls) == 0 and irr_A[i,j,k,y] > 0 and tempV_all[i,j,k,y] > 0:
                        # GCAM has irrigation data for a region and a SubRegion/basin.
                        # But from region map and SubRegion/basin map, there are no cells belong to both.
                        # Thus, GCAM data will not be included for downscaling.
                        # It will cause the difference in Spatial Downscaling diagnostics
                        logging.warning('{}  {}  {}  {} {} {} {} {}'.format('[Year Index, Region ID,',
                                            GISData['SubRegionString'],'ID, Crop ID, irr from GCAM not assigned (km3) (No overlapping cells)]:',
                                            y+1, i+1, j+1, k+1, tempV_all[i,j,k,y]))
                                        
    # this loop will replace all the nan values with zeros to be able to take sums, if we want to keep the nans (for plotting), comment following 2 lines
    #irrA_grid[np.isnan(irrA_grid)]         = 0
    #withd_irr_map[np.isnan(withd_irr_map)] = 0

    withd_irr_map_259200 = np.zeros(ms, dtype=float)
    withd_irr_map_259200[GISData['mapindex']] = withd_irr_map
    
    # Total Agricultural Water withdrawal in years
    OUT.wdirr       = np.sum(withd_irr_map_259200, axis=1)
    OUT.crops_wdirr = withd_irr_map_259200
    
    return withd_irr_map_259200

