"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""

import numpy as np
from scipy import io as spio
#from netCDF4 import Dataset

def OutWriter(Settings, OUT, GISData):
     
    if Settings.OutputUnit:
        temp = 'mm'
    else:
        temp = 'km3'
    
    if Settings.OutputFormat == 1:
        print 'Save the gridded water usage results for each withdrawal category in CSV format (Unit: '  + temp + '/yr)'
           
    elif Settings.OutputFormat == 2:
        print 'Save the gridded water usage results for each withdrawal category in NetCDF format (Unit: '  + temp + '/yr)'
        
    else:
        print 'Save the gridded water usage results for each withdrawal category in CSV and NetCDF format (Unit: '  + temp + '/yr)'
    
    if Settings.PerformTemporal:
        TDMonthStr = np.chararray((len(Settings.TDYears)*12,), itemsize=6)
        for y in Settings.TDYears:
            N = Settings.TDYears.index(y)
            TDMonthStr[N*12:(N+1)*12] = [str(y) + str(i).zfill(2) for i in range(1,13)]
        print 'Save the monthly water usage results for each withdrawal category (Unit: '  + temp + '/month)'
        
          
    for attr, value in OUT.__dict__.iteritems():
        if value is not None:
            OutputFilename = Settings.OutputFolder + attr
            if attr[0] == "r": # regional output
                newvalue   = value[:,:]
                #with open(OutputFilename + '.csv', 'w') as outfile:
                #    np.savetxt(outfile, newvalue, delimiter=',')
                          
            elif attr[0] == "w": # gridded output
                newvalue   = value[GISData['mapindex'],:]  # Only output 67420 cells (with coordinates)
                
                if Settings.OutputFormat == 1:          
                    writecsv(OutputFilename, newvalue, Settings, temp, GISData)
                elif Settings.OutputFormat == 2:
                    writeNETCDF(OutputFilename + '.nc', newvalue, GISData, temp, Settings.years)
                else:
                    writecsv(OutputFilename, newvalue, Settings, temp, GISData)
                    writeNETCDF(OutputFilename + '.nc', newvalue, GISData, temp, Settings.years)
                    
            elif attr[0] == "t": # temporal downscaling output
                if Settings.OutputFormat == 1:
                    writecsvMonthly(OutputFilename, value, TDMonthStr, temp, GISData)
                elif Settings.OutputFormat == 2:
                    writeNETCDFmonthly(OutputFilename + '.nc', value, GISData, temp, TDMonthStr)
                else:
                    writecsvMonthly(OutputFilename, value, TDMonthStr, temp, GISData)    
                    writeNETCDFmonthly(OutputFilename + '.nc', value, GISData, temp, TDMonthStr)
                    
def writecsv(filename, data, Settings, unit, GISData):
    unit       = "Unit(" + unit + "/yr)"
    if Settings.years:
        headerline = "ID,lon,lat,ilon,ilat," + ",".join([str(year) for year in Settings.years]) + "," + unit
    else:
        headerline = "ID,lon,lat,ilon,ilat," + ",".join(["Year Index " + str(y+1) for y in range(0, data.shape[1])]) + "," + unit
    with open(filename + '.csv', 'w') as outfile: 
        newdata = np.append(GISData['coord'][:,:],data, axis = 1)
        np.savetxt(outfile, newdata, delimiter=',', header=headerline)

def writecsvMonthly(filename, data, MonthStr, unit, GISData):
    unit       = "Unit(" + unit + "/month)"
    headerline = "ID,lon,lat,ilon,ilat," + ",".join([k for k in MonthStr]) + "," + unit
    with open(filename + '.csv', 'w') as outfile: 
        newdata = np.append(GISData['coord'][:,:],data, axis = 1)
        np.savetxt(outfile, newdata, delimiter=',', header=headerline)


def writeNETCDF(filename, data, GISData, unit, yearstrs):
    '''
    # Input:
    - filename    string, filename of netcdf file
    - data        2d array, row: number of cells (67420), col: number of years
    - GISData     structure, contains grid coordinates
    - unit        string, e.g. "mm" or 'km3'
    '''
    # open
#    datagrp = Dataset(filename, 'w', format='NETCDF4')
    datagrp = spio.netcdf.netcdf_file(filename, 'w')
    (nrows,ncols) = data.shape


    #Attributes
    #datagrp.description = ''
    
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
    griddata.description = 'Downscaled Results: 67420 rows, Number of Years columns'
    
        
    # data
    years[:]      = np.array(yearstrs).astype(int)
    ID[:]         = GISData['coord'][:,0].astype(int)
    lon[:]        = GISData['coord'][:,1]
    lat[:]        = GISData['coord'][:,2]
    ilon[:]       = GISData['coord'][:,3].astype(int)
    ilat[:]       = GISData['coord'][:,4].astype(int)
    map_index[:]  = GISData['mapindex'].astype(int) + 1

#    griddata[:, :] = data[:, :]
    griddata[:, :] = data[:, :].copy()    
    
    # close
    datagrp.close()
    
def writeNETCDFmonthly(filename, data, GISData, unit, monthstrs):
    '''
    # Input:
    - filename    string, filename of netcdf file
    - data        2d array, row: number of cells (67420), col: number of months
    - GISData     structure, contains grid coordinates
    - unit        string, e.g. "mm" or 'km3'
    '''
    # open

#    datagrp = Dataset(filename, 'w', format='NETCDF4')
    datagrp = spio.netcdf.netcdf_file(filename, 'w')    
    (nrows,ncols) = data.shape


    #Attributes
    #datagrp.description = ''
    
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
    griddata.description = 'Downscaled Results: 67420 rows, Number of Months columns'
    
        
    # data
    months[:]     = np.array(monthstrs).astype(int)
    ID[:]         = GISData['coord'][:,0].astype(int)
    lon[:]        = GISData['coord'][:,1]
    lat[:]        = GISData['coord'][:,2]
    ilon[:]       = GISData['coord'][:,3].astype(int)
    ilat[:]       = GISData['coord'][:,4].astype(int)
    map_index[:]  = GISData['mapindex'].astype(int) + 1
    
#    griddata[:, :] = data[:, :]
    griddata[:, :] = data[:, :].copy()  
    
    # close
    datagrp.close()