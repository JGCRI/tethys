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

Note we allow for (and in fact require) a single header line. The assumption is that there are two region mappings in play. The first is the 'ag' mapping, which covers agriculture (including land use), livestock, and (currently) mining. The second is the 'nonag' mapping, which covers everything else.

"""


import os
import numpy as np
from scipy import io as spio
#from netCDF4 import Dataset
from tethys.Utils.DataParser import GetArrayCSV, GetArrayTXT
from tethys.Utils.DataParser import getContentArray as ArrayCSVRead
from tethys.DataReader.HistPopIrrData import getPopYearData as GetPopData
from tethys.Utils.exceptions import FileNotFoundError


def getGISData(settings):
    # dictionary GISData{} saves the data related to GIS data
    GISData = {} 
        
    # AEZ mapping:  67420x1 -- 1-18, missing using 0
    GISData['aez']          = ArrayCSVRead(settings.aez,1).astype(int)
    
    # judge if use basin for aez
    if settings.subreg == 0:
        GISData['AEZstring'] = 'AEZ'
    elif settings.subreg == 1:
        GISData['AEZstring'] = 'Basin'
      
    # using finer resolution gridded population map (from HYDE or GPW) according to year availability
    GISData['pop']          = GetPopData(settings) # dictionary

    if settings.UseDemeter:
        # using finer resolution gridded Irrigation map (from demeter by individual crops) according to year availability
        from tethys.DataReader.HistPopIrrData import getIrrYearData_Crops as GetIrrData
    else:
        # using finer resolution gridded Irrigation map (from HYDE or GMIA) according to year availability
        from tethys.DataReader.HistPopIrrData import getIrrYearData as GetIrrData          
    
    GISData['irr']          = GetIrrData(settings) # dictionary   
    
    # Livestock (heads) in year 2000: dim is 67420x1 
    GISData['Buffalo']      = ArrayCSVRead(settings.Livestock_Buffalo,1)
    GISData['Cattle']       = ArrayCSVRead(settings.Livestock_Cattle,1)
    GISData['Goat']         = ArrayCSVRead(settings.Livestock_Goat,1)
    GISData['Sheep']        = ArrayCSVRead(settings.Livestock_Sheep,1)
    GISData['Poultry']      = ArrayCSVRead(settings.Livestock_Poultry,1)
    GISData['Pig']          = ArrayCSVRead(settings.Livestock_Pig,1)

    # Coordinates for flattened grd:  67420 x 5
    # The columns are ID#, lon, lat, ilon, ilat
    GISData['coord']        = ArrayCSVRead(settings.Coord,0)
    settings.coords         = GISData['coord'][:,:]
    # read area values for each land grid cell, convert from ha to km2
    GISData['area']         = ArrayCSVRead(settings.Area,0) * 0.01
    # read the latitude value for each cell [67420x1]
    
    GISData['mapAreaExt']   = None
    
    # Basin ID Map: 67420 x 1, 235 Basins
    GISData['BasinIDs'] = load_const_griddata(settings.InputBasinFile, 1).astype(int)

    # Corresponding to Basin ID Map, 235 Basin Names: 1D String Array
    GISData['BasinNames'] = load_const_griddata(settings.BasinNames)
    
    # Country ID Map : 67420 x 1 (249 countries: 1-249)
    GISData['CountryIDs'] = load_const_griddata(settings.InputCountryFile, 1).astype(int)

    # Corresponding to Country ID Map, 1-249 index number and 249 Country Names: 2D String Array
    with open(settings.CountryNames, 'r') as f:
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
            data = GetArrayTXT(fn, headerNum)
        except:
            with open(fn, 'r') as f:
                data = np.array(f.read().splitlines())

    elif fn.endswith('.csv'):
        data = GetArrayCSV(fn, headerNum)
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

def getRegionMapData(rgnmapfile):
    # read a table for looking up region by grid cell
    # All of these are two-column comma-separated tables.  Unassigned grid cells are
    # denoted by 0 in the second column.  Note we allow for (and in fact require) a single header line
    #   rgnmap - the lookup table.  First column is grid cell id; second is region number.
    #   nrgn   - the number of regions in this region mapping.
    
    # dictionary GISData{} saves the data related to region map data
    rgnmapData = {}
    # dim is 67420 x 2
    rgnmapData['rgnmapAG']      = ArrayCSVRead(rgnmapfile, 1).astype(int)
    rgnmapData['rgnmapNONAG']   = ArrayCSVRead(rgnmapfile, 1).astype(int)  
    rgnmapData['nrgnAG']        = max(rgnmapData['rgnmapAG'][:])   # Number of regions
    rgnmapData['nrgnNONAG']     = max(rgnmapData['rgnmapNONAG'][:])# Number of regions 
    rgnmapData['map_rgn_nonag'] = None
    rgnmapData['map_rgn_ag']    = None
    
    return rgnmapData

