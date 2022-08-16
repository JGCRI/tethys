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
import pandas as pd
from tethys.utils.data_parser import get_array_csv
from tethys.data_reader.hist_pop_irr_data import getPopYearData, getIrrYearData, getIrrYearData_Crops, downscaleSpatialInputs, getKeyCoordinates


def getGISData(UseDemeter, Livestock_Buffalo, Livestock_Cattle, Livestock_Goat, Livestock_Sheep,
               Livestock_Poultry, Livestock_Pig, Coord, Area, InputRegionFile, InputBasinFile, BasinNames,
               Irrigation_GMIA, Irrigation_HYDE, years, DemeterOutputFolder,
               Population_GPW, Population_HYDE, SpatialResolution):
    # dictionary GISData{} saves the data related to GIS data
    GISData = dict()


    key = getKeyCoordinates(Coord, SpatialResolution)
    print(key.head())
    
    # using finer resolution gridded population map (from HYDE or GPW) according to year availability
    GISData['pop'] = getPopYearData(Population_GPW=Population_GPW,
                                    Population_HYDE=Population_HYDE,
                                    years=years, 
                                    SpatialResolution = SpatialResolution,
                                    key_df = key)  # dictionary

    if UseDemeter:
        # using finer resolution gridded Irrigation map (from demeter by individual crops) according to year availability
        GISData['irr'] = getIrrYearData_Crops(DemeterOutputFolder=DemeterOutputFolder,
                                              years=years,
                                              SpatialResolution=SpatialResolution,
                                              key_df = key)
    else:
        # using finer resolution gridded Irrigation map (from HYDE or GMIA) according to year availability
        GISData['irr'] = getIrrYearData(Irrigation_GMIA=Irrigation_GMIA,
                                        Irrigation_HYDE=Irrigation_HYDE,
                                        years=years,
                                        SpatialResolution=SpatialResolution,
                                        key_df = key)  # dictionary
                                        
    # Livestock (heads) in year 2000: dim is 4x67420x1  # TODO: update to latest version of dataset
    if(SpatialResolution != .5):
        GISData['Livestock'] = np.stack([downscaleSpatialInputs(spatial_in = Livestock_Buffalo, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=1) +
                                         downscaleSpatialInputs(spatial_in = Livestock_Cattle, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=1),
                                         downscaleSpatialInputs(spatial_in = Livestock_Goat, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=1) +
                                         downscaleSpatialInputs(spatial_in = Livestock_Sheep, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=1),
                                         downscaleSpatialInputs(spatial_in = Livestock_Poultry, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=1),
                                         downscaleSpatialInputs(spatial_in = Livestock_Pig, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=1)]).reshape(4,-1,1)
    else:
        GISData['Livestock'] = np.stack([get_array_csv(Livestock_Buffalo, 1) + get_array_csv(Livestock_Cattle, 1),
                                     get_array_csv(Livestock_Goat, 1) + get_array_csv(Livestock_Sheep, 1),
                                     get_array_csv(Livestock_Poultry, 1),
                                     get_array_csv(Livestock_Pig, 1)]).reshape(4, -1, 1)
    
    # TODO: be explicit about array reshaping to catch errors rather than using -1 (dimension constants?)

    # Coordinates for flattened grd:  67420 x 5
    # The columns are ID#, lon, lat, ilon, ilat
    if(SpatialResolution != .5):
        coord_df = key
        coord_df['ilat'] = pd.DataFrame(coord_df['y']).rank(axis=0, method='dense').astype(int)
        coord_df['ilon'] = pd.DataFrame(coord_df['x']).rank(axis=0, method='dense').astype(int)
        coord_df = coord_df[["New_ID", "y", "x", "ilat", "ilon"]]
        GISData['coord'] = coord_df.to_numpy()
    else:
        GISData['coord'] = get_array_csv(Coord, 0)

    # read area values for each land grid cell, convert from ha to km2
    if(SpatialResolution != .5):
        GISData['area'] = downscaleSpatialInputs(spatial_in = Area, key_df=key, down_type='dist', SpatialResolution=SpatialResolution, skip_header=0) * 0.01
    else:
        GISData['area'] = get_array_csv(Area, 0) * 0.01
    
    
    # Basin ID Map: 67420 x 1, 235 Basins
    if(SpatialResolution != .5):
        GISData['BasinIDs'] = downscaleSpatialInputs(spatial_in = InputBasinFile, key_df=key, down_type='eq', SpatialResolution=SpatialResolution, skip_header=1).astype(int)
    else:
       GISData['BasinIDs'] = get_array_csv(InputBasinFile, 1).astype(int)

    # Corresponding to Basin ID Map, 235 Basin Names: 1D String Array
    with open(BasinNames, 'r') as f:
        GISData['BasinNames'] = f.read().splitlines()

    # 67420 valid "land cells"
    if(SpatialResolution != .5):
        GISData['RegionIDs'] = downscaleSpatialInputs(spatial_in = InputRegionFile, key_df=key, down_type='eq', SpatialResolution=SpatialResolution, skip_header=1).astype(int)
    else:
        GISData['RegionIDs'] = get_array_csv(InputRegionFile, 1).astype(int)
   
    
    GISData['nregions'] = GISData['RegionIDs'].max()  # Number of regions

    GISData['RegionBasins'] = dict()
    for i, pair in enumerate(zip(GISData['RegionIDs'], GISData['BasinIDs'])):
        if (pair[0] != 0):
            if pair not in GISData['RegionBasins']:
                GISData['RegionBasins'][pair] = list()
            GISData['RegionBasins'][pair].append(i)
    for pair in GISData['RegionBasins']:
        GISData['RegionBasins'][pair] = np.array(GISData['RegionBasins'][pair])

    GISData['basinlookup'] = dict()
    for i, basin in enumerate(GISData['BasinIDs']):
        if basin not in GISData['basinlookup']:
            GISData['basinlookup'][basin] = list()
        GISData['basinlookup'][basin].append(i)
    for basin in GISData['basinlookup']:
        GISData['basinlookup'][basin] = np.array(GISData['basinlookup'][basin])

    GISData['regionlookup'] = dict()
    for i, region in enumerate(GISData['RegionIDs']):
        if region != 0:
            if region not in GISData['regionlookup']:
                GISData['regionlookup'][region] = list()
            GISData['regionlookup'][region].append(i)
    for region in GISData['regionlookup']:
        GISData['regionlookup'][region] = np.array(GISData['regionlookup'][region])

    return GISData
