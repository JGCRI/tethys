'''
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-WD V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

Get the simulator settings from configuration(*.ini) file
'''

from configobj import ConfigObj
from ConfigSettings import ConfigSettings

def getSimulatorSettings(iniFile):
    
    config = ConfigObj(iniFile)
    settings = ConfigSettings()
    
    settings.ProjectName        = config['Project']['ProjectName']
    settings.InputFolder        = AddSlashToDir(config['Project']['InputFolder'])
    settings.OutputFolder       = AddSlashToDir(config['Project']['OutputFolder'])
    settings.rgnmapdir          = AddSlashToDir(config['Project']['rgnmapdir'])
    settings.OutputFormat       = int(config['Project']['OutputFormat'])
    settings.OutputUnit         = int(config['Project']['OutputUnit'])
    settings.PerformDiagnostics = int(config['Project']['PerformDiagnostics'])
    settings.PerformTemporal    = int(config['Project']['PerformTemporal'])
    
    settings.UseGCAMDatabase    = int(config['GCAM']['UseGCAMDatabase'])
    if settings.UseGCAMDatabase:
        settings.GCAM_DBpath         = AddSlashToDir(config['GCAM']['GCAM_DBpath'])
        settings.GCAM_DBfile         = config['GCAM']['GCAM_DBfile']
        settings.GCAM_query          = config['GCAM']['GCAM_query']
        
    else:
        settings.read_irrS          = int(config['GCAM']['Read_irrS'])
        settings.years              = map(str, config['GCAM']['GCAM_Years'])
    settings.GCAM_CSV          = AddSlashToDir(config['GCAM']['GCAM_CSV'])
        
    
    settings.Area               = settings.InputFolder + config['GriddedMap']['Area']
    settings.Coord              = settings.InputFolder + config['GriddedMap']['Coord']
    settings.aez                = settings.InputFolder + config['GriddedMap']['AEZ']
    settings.InputBasinFile     = settings.InputFolder + config['GriddedMap']['BasinIDs']
    settings.BasinNames         = settings.InputFolder + config['GriddedMap']['BasinNames']
    settings.InputRegionFile    = settings.InputFolder + config['GriddedMap']['RegionIDs']
    settings.RegionNames        = settings.InputFolder + config['GriddedMap']['RegionNames']
    settings.InputCountryFile   = settings.InputFolder + config['GriddedMap']['CountryIDs']
    settings.CountryNames       = settings.InputFolder + config['GriddedMap']['CountryNames']
    settings.Population_GPW     = settings.InputFolder + config['GriddedMap']['Population_GPW']
    settings.Population_HYDE    = settings.InputFolder + config['GriddedMap']['Population_HYDE']
    settings.Irrigation_GMIA    = settings.InputFolder + config['GriddedMap']['Irrigation_GMIA']
    settings.Irrigation_HYDE    = settings.InputFolder + config['GriddedMap']['Irrigation_HYDE']
    settings.Livestock_Buffalo  = settings.InputFolder + config['GriddedMap']['Livestock_Buffalo']
    settings.Livestock_Cattle   = settings.InputFolder + config['GriddedMap']['Livestock_Cattle']
    settings.Livestock_Goat     = settings.InputFolder + config['GriddedMap']['Livestock_Goat']
    settings.Livestock_Sheep    = settings.InputFolder + config['GriddedMap']['Livestock_Sheep']
    settings.Livestock_Poultry  = settings.InputFolder + config['GriddedMap']['Livestock_Poultry']
    settings.Livestock_Pig      = settings.InputFolder + config['GriddedMap']['Livestock_Pig']
    
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
    
    return settings

def PrintInfo(settings):
    
    print 'Project Name        : ', settings.ProjectName 
    print 'Input Folder        : ', settings.InputFolder
    print 'Output Folder       : ', settings.OutputFolder
    if settings.UseGCAMDatabase:
        print 'GCAM Database Folder: ', settings.GCAM_DBpath + settings.GCAM_DBfile
    else:
        print 'GCAM CSV Folder     : ', settings.GCAM_CSV
    print 'Region Info Folder  : ', settings.rgnmapdir

def AddSlashToDir(string): 
    
    string = string.rstrip('/') + '/'
    
    return string

def help():
    
    print 
    '''
    License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
    Copyright (c) 2017, Battelle Memorial Institute

    Module: DataReader.IniReader
    
    Read in configuration file (*.ini)
     
    '''   