"""
License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

Get the simulator settings from configuration(*.ini) file

@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0
"""

import os
from configobj import ConfigObj
from tethys.DataReader.ConfigSettings import ConfigSettings
from tethys.Utils.exceptions import FileNotFoundError, DirectoryNotFoundError
from tethys.Utils.Logging import Logger


def getSimulatorSettings(iniFile):
    
    config = ConfigObj(iniFile)
    settings = ConfigSettings()

    try:
        settings.Logger = config['Logger']
    except KeyError:
        # No logger configuration.  Supply a default one for backward compatibility with old config files.
        settings.Logger = {'logdir':'logs',
                           'filename':'mainlog.txt'} 

    # project level params
    settings.ProjectName        = config['Project']['ProjectName']
    settings.InputFolder        = config['Project']['InputFolder']
    settings.OutputFolder       = os.path.join(config['Project']['OutputFolder'], settings.ProjectName)
    settings.rgnmapdir          = config['Project']['rgnmapdir']
    settings.OutputFormat       = int(config['Project']['OutputFormat'])
    settings.OutputUnit         = int(config['Project']['OutputUnit'])
    settings.PerformDiagnostics = int(config['Project']['PerformDiagnostics'])
    settings.PerformTemporal    = int(config['Project']['PerformTemporal'])
    settings.subreg             = int(config['Project']['subreg'])

    # spatial params
    try:
        settings.SpatialResolution = float(config['Project']['SpatialResolution'])
    except:
        settings.SpatialResolution = 0.5
    settings.mapsize = [int(180/settings.SpatialResolution), int(360/settings.SpatialResolution)]

    # GCAM access settings
    settings.UseGCAMDatabase         = int(config['GCAM']['UseGCAMDatabase'])
    if settings.UseGCAMDatabase:
        settings.GCAM_DBpath         = os.path.join(settings.InputFolder, config['GCAM']['GCAM_DBpath'])
        settings.GCAM_DBfile         = config['GCAM']['GCAM_DBfile']
        settings.GCAM_query          = os.path.join(settings.GCAM_DBpath, config['GCAM']['GCAM_query'])
        
    else:
        settings.read_irrS          = int(config['GCAM']['Read_irrS'])
        settings.GCAM_CSV = config['GCAM']['GCAM_CSV']

    settings.years              = config['GCAM']['GCAM_Years'] 

    # reference data
    settings.Area               = os.path.join(settings.InputFolder, config['GriddedMap']['Area'])
    settings.Coord              = os.path.join(settings.InputFolder, config['GriddedMap']['Coord'])
    settings.aez                = os.path.join(settings.InputFolder, config['GriddedMap']['AEZ'])
    settings.InputBasinFile     = os.path.join(settings.InputFolder, config['GriddedMap']['BasinIDs'])
    settings.BasinNames         = os.path.join(settings.InputFolder, config['GriddedMap']['BasinNames'])
    settings.gcam_basin_lu      = os.path.join(settings.InputFolder, config['GriddedMap']['GCAM_Basin_Key'])
    settings.InputRegionFile    = os.path.join(settings.InputFolder, config['GriddedMap']['RegionIDs'])
    settings.RegionNames        = os.path.join(settings.InputFolder, config['GriddedMap']['RegionNames'])
    settings.InputCountryFile   = os.path.join(settings.InputFolder, config['GriddedMap']['CountryIDs'])
    settings.CountryNames       = os.path.join(settings.InputFolder, config['GriddedMap']['CountryNames'])
    settings.Population_GPW     = os.path.join(settings.InputFolder, config['GriddedMap']['Population_GPW'])
    settings.Population_HYDE    = os.path.join(settings.InputFolder, config['GriddedMap']['Population_HYDE'])
    settings.Irrigation_GMIA    = os.path.join(settings.InputFolder, config['GriddedMap']['Irrigation_GMIA'])
    settings.Irrigation_HYDE    = os.path.join(settings.InputFolder, config['GriddedMap']['Irrigation_HYDE'])
    settings.Livestock_Buffalo  = os.path.join(settings.InputFolder, config['GriddedMap']['Livestock_Buffalo'])
    settings.Livestock_Cattle   = os.path.join(settings.InputFolder, config['GriddedMap']['Livestock_Cattle'])
    settings.Livestock_Goat     = os.path.join(settings.InputFolder, config['GriddedMap']['Livestock_Goat'])
    settings.Livestock_Sheep    = os.path.join(settings.InputFolder, config['GriddedMap']['Livestock_Sheep'])
    settings.Livestock_Poultry  = os.path.join(settings.InputFolder, config['GriddedMap']['Livestock_Poultry'])
    settings.Livestock_Pig      = os.path.join(settings.InputFolder, config['GriddedMap']['Livestock_Pig'])
    settings.buff_fract         = os.path.join(settings.InputFolder, config['GriddedMap']['Buffalo_Fraction'])
    settings.goat_fract         = os.path.join(settings.InputFolder, config['GriddedMap']['Goat_Fraction'])
    settings.irrigated_fract    = os.path.join(settings.InputFolder, config['GriddedMap']['Irrigated_Fract'])

    if settings.PerformTemporal:
        settings.TempMonthlyFile       = config['TemporalDownscaling']['Temp_Monthly']
        settings.HDDCDDMonthlyFile     = config['TemporalDownscaling']['HDD_CDD_Monthly']
        settings.Domestic_R            = config['TemporalDownscaling']['Domestic_R']
        settings.Elec_Building         = config['TemporalDownscaling']['Elec_Building']
        settings.Elec_Industry         = config['TemporalDownscaling']['Elec_Industry']
        settings.Elec_Building_heat    = config['TemporalDownscaling']['Elec_Building_heat']
        settings.Elec_Building_cool    = config['TemporalDownscaling']['Elec_Building_cool']
        settings.Elec_Building_others  = config['TemporalDownscaling']['Elec_Building_others']
        settings.Irr_MonthlyData       = config['TemporalDownscaling']['Irr_MonthlyData']
        settings.TemporalInterpolation = int(config['TemporalDownscaling']['TemporalInterpolation'])
    
    CheckExistence(settings)
    
    return settings


