"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

This reader will reading the following three types of input files:
1. asc input files that were generated in GIS for baseyear disaggregation of water withdrawals.
2. other input files that were generated in GIS
3. region map files. All of these are two-column comma-separated tables.

Note we allow for (and in fact require) a single header line. The assumption is that there are two region mappings in
play. The first is the 'ag' mapping, which covers agriculture (including land use), livestock, and (currently) mining.
The second is the 'nonag' mapping, which covers everything else.

"""

import numpy as np
from tethys.utils.data_parser import get_array_csv
from tethys.data_reader.hist_pop_irr_data import getPopYearData, getIrrYearData, getIrrYearData_Crops
from tethys.utils.utils_math import sub2ind


def getGISData(UseDemeter, Livestock_Buffalo, Livestock_Cattle, Livestock_Goat, Livestock_Sheep,
               Livestock_Poultry, Livestock_Pig, Coord, Area, InputRegionFile, InputBasinFile, BasinNames,
               InputCountryFile, CountryNames, Irrigation_GMIA, Irrigation_HYDE, years, DemeterOutputFolder,
               Population_GPW, Population_HYDE, mapsize):
    # dictionary GISData{} saves the data related to GIS data
    GISData = dict()

    # using finer resolution gridded population map (from HYDE or GPW) according to year availability
    GISData['pop'] = getPopYearData(Population_GPW=Population_GPW,
                                    Population_HYDE=Population_HYDE,
                                    years=years)  # dictionary

    if UseDemeter:
        # using finer resolution gridded Irrigation map (from demeter by individual crops) according to year availability
        GISData['irr'] = getIrrYearData_Crops(DemeterOutputFolder=DemeterOutputFolder,
                                              years=years)  # dictionary
    else:
        # using finer resolution gridded Irrigation map (from HYDE or GMIA) according to year availability
        GISData['irr'] = getIrrYearData(Irrigation_GMIA=Irrigation_GMIA,
                                        Irrigation_HYDE=Irrigation_HYDE,
                                        years=years)  # dictionary

    # Livestock (heads) in year 2000: dim is 67420x1 
    GISData['Buffalo'] = get_array_csv(Livestock_Buffalo, 1)
    GISData['Cattle'] = get_array_csv(Livestock_Cattle, 1)
    GISData['Goat'] = get_array_csv(Livestock_Goat, 1)
    GISData['Sheep'] = get_array_csv(Livestock_Sheep, 1)
    GISData['Poultry'] = get_array_csv(Livestock_Poultry, 1)
    GISData['Pig'] = get_array_csv(Livestock_Pig, 1)

    # Coordinates for flattened grd:  67420 x 5
    # The columns are ID#, lon, lat, ilon, ilat
    GISData['coord'] = get_array_csv(Coord, 0)
    GISData['mapindex'] = sub2ind(mapsize, GISData['coord'][:, 4].astype(int)-1, GISData['coord'][:, 3].astype(int)-1)

    # read area values for each land grid cell, convert from ha to km2
    GISData['area'] = get_array_csv(Area, 0) * 0.01

    # Basin ID Map: 67420 x 1, 235 Basins
    GISData['BasinIDs'] = get_array_csv(InputBasinFile, 1).astype(int)

    # Corresponding to Basin ID Map, 235 Basin Names: 1D String Array
    with open(BasinNames, 'r') as f:
        GISData['BasinNames'] = f.read().splitlines()

    # Country ID Map : 67420 x 1 (249 countries: 1-249)
    GISData['CountryIDs'] = get_array_csv(InputCountryFile, 1).astype(int)

    # Corresponding to Country ID Map, 1-249 index number and 249 Country Names: 2D String Array
    with open(CountryNames, 'r') as f:
        temp = f.read().splitlines()
        GISData['CountryNames'] = np.array([i.split(',') for i in temp])[:, 1]

    # 67420 valid "land cells"
    GISData['RegionIDs'] = get_array_csv(InputRegionFile, 1).astype(int)
    GISData['nregions'] = GISData['RegionIDs'].max()  # Number of regions

    GISData['RegionBasins'] = dict()
    for i, pair in enumerate(zip(GISData['RegionIDs'], GISData['BasinIDs'])):
        if pair[0] != 0:
            if pair not in GISData['RegionBasins']:
                GISData['RegionBasins'][pair] = list()
            GISData['RegionBasins'][pair].append(i)
    for pair in GISData['RegionBasins']:
        GISData['RegionBasins'][pair] = np.array(GISData['RegionBasins'][pair])

    return GISData
