import os
import logging
import pkg_resources
import re

from configobj import ConfigObj

from tethys.logger import Logger


class ReadConfig(Logger):
    """Read the configuration file to a dictionary.

        :param config_file:                 Full path with file name and extension to the input config.ini file
        :type config_file:                  str

    """

    # type hints
    config_file: str

    DEFAULT_CONFIG_FILE = pkg_resources.resource_filename('tethys', 'data/config.ini')

    def __init__(self, **kwargs):

        self.params = kwargs

        # inherit logger class attributes
        super(ReadConfig, self).__init__()

        # if no configuration file has been provided, use the default template
        self.config_file = self.params.get('config_file', self.DEFAULT_CONFIG_FILE)

        # read into config object
        self.config = ConfigObj(self.config_file)

        # project level
        self.project_config = self.config.get('Project')

        # GCAM access settings
        self.gcam_config = self.config.get('GCAM')

        # reference data
        self.map_params = self.config.get('GriddedMap')

        # update any default dictionary values with items specified as arguments by the user
        self.project_config.update(self.params)

        self.ProjectName = self.validate_string(self.project_config.get('ProjectName'))

        self.InputFolder = self.validate_directory(self.project_config.get('InputFolder'), 'InputFolder')
        self.OutputFolder = os.path.join(self.project_config.get('OutputFolder'), self.ProjectName)
        self.rgnmapdir = self.project_config.get('rgnmapdir')
        self.OutputFormat = int(self.project_config.get('OutputFormat', 0))
        self.OutputUnit = int(self.project_config.get('OutputUnit', 0))
        self.PerformDiagnostics = int(self.project_config.get('PerformDiagnostics', 0))
        self.PerformTemporal = int(self.project_config.get('PerformTemporal', 0))
        self.UseDemeter = int(self.project_config.get('UseDemeter', 0))
        self.DemeterOutputFolder = self.project_config.get('DemeterOutputFolder', 'None')
        self.SpatialResolution = float(self.project_config.get('SpatialResolution', 0.5))

        # assumes geographic coordinates
        self.mapsize = [int(180 / self.SpatialResolution), int(360 / self.SpatialResolution)]

        self.GCAM_DBpath = os.path.join(self.InputFolder, self.gcam_config.get('GCAM_DBpath', None))
        self.GCAM_DBfile = self.gcam_config.get('GCAM_DBfile', None)
        self.GCAM_query = os.path.join(self.GCAM_DBpath, self.gcam_config.get('GCAM_query', None))
        self.subreg = int(self.gcam_config.get('GCAM_subreg', None))

        # a single year input will be string not list for self.years
        self.years = self.gcam_config.get('GCAM_Years', None)

        if not isinstance(self.years, list):
            self.years = [self.years]

        # update any default dictionary values with items specified as arguments by the user
        self.map_params.update(self.params)

        self.Area = os.path.join(self.InputFolder, self.map_params.get('Area'))
        self.Coord = os.path.join(self.InputFolder, self.map_params.get('Coord'))
        self.InputBasinFile = os.path.join(self.InputFolder, self.map_params.get('BasinIDs'))
        self.BasinNames = os.path.join(self.InputFolder, self.map_params.get('BasinNames'))
        self.gcam_basin_lu = os.path.join(self.InputFolder, self.map_params.get('GCAM_Basin_Key'))
        self.InputRegionFile = os.path.join(self.InputFolder, self.map_params.get('RegionIDs'))
        self.RegionNames = os.path.join(self.InputFolder, self.map_params.get('RegionNames'))
        self.InputCountryFile = os.path.join(self.InputFolder, self.map_params.get('CountryIDs'))
        self.CountryNames = os.path.join(self.InputFolder, self.map_params.get('CountryNames'))
        self.Population_GPW = os.path.join(self.InputFolder, self.map_params.get('Population_GPW'))
        self.Population_HYDE = os.path.join(self.InputFolder, self.map_params.get('Population_HYDE'))

        self.Irrigation_GMIA = os.path.join(self.InputFolder, self.map_params.get('Irrigation_GMIA', 'None'))
        self.Irrigation_HYDE = os.path.join(self.InputFolder, self.map_params.get('Irrigation_HYDE', 'None'))

        self.Livestock_Buffalo = os.path.join(self.InputFolder, self.map_params.get('Livestock_Buffalo'))
        self.Livestock_Cattle = os.path.join(self.InputFolder, self.map_params.get('Livestock_Cattle'))
        self.Livestock_Goat = os.path.join(self.InputFolder, self.map_params.get('Livestock_Goat'))
        self.Livestock_Sheep = os.path.join(self.InputFolder, self.map_params.get('Livestock_Sheep'))
        self.Livestock_Poultry = os.path.join(self.InputFolder, self.map_params.get('Livestock_Poultry'))
        self.Livestock_Pig = os.path.join(self.InputFolder, self.map_params.get('Livestock_Pig'))
        self.buff_fract = os.path.join(self.InputFolder, self.map_params.get('Buffalo_Fraction'))
        self.goat_fract = os.path.join(self.InputFolder, self.map_params.get('Goat_Fraction'))
        self.irrigated_fract = os.path.join(self.InputFolder, self.map_params.get('Irrigated_Fract'))

        if self.PerformTemporal:
            self.temporal_params = self.config.get('TemporalDownscaling')

            # update any default dictionary values with items specified as arguments by the user
            self.temporal_params.update(self.params)

            self.temporal_climate = self.temporal_params.get('temporal_climate')
            self.Domestic_R = self.temporal_params.get('Domestic_R')
            self.Elec_Building = self.temporal_params.get('Elec_Building')
            self.Elec_Industry = self.temporal_params.get('Elec_Industry')
            self.Elec_Building_heat = self.temporal_params.get('Elec_Building_heat')
            self.Elec_Building_cool = self.temporal_params.get('Elec_Building_cool')
            self.Elec_Building_others = self.temporal_params.get('Elec_Building_others')
            self.Irr_MonthlyData = self.temporal_params.get('Irr_MonthlyData')
            self.TemporalInterpolation = int(self.temporal_params.get('TemporalInterpolation'))

        if self.UseDemeter:
            D_years = []
            for filename in os.listdir(self.DemeterOutputFolder):  # Folder contains Demeter outputs
                if filename.endswith('.csv'):
                    yearstr = re.sub("[^0-9]", "", filename)
                    D_years.append(int(yearstr))

            years = [int(x) for x in self.years]

            # Subset D_years to match chosen years
            D_years = [number for number in D_years if number in years]
            D_years = sorted(D_years)

            # If we use Demeter outputs, we will start from the beginning year in Demeter.
            startindex = years.index(D_years[0])
            self.years = years[startindex:]

    @staticmethod
    def validate_string(string):
        """Ensure that a string is all lower case and spaces are underscore separated.

        :param string:                      any string value
        :type string:                       str

        :return:                            lower case underscore separated string

        """

        return '_'.join(string.strip().lower().split(' '))

    @staticmethod
    def validate_directory(directory, param_name):
        """Ensure directory exists."""

        if os.path.isdir(directory):
            return directory

        else:
            msg = f"Directory {directory} not found for {param_name}"
            raise NotADirectoryError(msg)