def PrintInfo(settings): 

    log = Logger.getlogger()
    oldlvl = log.setlevel(Logger.INFO)
    
    log.write('Project Name        : {}\n'.format(settings.ProjectName))
    log.write('Input Folder        : {}\n'.format(settings.InputFolder))
    log.write('Output Folder       : {}\n'.format(settings.OutputFolder))
    if settings.UseGCAMDatabase:
        log.write('GCAM Database Folder: {}\n'.format(settings.GCAM_DBpath + settings.GCAM_DBfile))
    else:
        log.write('GCAM CSV Folder     : {}\n'.format(settings.GCAM_CSV))
    log.write('Region Info Folder  : {}\n'.format(settings.rgnmapdir))


def CheckExistence(settings): 
    """
    Check existence of input files and directories, and create output directory if necessary.
    """
    if not (os.path.exists(settings.InputFolder) and os.path.isdir(settings.InputFolder)):
        raise DirectoryNotFoundError(settings.InputFolder)

    if not os.path.exists(settings.OutputFolder):
        os.makedirs(settings.OutputFolder) # this will raise an exception if it fails to create the directory
    
    if not (os.path.exists(settings.rgnmapdir) and os.path.isdir(settings.rgnmapdir)):
        raise DirectoryNotFoundError(settings.rgnmapdir)

    # if settings.UseGCAMDatabase and not (os.path.exists(settings.GCAM_CSV) and os.path.isdir(settings.GCAM_CSV)):
    #     raise DirectoryNotFoundError(settings.GCAM_CSV)
        
    # Check the existence of input files
    strlist = ['Area', 'Coord', 'aez', 'InputBasinFile', 'BasinNames', 'InputRegionFile', 'RegionNames', 'InputCountryFile', \
               'CountryNames', 'Population_GPW', 'Population_HYDE', 'Irrigation_GMIA', 'Irrigation_HYDE', \
               'Livestock_Buffalo', 'Livestock_Cattle', 'Livestock_Goat', 'Livestock_Sheep', 'Livestock_Poultry', 'Livestock_Pig']
    
    ifn = 0
    for s in strlist:
        fn = getattr(settings, s)
        if not os.path.isfile(fn):
            raise FileNotFoundError(getattr(settings, s))
               
    if settings.PerformTemporal:
        strlist = ['TempMonthlyFile', 'HDDCDDMonthlyFile', 'Domestic_R', 'Irr_MonthlyData', 'Elec_Building', 'Elec_Industry', \
                   'Elec_Building_heat', 'Elec_Building_cool', 'Elec_Building_others']
        for s in strlist:
            fn = getattr(settings, s)
            if not os.path.isfile(fn):
                raise FileNotFoundError(fn)


def help():
    
    print 
    '''
    License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
    Copyright (c) 2017, Battelle Memorial Institute

    Module: DataReader.IniReader
    
    Read in configuration file (*.ini)
    '''   
