"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""

import time
from tethys.DataReader.GCAMOutputs import get_gcam_data
from tethys.DataReader import GISReader
from tethys.DataWriter.OUTWriter import OUTSettings
from tethys.SpatialDownscaling.ProxyMaps import Rearranging
import tethys.SpatialDownscaling.ProxyMaps as ProxyMaps
import tethys.SpatialDownscaling.TotalWaterUse as TotalWaterUse
import tethys.Diagnostics.Spatial as DiagnosticsSD
import tethys.Diagnostics.Temporal as DiagnosticsTD
import tethys.TemporalDownscaling.TemporalDownscaling as TemporalDownscaling
from tethys.Utils.Logging import Logger

def run_disaggregation(settings):

    mainlog = Logger.getlogger()
    oldlvl = mainlog.setlevel(Logger.INFO)
    
    # initialize output parameters
    OUT = OUTSettings()

    # 1. Read in the GCAMData
    # a.    Population tables
    # b.    irrigation tables
    # c.    livestock tables
    # d.    Results of water withdrawals from GCAM by sectors and regions
    starttime1 = time.time() # Set-up timer
    mainlog.write('---Read in and format GCAM data---\n')

    GCAMData = get_gcam_data(settings)
    endtime1 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime1 - starttime1))

    # e. Get the number of years
    settings.years = [int(i) for i in settings.years]
    if settings.years:
        settings.NY = len(settings.years)
        mainlog.write('---Number of years: {}\n'.format(settings.NY))
        mainlog.write('------ {}\n'.format(str(settings.years)))
    else:
        (_, size) = GCAMData['pop_tot'].shape
        settings.NY = size
        mainlog.write('---Number of years: {}\n'.format(settings.NY))

    # 2. Read in the GIS data
    # a.    Coordinates of grids
    # b.    Area of grids
    # c.    Population maps
    # d.    irrigation maps
    # e.    livestock maps
    # f.    mask shape files of GCAM regions, river basins, countries, states, etc.

    mainlog.write(
        '---Read in the GIS data (asc/txt/csv format) and the region map data (csv format)---\n')
    GISData    = GISReader.getGISData(settings)
    rgnmapData = GISReader.getRegionMapData(settings.InputRegionFile)
    endtime2 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime2 - endtime1))
    mainlog.write('---Mapsize: {}\n'.format(settings.mapsize))

    # 3. Rearranging data and map indices
    #    Rearrange all the input data into a common framework (from 2D to 1D)
    mainlog.write('---Rearranging data and map indices\n')
    Rearranging(settings.mapsize,GISData,rgnmapData)
    endtime3 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime3 - endtime2))

    # 4. Create proxy maps and downscale non-Agriculture (domestic, electricity, manufacturing and mining) water
    #    withdrawals to grid scale
    # a.    Create a population proxy map
    mainlog.write('---Create a population map as proxy of non-agricultural water withdrawals\n')
    ProxyMaps.PopulationMap(settings.mapsize, GISData, GCAMData, rgnmapData, settings, OUT)
    endtime4 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime4 - endtime3))

    # b.    Create a livestock proxy map and downscale livestock water withdrawal to grid scale
    mainlog.write('---Create an livestock map as proxy of livestock water withdrawal\n')
    ProxyMaps.LivestockMap(settings.mapsize, GISData, GCAMData, rgnmapData, settings.NY, OUT)
    endtime5 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime5 - endtime4))

    # c.    Create an irrigation proxy map and downscale irrigation water withdrawal to grid scale
    mainlog.write('---Create an irrigation map as proxy of agricultural water withdrawal\n')
    ProxyMaps.IrrigationMap(settings.mapsize, GISData, GCAMData, rgnmapData, settings.NY, OUT, settings.subreg)
    endtime6 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime6 - endtime5))

    # 5. Total Water Withdrawal
    mainlog.write('---Aggregate to compute total water withdrawal at grid scale\n')
    TotalWaterUse.TotalWaterUse(settings, GISData, rgnmapData, OUT)
    endtime7 = time.time()
    mainlog.write("------Time Cost: %s seconds ---\n" % (endtime7 - endtime6))

    # 6. Diagnostics of Spatial Downscaling
    if settings.PerformDiagnostics:
        DiagnosticsSD.compare_downscaled_GCAMinput(settings, GCAMData, OUT)

    # 7. Temporal Downscaling
    if settings.PerformTemporal:
        mainlog.write(
            '---Temporal downscaling for Domestic, Electricity, Irrigation, Livestock, Mining and Manufacturing\n')
        endtime6 = time.time()
        TemporalDownscaling.GetDownscaledResults(settings, OUT, GISData['mapindex'], rgnmapData['rgnmapNONAG'], GISData['BasinIDs'])
        endtime7 = time.time()
        mainlog.write("------Time Cost: %s seconds ---\n" % (endtime7 - endtime6))

    # 8. Diagnostics of Temporal Downscaling
    if settings.PerformDiagnostics and settings.PerformTemporal:
        DiagnosticsTD.compare_temporal_downscaled(settings, OUT, GISData)

    return OUT, GISData
