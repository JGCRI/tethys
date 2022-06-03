import os
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
        self.PerformWithdrawal = int(self.project_config.get('PerformWithdrawal', 1))
        self.PerformConsumption = int(self.project_config.get('PerformConsumption', 0))
        self.PerformDiagnostics = int(self.project_config.get('PerformDiagnostics', 0))
        self.PerformTemporal = int(self.project_config.get('PerformTemporal', 0))
        self.UseDemeter = int(self.project_config.get('UseDemeter', 0))
        self.DemeterOutputFolder = self.project_config.get('DemeterOutputFolder', 'None')
        self.SpatialResolution = float(self.project_config.get('SpatialResolution', 0.5))

        # assumes geographic coordinates
        self.mapsize = [int(180 / self.SpatialResolution), int(360 / self.SpatialResolution)]

        self.GCAM_DBpath = os.path.join(self.InputFolder, self.gcam_config.get('GCAM_DBpath', None))
        self.GCAM_DBfile = self.gcam_config.get('GCAM_DBfile', None)

        self.GCAMUSA = int(self.project_config.get('GCAMUSA', 0))

        # for backwards compatability, and allow for non-default query files
        # this logic can be simplified considerably by ditching backwards compatibility
        self.GCAM_query = os.path.join(self.GCAM_DBpath, self.gcam_config.get('GCAM_query', 'None'))
        if self.PerformWithdrawal == 1 and not self.GCAM_query.endswith('.xml'):
            if self.GCAMUSA == 1:
                self.GCAM_query = \
                    pkg_resources.resource_filename('tethys', 'reference/queries/query_withdrawal_GCAMUSA.xml')
            else:
                self.GCAM_query = pkg_resources.resource_filename('tethys', 'reference/queries/query_withdrawal.xml')

        self.GCAM_query_C = os.path.join(self.GCAM_DBpath, self.gcam_config.get('GCAM_query_C', 'None'))
        if self.PerformConsumption == 1 and not self.GCAM_query_C.endswith('.xml'):
            if self.GCAMUSA == 1:
                self.GCAM_query_C = \
                    pkg_resources.resource_filename('tethys', 'reference/queries/query_consumption_GCAMUSA.xml')
            else:
                self.GCAM_query_C = pkg_resources.resource_filename('tethys', 'reference/queries/query_consumption.xml')

        self.GCAM_queryCore = os.path.join(self.GCAM_DBpath, self.gcam_config.get('GCAM_queryCore', 'None'))
        if not self.GCAM_queryCore.endswith('.xml'):
            self.GCAM_queryCore = pkg_resources.resource_filename('tethys', 'reference/queries/query_withdrawal.xml')

        self.GCAM_queryCore_C = os.path.join(self.GCAM_DBpath, self.gcam_config.get('GCAM_queryCore_C', 'None'))
        if not self.GCAM_queryCore_C.endswith('.xml'):
            self.GCAM_queryCore_C = pkg_resources.resource_filename('tethys', 'reference/queries/query_consumption.xml')

        # a single year input will be string not list for self.years
        self.years = self.gcam_config.get('GCAM_Years', None)

        if not isinstance(self.years, list):
            self.years = [self.years]
        self.years = [int(i) for i in self.years]

        # update any default dictionary values with items specified as arguments by the user
        self.map_params.update(self.params)

        self.Area = os.path.join(self.InputFolder, self.map_params.get('Area', 'None'))
        if os.path.basename(self.Area) == 'None':
            self.Area = pkg_resources.resource_filename('tethys', 'reference/grid_info/Grid_Areas_ID.csv')

        self.Coord = os.path.join(self.InputFolder, self.map_params.get('Coord', 'None'))
        if os.path.basename(self.Coord) == 'None':
            self.Coord = pkg_resources.resource_filename('tethys', 'reference/grid_info/coordinates.csv')

        self.InputBasinFile = os.path.join(self.InputFolder, self.map_params.get('BasinIDs', 'None'))
        if os.path.basename(self.InputBasinFile) == 'None':
            self.InputBasinFile = pkg_resources.resource_filename('tethys', 'reference/grid_info/basin.csv')

        self.BasinNames = os.path.join(self.InputFolder, self.map_params.get('BasinNames', 'None'))
        if os.path.basename(self.BasinNames) == 'None':
            self.BasinNames = pkg_resources.resource_filename('tethys', 'reference/grid_info/BasinNames.csv')

        self.gcam_basin_lu = os.path.join(self.InputFolder, self.map_params.get('GCAM_Basin_Key', 'None'))
        if os.path.basename(self.gcam_basin_lu) == 'None':
            self.gcam_basin_lu = pkg_resources.resource_filename('tethys', 'reference/grid_info/gcam_basin_lookup.csv')

        self.InputRegionFile = os.path.join(self.InputFolder, self.map_params.get('RegionIDs', 'None'))
        if os.path.basename(self.InputRegionFile) == 'None':
            if self.GCAMUSA == 1:
                self.InputRegionFile = \
                    pkg_resources.resource_filename('tethys', 'reference/grid_info/region32_grids_gcamUSA.csv')
            else:
                self.InputRegionFile = \
                    pkg_resources.resource_filename('tethys', 'reference/grid_info/region32_grids.csv')

        self.RegionNames = os.path.join(self.InputFolder, self.map_params.get('RegionNames', 'None'))
        if os.path.basename(self.RegionNames) == 'None':
            if self.GCAMUSA == 1:
                self.RegionNames = pkg_resources.resource_filename('tethys', 'reference/grid_info/RgnNames_gcamUSA.csv')
            else:
                self.RegionNames = pkg_resources.resource_filename('tethys', 'reference/grid_info/RgnNames.csv')

        self.InputCountryFile = os.path.join(self.InputFolder, self.map_params.get('CountryIDs', 'None'))
        if os.path.basename(self.InputCountryFile) == 'None':
            self.InputCountryFile = pkg_resources.resource_filename('tethys', 'reference/grid_info/country.csv')

        self.CountryNames = os.path.join(self.InputFolder, self.map_params.get('CountryNames', 'None'))
        if os.path.basename(self.CountryNames) == 'None':
            self.CountryNames = pkg_resources.resource_filename('tethys', 'reference/grid_info/country-names.csv')

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

        self.buff_fract = os.path.join(self.InputFolder, self.map_params.get('Buffalo_Fraction', 'None'))
        if os.path.basename(self.buff_fract) == 'None':
            if self.GCAMUSA == 1:
                self.buff_fract = \
                    pkg_resources.resource_filename('tethys', 'reference/grid_info/bfracFAO2005_gcamUSA.csv')
            else:
                self.buff_fract = pkg_resources.resource_filename('tethys', 'reference/grid_info/bfracFAO2005.csv')

        self.goat_fract = os.path.join(self.InputFolder, self.map_params.get('Goat_Fraction', 'None'))
        if os.path.basename(self.goat_fract) == 'None':
            if self.GCAMUSA == 1:
                self.goat_fract = \
                    pkg_resources.resource_filename('tethys', 'reference/grid_info/gfracFAO2005_gcamUSA.csv')
            else:
                self.goat_fract = pkg_resources.resource_filename('tethys', 'reference/grid_info/gfracFAO2005.csv')

        # Additional details for GCAM USA (Only if present)
        self.basin_state_area = os.path.join(self.InputFolder, self.map_params.get('BasinStateArea', 'None'))
        if os.path.basename(self.basin_state_area) == 'None' and self.GCAMUSA == 1:
            self.basin_state_area = \
                pkg_resources.resource_filename('tethys', 'reference/grid_info/basin_state_area_ratio_gcamUSA.csv')

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
        else:  # quick fix to allow running spatial only
            self.temporal_climate = None
            self.Domestic_R = None
            self.Elec_Building = None
            self.Elec_Industry = None
            self.Elec_Building_heat = None
            self.Elec_Building_cool = None
            self.Elec_Building_others = None
            self.Irr_MonthlyData = None
            self.TemporalInterpolation = None

        if self.UseDemeter:
            demeter_years = []
            for filename in os.listdir(self.DemeterOutputFolder):  # Folder contains Demeter outputs
                if filename.endswith('.csv'):
                    yearstr = re.sub("[^0-9]", "", filename)
                    demeter_years.append(int(yearstr))

            # If we use Demeter outputs, we will start from the beginning year in Demeter.
            self.years = [i for i in self.years if i >= min(demeter_years)]

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
