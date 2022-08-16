"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import os
import logging

import numpy as np
import netCDF4 as nc4


class OUTSettings:
    """
    Output file names
    """

    def __init__(self):
        
        # gridded results, 2D array, size: (360*720, NY)
        self.wdtotal = None
        self.wdnonag = None
        self.wddom = None
        self.wdelec = None
        self.wdmfg = None
        self.wdmin = None
        self.wdirr = None
        self.wdliv = None
        
        # regional aggregates, 2D array, size: (NRegion, NY)
        self.rtotal = None
        self.rnonag = None
        self.rdom = None
        self.relec = None
        self.rmfg = None
        self.rmin = None
        self.rirr = None
        self.rliv = None


def write_outputs(OutputUnit, OutputFormat, OutputFolder, PerformTemporal, TDYears, years, OUT, GISData):
    
    # Names of the 13 crop types
    d_crops = ['biomass', 'Corn', 'FiberCrop', 'FodderGrass', 'FodderHerb', 'MiscCrop', 'OilCrop', 'OtherGrain',
               'PalmFruit', 'Rice', 'Root_Tuber', 'SugarCrop', 'Wheat']

    if OutputUnit:
        unit = 'mm'
    else:
        unit = 'km3'

    if OutputFormat == 1:
        msg = f'Save the gridded water usage results for each withdrawal category in CSV format (Unit: {unit}/yr)'
    elif OutputFormat == 2:
        msg = f'Save the gridded water usage results for each withdrawal category in NetCDF format (Unit: {unit}/yr)'
    else:
        msg = f'Save the gridded water usage results for each withdrawal category in CSV and NetCDF format (Unit: {unit}/yr)'

    logging.info(msg)

    if PerformTemporal:
        logging.info(f'Save the monthly water usage results for each withdrawal category (Unit: {unit}/month)')

        TDMonthStr = [str(y) + str(i).zfill(2) for y in TDYears for i in range(1, 13)]

    for attr, value in OUT.__dict__.items():
        # only want OUT.wd*, OUT.twd*, OUT.crops_wdirr, or OUT.crops_twdirr
        if attr[0] in ('w', 't', 'c') and value is not None:
            OutputFilename = os.path.join(OutputFolder, attr)

            if attr.startswith('crops_t') or attr.startswith('t'):
                timestep, timestr = 'month', TDMonthStr  # set monthly options
            else:
                timestep, timestr = 'year', years  # set year options

            if attr.startswith('crops_'):
                for i in range(value.shape[1]):  # iterate over crops
                    newvalue = value[:, i, :]
                    filename = OutputFilename + '_' + d_crops[i]
                    if OutputFormat == 1 or OutputFormat == 0:
                        write_csv(filename, newvalue, timestr, unit, GISData)
                    if OutputFormat == 2 or OutputFormat == 0:
                        write_netcdf(filename + '.nc', newvalue, timestr, unit, GISData, timestep=timestep)
            else:  # non-crop output
                if OutputFormat == 1 or OutputFormat == 0:
                    write_csv(OutputFilename, value, timestr, unit, GISData)
                if OutputFormat == 2 or OutputFormat == 0:
                    write_netcdf(OutputFilename + '.nc', value, timestr, unit, GISData, timestep=timestep)


def write_csv(filename, data, timestrs, unit, GISData):

    headerline = 'Grid_ID,lon,lat,ilon,ilat,' + ','.join([str(time) for time in timestrs])

    with open('{}_{}peryr.csv'.format(filename, unit), 'w') as outfile:
        newdata = np.append(GISData['coord'][:, :], data, axis=1)
        np.savetxt(outfile, newdata, delimiter=',', header=headerline, comments='')


def write_netcdf(filename, data, timestrs, unit, GISData, timestep='year'):
    """
    Input:
    - filename    string, filename of netcdf file
    - data        2d array, row: number of cells (67420), col: number of years
    - GISData     structure, contains grid coordinates
    - unit        string, e.g. "mm" or 'km3'
    """

    datagrp = nc4.Dataset(filename, 'w')
    (nrows, ncols) = data.shape

    # dimensions
    datagrp.createDimension('index', nrows)
    datagrp.createDimension(timestep, ncols)

    # create variables
    # Add the columns from coordinates: ID#, lon, lat, ilon, ilat
    time = datagrp.createVariable(f'{timestep}s', 'i4', (timestep,))
    ID = datagrp.createVariable('ID', 'i4', ('index',))
    lon = datagrp.createVariable('lon', 'f4', ('index',))
    lat = datagrp.createVariable('lat', 'f4', ('index',))
    ilon = datagrp.createVariable('ilon', 'i4', ('index',))
    ilat = datagrp.createVariable('ilat', 'i4', ('index',))
    griddata = datagrp.createVariable('data', 'f4', ('index', timestep))
    griddata.units = f'{unit}/{"yr" if timestep == "year" else "month"}'
    griddata.description = f'Downscaled Results: {nrows} rows, {ncols} columns ({timestep}s)'

    # write data to file variables
    time[:] = np.array(timestrs).astype(int)
    ID[:] = GISData['coord'][:, 0].astype(int)
    lon[:] = GISData['coord'][:, 1]
    lat[:] = GISData['coord'][:, 2]
    ilon[:] = GISData['coord'][:, 3].astype(int)
    ilat[:] = GISData['coord'][:, 4].astype(int)
    griddata[:] = data[:].copy()

    datagrp.close()
