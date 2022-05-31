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


def PopulationMap(GISData, GCAMData, OUT, nyears):
    """
    Population density map is used to downscale non-agricultural water withdrawal

    :param GISData: dictionary with population arrays, region mappings, and other data
    :param GCAMData: dictionary with GCAM water demand and population data
    :param OUT: OUTSettings object that will hold downscaled results
    :param nyears: number of years
    """

    # ncells x nyears population array, filter out invalid regions
    pop = np.where(GISData['RegionIDs'][:, np.newaxis] > 0, GISData['pop'], 0)

    # calculate total region population according to gridded maps
    pop_total = np.zeros((GISData['nregions'], nyears), dtype=float)
    for i in range(GISData['nregions']):
        index = np.where(GISData['RegionIDs'] == i + 1)[0]
        pop_total[i] = np.sum(pop[index], axis=0)

    region_indices = GISData['RegionIDs'] - 1  # convert to 0 indexed values

    # ratio of cell population to region population for all cells and years
    pop_pro_rata = pop / pop_total[region_indices]

    # the actual downscaling calculations
    OUT.wddom = pop_pro_rata * GCAMData['rgn_wddom'][region_indices]
    OUT.wdelec = pop_pro_rata * GCAMData['rgn_wdelec'][region_indices]
    OUT.wdmfg = pop_pro_rata * GCAMData['rgn_wdmfg'][region_indices]
    OUT.wdmin = pop_pro_rata * GCAMData['rgn_wdmining'][region_indices]
    OUT.wdnonag = OUT.wddom + OUT.wdelec + OUT.wdmfg + OUT.wdmin


def LivestockMap(GISData, GCAMData, nyears, OUT):
    """
    Livestock gridded GIS data maps by six types are used to downscale livestock Water withdrawal 
    """

    # count how many animals live in each GCAM region first
    nregions = GISData['nregions']
    ncells = len(GISData['RegionIDs'])
    animals = ['Buffalo', 'Cattle', 'Goat', 'Sheep', 'Poultry', 'Pig']

    tot_livestock = np.zeros((nregions, 6), dtype=float)  # Livestock totals at GCAM scale in year 2005
    for i, region in enumerate(GISData['RegionIDs']):
        if region > 0:
            for a, animal in enumerate(animals):
                tot_livestock[region - 1, a] += GISData[animal][i]
  
    #  now create a spatial distribution for each GCAM region
    #  withd_liv: these are the GCAM results of total volume of livestock water withdrawal in
    #  km3 in each GCAM region per animal type in the years 1990, 2005:5:2095
    #  variables are nrgn GCAM regions x 6 animals (1:Buffalo, 2:Cattle, 3-Goat, 4-Sheep, 5-Poultry, 6-Pig)
    # 
    #  Next, we distribute those volumes using the spatial distribution of the gis maps
    # these will be the GIS downscaled matrices

    withd_liv_map = np.zeros((ncells, nyears), dtype=float)
    for y in range(nyears):
        livestock = np.zeros((ncells, 6), dtype=float)
        for i, region in enumerate(GISData['RegionIDs']):
            if region > 0:
                for a, animal in enumerate(animals):
                    if GISData[animal][i] != 0:
                        livestock[i, a] = GCAMData['wdliv'][a*nregions + region - 1, y] * GISData[animal][i] \
                                          / tot_livestock[region - 1, a]
        withd_liv_map[:, y] = np.sum(livestock, axis=1)

    OUT.wdliv = withd_liv_map

    # Diagnostic message
    fmtstr = '[Year Index, Region ID, {:7s} from GCAM not assigned (no GIS data)]:  {}  {}  {}'
    for y in range(nyears):
        for IN in range(nregions):
            for a, animal in enumerate(animals):
                if GCAMData['wdliv'][a*nregions + IN, y] > 0 and tot_livestock[IN, a] == 0:
                    logging.info(fmtstr.format(animal.lower(), y+1, IN+1, GCAMData['wdliv'][a*nregions + IN, y]))

    return withd_liv_map

def IrrigationMap(GISData, GCAMData, nyears, UseDemeter, OUT):

    ncells = len(GISData['RegionIDs'])
    ncrops = int(max(GCAMData['irrV'][:, 2]))

    irr_demand_map = np.zeros((ncells, ncrops, nyears), dtype=float)
    irr_area_map = np.zeros((ncells, nyears), dtype=float)

    # build dict to look up GCAM irrigation area
    gcam_irr_areas = {}
    for row in GCAMData['irrArea']:
        region = int(row[0])
        basin = int(row[1])
        crop = int(row[2]) - 1
        for year in range(nyears):
            gcam_irr_areas[region, basin, crop, year] = row[year + 3] * 1000  # convert to km^2 from thousands of km^2

    for row in GCAMData['irrV']:  # row looks like [region, basin, crop, year1, year2, ...]
        region = int(row[0])
        basin = int(row[1])
        crop = int(row[2]) - 1  # convert to array index
        if (region, basin) in GISData['RegionBasins']:  # check if intersection has any cells
            cells = GISData['RegionBasins'][region, basin]  # indices of cells in intersection
            for year in range(nyears):
                if UseDemeter:
                    irr_area = GISData['irr']['array'][cells, crop, year]  # Demeter crop irrigation area map
                else:
                    irr_area = GISData['irr']['array'][cells, year]  # irrigation area map

                if np.any(irr_area > 0):  # if irrigated cells exist in the intersection use them as proxy
                    irr_distribution = irr_area / np.sum(irr_area)
                else:  # otherwise downscale in proportion to total land area
                    logging.warning(f'No gridded irrigation data for region {region}, basin {basin}')
                    irr_distribution = GISData['area'][cells] / np.sum(GISData['area'][cells])
                    
                irr_demand_map[cells, crop, year] = row[year + 3] * irr_distribution
                irr_area_map[cells, year] += gcam_irr_areas[region, basin, crop, year] * irr_distribution
        else:
            logging.warning(f'No intersection for region {region}, basin {basin}, demand dropped')

    # find cells where implied irrigated area is greater than total land area
    for (region, basin) in GISData['RegionBasins']:
        cells = GISData['RegionBasins'][region, basin]
        for year in range(nyears):
            if np.any(irr_area_map[cells, year] > GISData['area'][cells]):
                logging.warning(f'Cells with implied irrigation area > total land area in region {region}, basin {basin}, year {year}')

    # Total Agricultural Water withdrawal in years
    OUT.wdirr = np.sum(irr_demand_map, axis=1)
    if UseDemeter:
        OUT.crops_wdirr = irr_demand_map
