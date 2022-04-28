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

import os
import numpy as np
from scipy import io as spio
from tethys.utils.data_parser import get_array_csv, get_array_txt
from tethys.data_reader.hist_pop_irr_data import getPopYearData as GetPopData
from tethys.utils.exceptions import FileNotFoundError


def getGISData(UseDemeter, Livestock_Buffalo, Livestock_Cattle,Livestock_Goat, Livestock_Sheep,
               Livestock_Poultry, Livestock_Pig, Coord, Area, InputRegionFile, InputBasinFile, BasinNames,
               InputCountryFile, CountryNames, Irrigation_GMIA, Irrigation_HYDE, years, DemeterOutputFolder,
               Population_GPW, Population_HYDE):
    # dictionary GISData{} saves the data related to GIS data
    GISData = dict()

    GISData['RegionIDs'] = get_array_csv(InputRegionFile, 1).astype(int)
    GISData['nregions'] = GISData['RegionIDs'].max()  # Number of regions
    GISData['map_rgn'] = None

    GISData['SubRegionString'] = 'Basin'

    # using finer resolution gridded population map (from HYDE or GPW) according to year availability
    GISData['pop'] = GetPopData(Population_GPW=Population_GPW,
                                Population_HYDE=Population_HYDE,
                                years=years)  # dictionary

    if UseDemeter:
        # using finer resolution gridded Irrigation map (from HYDE or GMIA) according to year availability
        from tethys.data_reader.hist_pop_irr_data import getIrrYearData_Crops as GetIrrData
        GISData['irr'] = GetIrrData(DemeterOutputFolder=DemeterOutputFolder,
                                    years=years)  # dictionary
    else:
        # using finer resolution gridded Irrigation map (from demeter by individual crops) according to year availability
        from tethys.data_reader.hist_pop_irr_data import getIrrYearData as GetIrrData
        GISData['irr'] = GetIrrData(Irrigation_GMIA=Irrigation_GMIA,
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
    #coords = GISData['coord'][:, :]
    # read area values for each land grid cell, convert from ha to km2
    GISData['area'] = get_array_csv(Area, 0) * 0.01
    # read the latitude value for each cell [67420x1]

    GISData['mapAreaExt'] = None

    # Basin ID Map: 67420 x 1, 235 Basins
    GISData['BasinIDs'] = load_const_griddata(InputBasinFile, 1).astype(int)

    # Corresponding to Basin ID Map, 235 Basin Names: 1D String Array
    GISData['BasinNames'] = load_const_griddata(BasinNames)

    # Country ID Map : 67420 x 1 (249 countries: 1-249)
    GISData['CountryIDs'] = load_const_griddata(InputCountryFile, 1).astype(int)

    # Corresponding to Country ID Map, 1-249 index number and 249 Country Names: 2D String Array
    with open(CountryNames, 'r') as f:
        temp = f.read().splitlines()
        GISData['CountryNames'] = np.array([i.split(',') for i in temp])[:, 1]

    return GISData


def load_mat_var(fn, varname):
    if not os.path.isfile(fn):
        raise FileNotFoundError(fn)

    temp = spio.loadmat(fn)
    data = temp[varname]

    return data


def load_const_griddata(fn, headerNum=0, key=" "):
    # Load constant grid data stored in files defined in GRID_CONSTANTS.

    if not os.path.isfile(fn):
        raise FileNotFoundError(fn)

    if fn.endswith('.mat'):
        data = load_mat_var(fn, key)

    elif fn.endswith('.txt'):
        try:
            data = get_array_txt(fn, headerNum)
        except:
            with open(fn, 'r') as f:
                data = np.array(f.read().splitlines())

    elif fn.endswith('.csv'):
        data = get_array_csv(fn, headerNum)
        all_zeros = not np.any(data)
        if all_zeros:
            try:
                with open(fn, 'r') as f:
                    data = np.array(f.read().splitlines())
            except:
                pass

    elif fn.endswith('.nc'):
        #        datagrp = Dataset(fn, 'r', format='NETCDF4')
        datagrp = spio.netcdf.netcdf_file(fn, 'r')

        # copy() added to handle numpy 'ValueError:assignment destination is read-only' related to non-contiguous memory
        try:
            #            data = datagrp[key][:, :]
            data = datagrp.variables[key][:, :].copy()
        except:
            #            data = datagrp[key][:]
            data = datagrp.variables[key][:].copy()

        datagrp.close()

    return data
