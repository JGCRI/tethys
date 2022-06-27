"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import os
import re
import logging

import numpy as np
from tethys.utils.data_parser import get_array_csv


def getIrrYearData(Irrigation_GMIA, Irrigation_HYDE, years):
    """
    Update the irrigation maps to include a unique map for each historical time period
    """
    
    hyde_irr = get_array_csv(Irrigation_HYDE, 1)
    gmia_irr = get_array_csv(Irrigation_GMIA, 1).reshape(-1, 1)  # with only 1 year, resulting array is 1D, so reshape

    hyde_years = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]
    gmia_years = [2005]

    irr = {'years': years, 'array': np.zeros((len(gmia_irr), len(years)))}

    for y, year in enumerate(years):
        if year < min(hyde_years):
            irr['array'][:, y] = hyde_irr[:, 0]
            logging.info(f'------Use HYDE {min(hyde_years)} Irrigation Area Data for {year}')
        elif year < min(gmia_years):
            new_year = max(i for i in hyde_years if i <= year)
            irr['array'][:, y] = hyde_irr[:, hyde_years.index(new_year)]
            logging.info(f'------Use HYDE {new_year} Irrigation Area Data for {year}')
        else:
            new_year = max(i for i in gmia_years if i <= year)
            irr['array'][:, y] = gmia_irr[:, gmia_years.index(new_year)]
            logging.info(f'------Use FAO-GMIA {new_year} Irrigation Area Data for {year}')

    return irr


def getIrrYearData_Crops(DemeterOutputFolder, years):
    """
    Update the irrigation maps to include a unique map for each historical time period from Demeter outputs by crop types
    """
    
    irr = {}
    demeter_years = []  # is the range of years from Demeter outputs
    for filename in os.listdir(DemeterOutputFolder):  # Folder contains Demeter outputs in the fraction of a 0.5 degree grid cell
        if filename.endswith('.csv'):
            yearstr = re.sub("[^0-9]", "", filename)
            demeter_years.append(int(yearstr))
            if int(yearstr) in years:
                tmp = get_array_csv(os.path.join(DemeterOutputFolder, filename), 1)
                index = check_header_Demeter_outputs(os.path.join(DemeterOutputFolder, filename))
                # tmp[:, 1] is latitude
                area = np.cos(np.radians(tmp[:, 1])) * (111.32 * 110.57) * (0.5**2)  # 0.5 hardcoded!
                newdata = tmp[:, index] * area[:, np.newaxis]  # cell_crop_fraction * cell_area

                # While Tethys contains code to aggregate numerous subsectors into the biomass category (see l_biomass),
                # the only biomass outputs from GCAM databases I've seen are from biomass_grass and biomass_tree.
                # In all Demeter outputs I've seen, biomass_tree_irr == biomass_grass_irr.
                # As an initial method for downscaling the total biomass irrigation water demand,
                # we use biomass grass irrigation area as the proxy.
                # While this gives the correct total when biomass_tree_irr == biomass_grass_irr,
                # (the raw cell irrigation area does not matter, only the proportion to the basin total)
                # this may not always be guaranteed, or separate biomass_grass and biomass_tree outputs may be desired.
                # A more robust solution will involve some reworking of gcam_outputs.py

                irr[yearstr] = newdata

    years_new = years[:]
    for y, year in enumerate(years):
        # config_reader.py guarantees min(demeter_years) <= year
        years_new[y] = max(i for i in demeter_years if i <= year)
        logging.info(f'------Use Demeter {years_new[y]} Irrigation Area Data for {year}')
    
    irr['years'] = years  # years (integer) from settings
    irr['years_new'] = years_new  # years to import irrigation data (integer) corresponding to years

    # reorganize into an an array (will rewrite above to build this directly)
    nyears = len(years)
    ncells, ncrops = irr[str(irr['years_new'][0])].shape

    irr_new = {'array': np.zeros((ncells, ncrops, nyears), dtype=float)}
    for y, year in enumerate(years_new):
        irr_new['array'][:, :, y] = irr[str(year)]

    return irr_new


def getPopYearData(Population_GPW, Population_HYDE, years):
    """"
    Update the population maps to include a unique map for each historical time period
    """

    # could be rewritten to only load years/files that will be needed
    hyde_pop = get_array_csv(Population_HYDE, 1)
    gpw_pop = get_array_csv(Population_GPW, 1)

    hyde_years = [1750, 1760, 1770, 1780, 1790, 1800, 1810, 1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890,
                  1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980]
    gpw_years = [1990, 1995, 2000, 2005, 2010, 2015]

    pop = np.zeros((len(gpw_pop), len(years)))

    # build the population array used by PopulationMap
    for y, year in enumerate(years):
        if year < min(hyde_years):
            pop[:, y] = hyde_pop[:, 0]
            logging.info(f'------Use HYDE {min(hyde_years)} Population Data for {year}')
        elif year < min(gpw_years):
            new_year = max(i for i in hyde_years if i <= year)
            pop[:, y] = hyde_pop[:, hyde_years.index(new_year)]
            logging.info(f'------Use HYDE {new_year} Population Data for {year}')
        else:
            new_year = max(i for i in gpw_years if i <= year)
            pop[:, y] = gpw_pop[:, gpw_years.index(new_year)]
            logging.info(f'------Use GPW {new_year} Population Data for {year}')

    return pop


def check_header_Demeter_outputs(filename):
    # check the header (order) of the Demeter outputs are consistent and corresponding to the crops used in GCAM
    d_crops = ['biomass_grass_irr', 'corn_irr', 'fibercrop_irr', 'foddergrass_irr', 'fodderherb_irr',
               'misccrop_irr', 'oilcrop_irr', 'othergrain_irr', 'palmfruit_irr',
               'rice_irr', 'root_tuber_irr', 'sugarcrop_irr', 'wheat_irr']

    with open(filename, 'r') as file:
        headers = file.readline().strip().lower().replace('"', '').split(',')
        headers = [i.replace('"','') for i in headers]
    index = [headers.index(crop) for crop in d_crops]

    return index
