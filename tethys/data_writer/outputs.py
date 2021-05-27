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
from scipy import io as spio


class OUTSettings:
    """
    Output file names
    """

    def __init__(self):
        
        # gridded results, 2D array, size: (360*720, NY)
        self.wdtotal  = None
        self.wdnonag  = None
        self.wddom    = None
        self.wdelec   = None
        self.wdmfg    = None
        self.wdmin    = None
        self.wdirr    = None
        self.wdliv    = None
        
        # regional aggregates, 2D array, size: (NRegion, NY)
        self.rtotal   = None
        self.rnonag   = None
        self.rdom     = None
        self.relec    = None
        self.rmfg     = None
        self.rmin     = None
        self.rirr     = None
        self.rliv     = None


def write_outputs(Settings, OUT, GISData):
    
    # Names of the 13 crop types
    d_crops = ['biomass', 'Corn', 'FiberCrop', 'FodderGrass', 'FodderHerb', 'MiscCrop', 'OilCrop', 'OtherGrain',
               'PalmFruit', 'Rice', 'Root_Tuber', 'SugarCrop', 'Wheat']
    
    if Settings.OutputUnit:
        temp = 'mm'
    else:
        temp = 'km3'

    # CSV
    if Settings.OutputFormat == 1:
        msg = f'Save the gridded water usage results for each withdrawal category in CSV format (Unit: {temp}/yr)'
        logging.info(msg)

    # NetCDF
    elif Settings.OutputFormat == 2:
        msg = f'Save the gridded water usage results for each withdrawal category in NetCDF format (Unit: {temp}/yr)'
        logging.info(msg)

    # Both
    else:
        msg = f'Save the gridded water usage results for each withdrawal category in CSV and NetCDF format (Unit: {temp}/yr)'
        logging.info(msg)
    
    if Settings.PerformTemporal:
        TDMonthStr = np.chararray((len(Settings.TDYears)*12,), itemsize=6)

        for y in Settings.TDYears:
            N = Settings.TDYears.index(y)
            TDMonthStr[N*12:(N+1)*12] = [str(y) + str(i).zfill(2) for i in range(1,13)]

        logging.info(f'Save the monthly water usage results for each withdrawal category (Unit: {temp}/month)')

    for attr in list(OUT.__dict__.keys()):
        value = OUT.__dict__[attr]

        if value is not None:
            OutputFilename = os.path.join(Settings.OutputFolder, attr)

            if attr[0] == "r": # regional output
                newvalue   = value[:, :]

            # gridded output from spatial downscaling
            elif attr[0] == "w":

                # Only output 67420 cells (with coordinates)
                newvalue   = value[GISData['mapindex'],:]
                
                if Settings.OutputFormat == 1:          
                    writecsv(OutputFilename, newvalue, Settings, temp, GISData)
                elif Settings.OutputFormat == 2:
                    writeNETCDF(OutputFilename + '.nc', newvalue, GISData, temp, Settings.years)
                else:
                    writecsv(OutputFilename, newvalue, Settings, temp, GISData)
                    writeNETCDF(OutputFilename + '.nc', newvalue, GISData, temp, Settings.years)

            #  gridded output from temporal downscaling
            elif attr[0] == "t":
                if Settings.OutputFormat == 1:
                    writecsvMonthly(OutputFilename, value, TDMonthStr, temp, GISData)

                elif Settings.OutputFormat == 2:
                    writeNETCDFmonthly(OutputFilename + '.nc', value, GISData, temp, TDMonthStr)

                else:
                    writecsvMonthly(OutputFilename, value, TDMonthStr, temp, GISData)    
                    writeNETCDFmonthly(OutputFilename + '.nc', value, GISData, temp, TDMonthStr)

            # for outputs, divided twdirr by crops for additional files when using Demeter outputs
            elif attr[:7] == 'crops_t':
                for i in range(value.shape[1]):
                    newvalue   = value[:,i,:]
                    if Settings.OutputFormat == 1:          
                        writecsvMonthly(OutputFilename + '_' + d_crops[i], newvalue, TDMonthStr, temp, GISData)
                    elif Settings.OutputFormat == 2:
                        writeNETCDFmonthly(OutputFilename + '_' + d_crops[i] + '.nc', newvalue, GISData, temp, TDMonthStr)
                    else:
                        writecsvMonthly(OutputFilename + '_' + d_crops[i], newvalue, TDMonthStr, temp, GISData)
                        writeNETCDFmonthly(OutputFilename + '_' + d_crops[i] + '.nc', newvalue, GISData, temp, TDMonthStr)

            # for outputs, divided wdirr by crops for additional files when using Demeter outputs
            elif attr[:7] == 'crops_w':
                for i in range(value.shape[1]):
                    newvalue   = value[GISData['mapindex'],i,:]
                    if Settings.OutputFormat == 1:          
                        writecsv(OutputFilename + '_' + d_crops[i], newvalue, Settings, temp, GISData)
                    elif Settings.OutputFormat == 2:
                        writeNETCDF(OutputFilename + '_' + d_crops[i] + '.nc', newvalue, GISData, temp, Settings.years)
                    else:
                        writecsv(OutputFilename + '_' + d_crops[i], newvalue, Settings, temp, GISData)
                        writeNETCDF(OutputFilename + '_' + d_crops[i] + '.nc', newvalue, GISData, temp, Settings.years)


