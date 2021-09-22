"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""

import time
import logging

from tethys.data_reader.gcam_outputs import get_gcam_data
from tethys.data_reader import gis_reader
from tethys.data_writer.outputs import OUTSettings
from tethys.spatial_downscaling.proxy_maps import Rearranging
import tethys.spatial_downscaling.proxy_maps as ProxyMaps
import tethys.spatial_downscaling.total_water_use as TotalWaterUse
import tethys.diagnostics.spatial_diagnostics as DiagnosticsSD
import tethys.diagnostics.temporal_diagnostics as DiagnosticsTD
import tethys.temporal_downscaling.temporal_downscaling as TemporalDownscaling


def run_disaggregation(years, InputRegionFile, mapsize, subreg, UseDemeter, PerformDiagnostics,
                       PerformTemporal, RegionNames, gcam_basin_lu, buff_fract, goat_fract, GCAM_DBpath,
                       GCAM_DBfile, GCAM_query, OutputFolder, temporal_climate, Irr_MonthlyData,
                       TemporalInterpolation, Domestic_R, Elec_Building, Elec_Industry, Elec_Building_heat,
                       Elec_Building_cool, Elec_Building_others, Livestock_Buffalo, Livestock_Cattle, Livestock_Goat,
                       Livestock_Sheep, Livestock_Poultry, Livestock_Pig, Coord, Area, InputBasinFile, BasinNames,
                       InputCountryFile, CountryNames,Irrigation_GMIA, Irrigation_HYDE, DemeterOutputFolder,
                       Population_GPW, Population_HYDE, OutputUnit):
    """Main Function of Tethys Steps for water disaggregation

    :param x:    x description
    :type x:     x type here

    Main Function of Tethys Steps for water disaggregation
    1. Read in the GCAM Data and Get the number of years
    2. Read in the GIS data
    3. Rearranging data and map indices
    4. Create proxy maps for population, livestock and irrigation
       and downscale non-Agriculture (domestic, electricity, manufacturing and mining), 
       livestock and irrigation water withdrawals to grid scale
    5. Compute Total Water withdrawal
    6. diagnostics of Spatial Downscaling
    7. Temporal Downscaling (annually -> monthly)
    8. diagnostics of Temporal Downscaling

    # Output:
    - OUT         class data_writer.OUTWritter, data for output, gridded results for each withdrawal category
    """

    # initialize output parameters
    OUT = OUTSettings()

    # 1. Read in the GCAMData
    # a.    Population tables
    # b.    irrigation tables
    # c.    livestock tables
    # d.    Results of water withdrawals from GCAM by sectors and regions
    starttime1 = time.time()  # Set-up timer
    logging.info('---Read in and format GCAM data---')

    GCAMData = get_gcam_data(years=years,
                             RegionNames=RegionNames,
                             gcam_basin_lu=gcam_basin_lu,
                             buff_fract=buff_fract,
                             goat_fract=goat_fract,
                             GCAM_DBpath=GCAM_DBpath,
                             GCAM_DBfile=GCAM_DBfile,
                             GCAM_query=GCAM_query,
                             subreg=subreg)
    endtime1 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime1 - starttime1))

    # e. Get the number of years
    years = [int(i) for i in years]
    if years:
        NY = len(years)
        logging.info('---Number of years: {}'.format(NY))
        logging.info('------ {}'.format(str(years)))
    else:
        (_, size) = GCAMData['pop_tot'].shape
        NY = size
        logging.info('---Number of years: {}'.format(NY))

    # 2. Read in the GIS data
    # a.    Coordinates of grids
    # b.    Area of grids
    # c.    Population maps
    # d.    irrigation maps
    # e.    livestock maps
    # f.    mask shape files of GCAM regions, river basins, countries, states, etc.

    logging.info(
        '---Read in the GIS data (asc/txt/csv format) and the region map data (csv format)---')
    GISData = gis_reader.getGISData(UseDemeter=UseDemeter,
                                    Livestock_Buffalo=Livestock_Buffalo,
                                    Livestock_Cattle=Livestock_Cattle,
                                    Livestock_Goat=Livestock_Goat,
                                    Livestock_Sheep=Livestock_Sheep,
                                    Livestock_Poultry=Livestock_Poultry,
                                    Livestock_Pig=Livestock_Pig,
                                    Coord=Coord,
                                    Area=Area,
                                    InputBasinFile=InputBasinFile,
                                    BasinNames=BasinNames,
                                    InputCountryFile=InputCountryFile,
                                    CountryNames=CountryNames,
                                    Population_GPW=Population_GPW,
                                    Population_HYDE=Population_HYDE,
                                    years=years,
                                    Irrigation_GMIA=Irrigation_GMIA,
                                    Irrigation_HYDE=Irrigation_HYDE,
                                    DemeterOutputFolder=DemeterOutputFolder
                                    )
    rgnmapData = gis_reader.getRegionMapData(InputRegionFile)
    endtime2 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime2 - endtime1))
    logging.info('---Mapsize: {}'.format(mapsize))

    # 3. Rearranging data and map indices
    #    Rearrange all the input data into a common framework (from 2D to 1D)
    logging.info('---Rearranging data and map indices')
    Rearranging(mapsize, GISData, rgnmapData)
    endtime3 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime3 - endtime2))

    # 4. Create proxy maps and downscale non-Agriculture (domestic, electricity, manufacturing and mining) water
    #    withdrawals to grid scale
    # a.    Create a population proxy map
    logging.info('---Create a population map as proxy of non-agricultural water withdrawals')
    ProxyMaps.PopulationMap(mapsize, GISData, GCAMData, rgnmapData, OUT, NY)
    endtime4 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime4 - endtime3))

    # b.    Create a livestock proxy map and downscale livestock water withdrawal to grid scale
    logging.info('---Create an livestock map as proxy of livestock water withdrawal')
    ProxyMaps.LivestockMap(mapsize, GISData, GCAMData, rgnmapData, NY, OUT)
    endtime5 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime5 - endtime4))

    # c.    Create an irrigation proxy map and downscale irrigation water withdrawal to grid scale
    if UseDemeter:
        # Use Demeter outputs (irrigated cropland areas for each type of crops ) to replace the GMIA/HYSE data used in downscaling of irrigation water withdrawal
        # Additional gridded outputs: irrigation water withdrawal by 13 crop types
        logging.info('---Create an irrigation map as proxy of agricultural water withdrawal using Demeter outputs')
        ProxyMaps.IrrigationMapCrops(mapsize, GISData, GCAMData, rgnmapData, NY, OUT, subreg)
    else:
        logging.info('---Create an irrigation map as proxy of agricultural water withdrawal ')
        ProxyMaps.IrrigationMap(mapsize, GISData, GCAMData, rgnmapData, NY, OUT, subreg)

    endtime6 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime6 - endtime5))

    # 5. Total Water Withdrawal
    logging.info('---Aggregate to compute total water withdrawal at grid scale')
    TotalWaterUse.TotalWaterUse(OutputUnit=OutputUnit,
                                GISData=GISData,
                                rgnmapData=rgnmapData,
                                OUT=OUT)
    endtime7 = time.time()
    logging.info("------Time Cost: %s seconds ---" % (endtime7 - endtime6))

    # 6. diagnostics of Spatial Downscaling
    if PerformDiagnostics:
        DiagnosticsSD.compare_downscaled_GCAMinput(PerformDiagnostics=PerformDiagnostics,
                                                   NY=NY,
                                                   years=years,
                                                   OutputFolder=OutputFolder,
                                                   RegionNames= RegionNames,
                                                   GCAMData=GCAMData,
                                                   OUT=OUT)
    if UseDemeter:
        DiagnosticsSD.compare_downscaled_GCAMinput_irr_by_crops(PerformDiagnostics=PerformDiagnostics,
                                                                NY=NY,
                                                                years=years,
                                                                GCAMData=GCAMData,
                                                                OUT=OUT)

    # 7. Temporal Downscaling
    if PerformTemporal:
        logging.info(
            '---Temporal downscaling for Domestic, Electricity, Irrigation, Livestock, Mining and Manufacturing')
        endtime6 = time.time()
        TDYears = TemporalDownscaling.GetDownscaledResults(temporal_climate=temporal_climate,
                                                           Irr_MonthlyData=Irr_MonthlyData,
                                                           years=years,
                                                           UseDemeter=UseDemeter,
                                                           TemporalInterpolation=TemporalInterpolation,
                                                           Domestic_R=Domestic_R,
                                                           Elec_Building=Elec_Building,
                                                           Elec_Industry=Elec_Industry,
                                                           Elec_Building_heat=Elec_Building_heat,
                                                           Elec_Building_cool=Elec_Building_cool,
                                                           Elec_Building_others=Elec_Building_others,
                                                           coords=GISData['coord'][:,:],
                                                           OUT=OUT,
                                                           mapindex=GISData['mapindex'],
                                                           regionID=rgnmapData['rgnmapNONAG'],
                                                           basinID=GISData['BasinIDs'])
        print(f'TDyears = {TDYears}')
        endtime7 = time.time()
        logging.info("------Time Cost: %s seconds ---" % (endtime7 - endtime6))

    # 8. diagnostics of Temporal Downscaling
    if PerformDiagnostics and PerformTemporal:
        DiagnosticsTD.compare_temporal_downscaled(PerformDiagnostics=PerformDiagnostics,
                                                  TDYears=TDYears,
                                                  OutputFolder=OutputFolder,
                                                  OUT=OUT,
                                                  GISData=GISData)

    return OUT, GISData
