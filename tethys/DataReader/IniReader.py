"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

Get the simulator settings from configuration(.ini) file

"""

import os
from configobj import ConfigObj
from tethys.Utils.exceptions import FileNotFoundError, DirectoryNotFoundError
from tethys.Utils.Logging import Logger


class Settings:

    def __init__(self, ini):

        config = ConfigObj(ini)

        # project level params
        self.ProjectName        = config['Project']['ProjectName']
        self.InputFolder        = config['Project']['InputFolder']
        self.OutputFolder       = os.path.join(config['Project']['OutputFolder'], self.ProjectName)
        self.rgnmapdir          = config['Project']['rgnmapdir']
        try: 
            self.OutputFormat       = int(config['Project']['OutputFormat'])
        except KeyError:
            self.OutputFormat       = 0
        try:    
            self.OutputUnit         = int(config['Project']['OutputUnit'])
        except KeyError:
            self.OutputUnit         = 0
        try:
            self.PerformDiagnostics = int(config['Project']['PerformDiagnostics'])
        except KeyError:
            self.PerformDiagnostics = 1
        try:     
            self.PerformTemporal    = int(config['Project']['PerformTemporal'])
        except KeyError:
            self.PerformTemporal    = 0
        try:
            self.UseDemeter         = int(config['Project']['UseDemeter'])
        except KeyError:
            self.UseDemeter         = 0
        
        try:
            self.Logger           = config['Logger']
            self.Logger['logdir'] = self.OutputFolder 
        except KeyError:
            # No logger configuration.  Supply a default one for backward compatibility with old config files.
            self.Logger = {'logdir': 'logs', 'filename': 'mainlog.txt'}

        # spatial params
        try:
            self.SpatialResolution = float(config['Project']['SpatialResolution'])
        except KeyError:
            self.SpatialResolution = 0.5
            self.mapsize = [int(180 / self.SpatialResolution), int(360 / self.SpatialResolution)]

        # GCAM access settings
        self.GCAM_DBpath = os.path.join(self.InputFolder, config['GCAM']['GCAM_DBpath'])
        self.GCAM_DBfile = config['GCAM']['GCAM_DBfile']
        self.GCAM_query = os.path.join(self.GCAM_DBpath, config['GCAM']['GCAM_query'])
        self.subreg = int(config['GCAM']['GCAM_subreg'])
        self.years = config['GCAM']['GCAM_Years']
        if not isinstance(self.years, (list,)): # a single year input will be string not list for self.years
            self.years = [self.years]
			
        # reference data
        self.Area               = os.path.join(self.InputFolder, config['GriddedMap']['Area'])
        self.Coord              = os.path.join(self.InputFolder, config['GriddedMap']['Coord'])
        self.aez                = os.path.join(self.InputFolder, config['GriddedMap']['AEZ'])
        self.InputBasinFile     = os.path.join(self.InputFolder, config['GriddedMap']['BasinIDs'])
        self.BasinNames         = os.path.join(self.InputFolder, config['GriddedMap']['BasinNames'])
        self.gcam_basin_lu      = os.path.join(self.InputFolder, config['GriddedMap']['GCAM_Basin_Key'])
        self.InputRegionFile    = os.path.join(self.InputFolder, config['GriddedMap']['RegionIDs'])
        self.RegionNames        = os.path.join(self.InputFolder, config['GriddedMap']['RegionNames'])
        self.InputCountryFile   = os.path.join(self.InputFolder, config['GriddedMap']['CountryIDs'])
        self.CountryNames       = os.path.join(self.InputFolder, config['GriddedMap']['CountryNames'])
        self.Population_GPW     = os.path.join(self.InputFolder, config['GriddedMap']['Population_GPW'])
        self.Population_HYDE    = os.path.join(self.InputFolder, config['GriddedMap']['Population_HYDE'])
        if not self.UseDemeter:
            self.Irrigation_GMIA    = os.path.join(self.InputFolder, config['GriddedMap']['Irrigation_GMIA'])
            self.Irrigation_HYDE    = os.path.join(self.InputFolder, config['GriddedMap']['Irrigation_HYDE'])
        self.Livestock_Buffalo  = os.path.join(self.InputFolder, config['GriddedMap']['Livestock_Buffalo'])
        self.Livestock_Cattle   = os.path.join(self.InputFolder, config['GriddedMap']['Livestock_Cattle'])
        self.Livestock_Goat     = os.path.join(self.InputFolder, config['GriddedMap']['Livestock_Goat'])
        self.Livestock_Sheep    = os.path.join(self.InputFolder, config['GriddedMap']['Livestock_Sheep'])
        self.Livestock_Poultry  = os.path.join(self.InputFolder, config['GriddedMap']['Livestock_Poultry'])
        self.Livestock_Pig      = os.path.join(self.InputFolder, config['GriddedMap']['Livestock_Pig'])
        self.buff_fract         = os.path.join(self.InputFolder, config['GriddedMap']['Buffalo_Fraction'])
        self.goat_fract         = os.path.join(self.InputFolder, config['GriddedMap']['Goat_Fraction'])
        self.irrigated_fract    = os.path.join(self.InputFolder, config['GriddedMap']['Irrigated_Fract'])

        if self.PerformTemporal:
            self.temporal_climate      = config['TemporalDownscaling']['temporal_climate']
            self.Domestic_R            = config['TemporalDownscaling']['Domestic_R']
            self.Elec_Building         = config['TemporalDownscaling']['Elec_Building']
            self.Elec_Industry         = config['TemporalDownscaling']['Elec_Industry']
            self.Elec_Building_heat    = config['TemporalDownscaling']['Elec_Building_heat']
            self.Elec_Building_cool    = config['TemporalDownscaling']['Elec_Building_cool']
            self.Elec_Building_others  = config['TemporalDownscaling']['Elec_Building_others']
            self.Irr_MonthlyData       = config['TemporalDownscaling']['Irr_MonthlyData']
            self.TemporalInterpolation = int(config['TemporalDownscaling']['TemporalInterpolation'])
        
        if self.UseDemeter:
            self.DemeterOutputFolder = config['Project']['DemeterOutputFolder']
            D_years = []
            for filename in os.listdir(self.DemeterOutputFolder): # Folder contains Demeter outputs
                if filename.endswith('.csv'):
                    yearstr = filename.split('.')[0].split('_')[-1]
                    D_years.append(int(yearstr))
                           
            years      = [int(x) for x in self.years]
            startindex = years.index(D_years[0]) # If we use Demeter outputs, we will start from the beginning year in Demeter.
            self.years = years[startindex:]

        self.check_existence()

    def check_existence(self):
        """
        Check existence of input files and directories, and create output directory if necessary.
        """
        if not (os.path.exists(self.InputFolder) and os.path.isdir(self.InputFolder)):
            raise DirectoryNotFoundError(self.InputFolder)

        if not os.path.exists(self.OutputFolder):
            os.makedirs(self.OutputFolder)  # this will raise an exception if it fails to create the directory

        if not (os.path.exists(self.rgnmapdir) and os.path.isdir(self.rgnmapdir)):
            raise DirectoryNotFoundError(self.rgnmapdir)

        # if settings.UseGCAMDatabase and not (os.path.exists(settings.GCAM_CSV) and os.path.isdir(settings.GCAM_CSV)):
        #     raise DirectoryNotFoundError(settings.GCAM_CSV)

        # Check the existence of input files
        if not self.UseDemeter:
            strlist = ['Area', 'Coord', 'aez', 'InputBasinFile', 'BasinNames', 'InputRegionFile', 'RegionNames',
                       'InputCountryFile', 'CountryNames', 'Population_GPW', 'Population_HYDE', 'Irrigation_GMIA',
                       'Irrigation_HYDE', 'Livestock_Buffalo', 'Livestock_Cattle', 'Livestock_Goat', 'Livestock_Sheep',
                       'Livestock_Poultry', 'Livestock_Pig']
        else:
            strlist = ['Area', 'Coord', 'aez', 'InputBasinFile', 'BasinNames', 'InputRegionFile', 'RegionNames',
                       'InputCountryFile', 'CountryNames', 'Population_GPW', 'Population_HYDE',
                       'Livestock_Buffalo', 'Livestock_Cattle', 'Livestock_Goat', 'Livestock_Sheep',
                       'Livestock_Poultry', 'Livestock_Pig']

        ifn = 0
        for s in strlist:
            fn = getattr(self, s)
            if not os.path.isfile(fn):
                raise FileNotFoundError(getattr(self, s))

        if self.PerformTemporal:
            strlist = ['temporal_climate', 'Domestic_R', 'Irr_MonthlyData', 'Elec_Building', 'Elec_Industry',
                       'Elec_Building_heat', 'Elec_Building_cool', 'Elec_Building_others']

            for s in strlist:
                fn = getattr(self, s)
                if not os.path.isfile(fn):
                    raise FileNotFoundError(fn)
                
        if self.UseDemeter and not os.path.exists(self.DemeterOutputFolder):
            raise DirectoryNotFoundError(self.DemeterOutputFolder)
						
    def print_info(self):

        log    = Logger.getlogger()
        oldlvl = log.setlevel(Logger.INFO)

        log.write('Project Name        : {}\n'.format(self.ProjectName))
        log.write('Input Folder        : {}\n'.format(self.InputFolder))
        log.write('Output Folder       : {}\n'.format(self.OutputFolder))
        log.write('GCAM Database Folder: {}\n'.format(os.path.join(self.GCAM_DBpath, self.GCAM_DBfile)))
        log.write('Region Info Folder  : {}\n'.format(self.rgnmapdir))