def writecsv(filename, data, Settings, unit, GISData):

    if Settings.years:
        headerline = "Grid_ID,lon,lat,ilon,ilat," + ",".join([str(year) for year in Settings.years])
    else:
        headerline = "Grid_ID,lon,lat,ilon,ilat," + ",".join(["Year Index " + str(y+1) for y in range(0, data.shape[1])])

    with open('{}_{}peryr.csv'.format(filename, unit), 'w') as outfile:
        newdata = np.append(GISData['coord'][:, :], data, axis=1)
        np.savetxt(outfile, newdata, delimiter=',', header=headerline, comments='')


def writecsvMonthly(filename, data, MonthStr, unit, GISData):

    mth_str = ','.join(map(bytes.decode, MonthStr))
    headerline = "Grid_ID,lon,lat,ilon,ilat," + mth_str

    with open('{}_{}permonth.csv'.format(filename, unit), 'w') as outfile:
        newdata = np.append(GISData['coord'][:, :], data, axis=1)
        np.savetxt(outfile, newdata, delimiter=',', header=headerline, comments='')


def writeNETCDF(filename, data, GISData, unit, yearstrs):
    """
    Input:
    - filename    string, filename of netcdf file
    - data        2d array, row: number of cells (67420), col: number of years
    - GISData     structure, contains grid coordinates
    - unit        string, e.g. "mm" or 'km3'
    """
    datagrp = spio.netcdf.netcdf_file(filename, 'w')
    (nrows,ncols) = data.shape

    # dimensions
    datagrp.createDimension('index', nrows)
    datagrp.createDimension('year', ncols)    
    
    # variables
    # Add the columns from coordinates: ID#, lon, lat, ilon, ilat
    years     = datagrp.createVariable('years', 'i4', ('year',))
    ID        = datagrp.createVariable('ID', 'i4', ('index',))
    lon       = datagrp.createVariable('lon', 'f4', ('index',))
    lat       = datagrp.createVariable('lat', 'f4', ('index',))
    ilon      = datagrp.createVariable('ilon', 'i4', ('index',))
    ilat      = datagrp.createVariable('ilat', 'i4', ('index',))
    map_index = datagrp.createVariable('mapindex', 'i4', ('index',))
    griddata  = datagrp.createVariable('data', 'f4', ('index', 'year'))
    griddata.units = unit + '/yr'
    griddata.description = 'Downscaled Results: ' + str(nrows) + ' rows, ' + str(ncols) + ' columns (years)'    
        
    # data
    years[:]      = np.array(yearstrs).astype(int)
    ID[:]         = GISData['coord'][:,0].astype(int)
    lon[:]        = GISData['coord'][:,1]
    lat[:]        = GISData['coord'][:,2]
    ilon[:]       = GISData['coord'][:,3].astype(int)
    ilat[:]       = GISData['coord'][:,4].astype(int)
    map_index[:]  = GISData['mapindex'].astype(int) + 1

    # griddata[:, :] = data[:, :]
    griddata[:, :] = data[:, :].copy()    
    
    # close
    datagrp.close()


def writeNETCDFmonthly(filename, data, GISData, unit, monthstrs):
    """
    Input:
    - filename    string, filename of netcdf file
    - data        2d array, row: number of cells (67420), col: number of months
    - GISData     structure, contains grid coordinates
    - unit        string, e.g. "mm" or 'km3'
    """
    
    # open
    datagrp = spio.netcdf.netcdf_file(filename, 'w')
    (nrows,ncols) = data.shape

    # dimensions
    datagrp.createDimension('index', nrows)
    datagrp.createDimension('month', ncols)    
    
    # variables
    # Add the columns from coordinates: ID#, lon, lat, ilon, ilat
    months    = datagrp.createVariable('months', 'i4', ('month',))
    ID        = datagrp.createVariable('ID', 'i4', ('index',))
    lon       = datagrp.createVariable('lon', 'f4', ('index',))
    lat       = datagrp.createVariable('lat', 'f4', ('index',))
    ilon      = datagrp.createVariable('ilon', 'i4', ('index',))
    ilat      = datagrp.createVariable('ilat', 'i4', ('index',))
    map_index = datagrp.createVariable('mapindex', 'i4', ('index',))
    griddata  = datagrp.createVariable('data', 'f4', ('index', 'month'))
    griddata.units = unit + '/month'
    griddata.description = 'Downscaled Results: ' + str(nrows) + ' rows, ' + str(ncols) + ' columns (months)'
     
    # data
    months[:]     = np.array(monthstrs).astype(int)
    ID[:]         = GISData['coord'][:,0].astype(int)
    lon[:]        = GISData['coord'][:,1]
    lat[:]        = GISData['coord'][:,2]
    ilon[:]       = GISData['coord'][:,3].astype(int)
    ilat[:]       = GISData['coord'][:,4].astype(int)
    map_index[:]  = GISData['mapindex'].astype(int) + 1
    
    griddata[:, :] = data[:, :].copy()
    
    # close
    datagrp.close()
