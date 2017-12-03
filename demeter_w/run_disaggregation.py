"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import time
from demeter_w.DataReader.GCAMOutputs import getGCAMData
from demeter_w.DataReader import GISReader
from demeter_w.DataWriter.OUTWriter import OUTSettings
from demeter_w.SpatialDownscaling.ProxyMaps import Rearranging
import demeter_w.SpatialDownscaling.ProxyMaps as ProxyMaps
import demeter_w.SpatialDownscaling.TotalWaterUse as TotalWaterUse
import demeter_w.Diagnostics.Spatial as DiagnosticsSD
import demeter_w.Diagnostics.Temporal as DiagnosticsTD
import demeter_w.TemporalDownscaling.TemporalDownscaling as TemporalDownscaling


def run_disaggregation(settings):
    '''
    License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
    Copyright (c) 2017, Battelle Memorial Institute

    Module: run_disaggregation

    Main Function of Demeter-W: Steps for water disaggregation
    1. Read in the GCAM Data and Get the number of years
    2. Read in the GIS data
    3. Rearranging data and map indices
    4. Create proxy maps for population, livestock and irrigation
       and downscale non-Agriculture (domestic, electricity, manufacturing and mining), 
       livestock and irrigation water withdrawals to grid scale
    5. Compute Total Water withdrawal
    6. Diagnostics of Spatial Downscaling
    7. Temporal Downscaling (annually -> monthly)
    8. Diagnostics of Temporal Downscaling

    # Input:
    - settings    class DataReader.ConfigSettings, required input and control parameters

    # Output:
    - OUT         class DataWriter.OUTWritter, data for output, gridded results for each withdrawal category
    '''

    # initialize output parameters
    OUT = OUTSettings()

    # 1. Read in the GCAMData
    # a.    Population tables
    # b.    irrigation tables
    # c.    livestock tables
    # d.    Results of water withdrawals from GCAM by sectors and regions
    starttime1 = time.time() # Set-up timer
    print '---Read in the GCAM data (csv format)---'
    settings.setGCAMDataFiles() # set the GCAM data files
    GCAMData = getGCAMData(settings)
    endtime1 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime1 - starttime1))

    # e. Get the number of years
    settings.years = map(int, settings.years)
    if settings.years:
        settings.NY = len(settings.years)
        print '---Number of years:', settings.NY
        print '------', settings.years
    else:
        (_, size) = GCAMData['pop_tot'].shape
        settings.NY = size
        print '---Number of years:', settings.NY

    # 2. Read in the GIS data
    # a.    Coordinates of grids
    # b.    Area of grids
    # c.    Population maps
    # d.    irrigation maps
    # e.    livestock maps
    # f.    mask shape files of GCAM regions, river basins, countries, states, etc.

    print '---Read in the GIS data (asc/txt/csv format) and the region map data (csv format)---'
    GISData    = GISReader.getGISData(settings)
    rgnmapData = GISReader.getRegionMapData(settings.InputRegionFile)
    endtime2 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime2 - endtime1))
    print '---Mapsize:', settings.mapsize

    # 3. Rearranging data and map indices
    #    Rearrange all the input data into a common framework (from 2D to 1D)
    print '---Rearranging data and map indices'
    Rearranging(settings.mapsize,GISData,rgnmapData)
    endtime3 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime3 - endtime2))

    # 4. Create proxy maps and downscale non-Agriculture (domestic, electricity, manufacturing and mining) water withdrawals to grid scale
    # a.    Create a population proxy map
    print '---Create a population map as proxy of non-agricultural water withdrawals'
    ProxyMaps.PopulationMap(settings.mapsize, GISData, GCAMData, rgnmapData, settings, OUT)
    endtime4 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime4 - endtime3))

    # b.    Create a livestock proxy map and downscale livestock water withdrawal to grid scale
    print '---Create an livestock map as proxy of livestock water withdrawal'
    ProxyMaps.LivestockMap(settings.mapsize, GISData, GCAMData, rgnmapData, settings.NY, OUT)
    endtime5 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime5 - endtime4))

    # c.    Create an irrigation proxy map and downscale irrigation water withdrawal to grid scale
    print '---Create an irrigation map as proxy of agricultural water withdrawal'
    ProxyMaps.IrrigationMap(settings.mapsize, GISData, GCAMData, rgnmapData, settings.NY, OUT)
    endtime6 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime6 - endtime5))

    # 5. Total Water Withdrawal
    print '---Aggregate to compute total water withdrawal at grid scale'
    TotalWaterUse.TotalWaterUse(settings, GISData, rgnmapData, OUT)
    endtime7 = time.time()
    print("------Time Cost: %s seconds ---" % (endtime7 - endtime6))

    # 6. Diagnostics of Spatial Downscaling
    if settings.PerformDiagnostics:
        DiagnosticsSD.compare_downscaled_GCAMinput(settings, GCAMData, OUT)


    # 7. Temporal Downscaling
    if settings.PerformTemporal:
        print '---Temporal downscaling for Domestic, Electricity, Irrigation, Livestock, Mining and Manufacturing'
        endtime6 = time.time()
        TemporalDownscaling.GetDownscaledResults(settings, OUT, GISData['mapindex'], rgnmapData['rgnmapNONAG'], GISData['BasinIDs'])
        endtime7 = time.time()
        print("------Time Cost: %s seconds ---" % (endtime7 - endtime6))

    # 8. Diagnostics of Temporal Downscaling
    if settings.PerformDiagnostics and settings.PerformTemporal:
        DiagnosticsTD.compare_temporal_downscaled(settings, OUT, GISData)


    return OUT, GISData
