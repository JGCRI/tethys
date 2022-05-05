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

    years = [int(x) for x in years]

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
    D_irr = {}

    for filename in os.listdir(DemeterOutputFolder):  # Folder contains Demeter outputs in the fraction of a 0.5 degree grid cell
        if filename.endswith('.csv'):
            yearstr = re.sub("[^0-9]", "", filename)
            demeter_years.append(int(yearstr))

    demeter_years = [number for number in demeter_years if number in years]
    demeter_years = sorted(demeter_years)
    years_new = years[:]
    inter = list(set(demeter_years) & set(years))  # intersection of Demeter years and GCAM years

    for filename in os.listdir(DemeterOutputFolder):  # Folder contains Demeter outputs in the fraction of a 0.5 degree grid cell
        if filename.endswith('.csv'):
            yearstr = re.sub("[^0-9]", "", filename)
            if int(yearstr) in inter:
                tmp = get_array_csv(os.path.join(DemeterOutputFolder, filename), 1)
                index = check_header_Demeter_outputs(os.path.join(DemeterOutputFolder, filename))
                # tmp[:, 1] is latitude
                area = np.cos(np.radians(tmp[:, 1])) * (111.32 * 110.57) * (0.5**2)  # 0.5 hardcoded!
                newdata = tmp[:, index] * area[:, np.newaxis]  # cell_crop_fraction * cell_area
                newdata = np.insert(newdata, 0, 0, axis=1)  # no fraction data from Demeter for biomass, all zeros
                D_irr[yearstr] = newdata

    for i in range(len(years)):
        if years[i] >= max(demeter_years):
            years_new[i] = max(demeter_years)
        else:
            for j in range(len(demeter_years)-1):
                if years[i] >= demeter_years[j] and years[i] < demeter_years[j+1]:
                    years_new[i] = demeter_years[j]  # use previous year
                    
        if not str(years_new[i]) in irr:
            irr[str(years_new[i])] = D_irr[str(years_new[i])][:, :]
        logging.info('------Use Demeter ' + str(years_new[i]) + ' Irrigation Area Data for ' + str(years[i]))
    
    irr['years'] = years  # years (integer) from settings
    irr['years_new'] = years_new  # years to import irrigation data (integer) corresponding to years

    return irr


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
    years = [int(x) for x in years]

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
    d_crops = ['corn_irr', 'fibercrop_irr', 'foddergrass_irr','fodderherb_irr',
               'misccrop_irr', 'oilcrop_irr', 'othergrain_irr', 'palmfruit_irr',
               'rice_irr', 'root_tuber_irr', 'sugarcrop_irr', 'wheat_irr']

    with open(filename, 'r') as file:
        headers = file.readline().strip().lower().split(',')

    index = [headers.index(crop) for crop in d_crops]

    return index
