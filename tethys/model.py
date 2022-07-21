"""model.py which defines the Tethys class and calls the run_model() method to run remaining model.
"""

import logging
import time
import os

from tethys.config_reader import ReadConfig
from tethys.run_disaggregation import run_disaggregation
from tethys.data_writer.outputs import write_outputs

class Tethys(ReadConfig):
    """Model wrapper for Tethys.

    :param config_file:                 Full path with file name and extension to a input config.ini file.  If not
                                        passed, the default configuration will be used.
    :type config_file:                  str

    """

    def __init__(self, config_file):

        # start time for model run
        self.start_time = time.time()

        # initialize console handler for logger
        self.console_handler()

        logging.info("Starting Tethys model")

        # inherit the configuration reader class attributes
        super(Tethys, self).__init__(config_file=config_file)

    def execute(self):
        """Execute the model and save the outputs."""

        t0 = time.time()
        logging.info('Start Disaggregation...')

        if self.PerformWithdrawal == 1:

            # Create OutputFolder if doesn't exist
            # Check whether the specified path exists or not
            if not os.path.exists(self.OutputFolder):
                # Create a new directory because it does not exist
                os.makedirs(self.OutputFolder)
                print(f"Output folder created: {self.OutputFolder}")

            TDYears, gridded_data, gis_data = run_disaggregation(years=self.years,
                                                        InputRegionFile=self.InputRegionFile,
                                                        mapsize=self.mapsize,
                                                        UseDemeter=self.UseDemeter,
                                                        PerformDiagnostics=self.PerformDiagnostics,
                                                        PerformTemporal=self.PerformTemporal,
                                                        RegionNames=self.RegionNames,
                                                        gcam_basin_lu=self.gcam_basin_lu,
                                                        buff_fract=self.buff_fract,
                                                        goat_fract=self.goat_fract,
                                                        GCAM_DBpath=self.GCAM_DBpath,
                                                        GCAM_DBfile=self.GCAM_DBfile,
                                                        query_file=self.query_file,
                                                        OutputFolder=self.OutputFolder,
                                                        temporal_climate=self.temporal_climate,
                                                        Irr_MonthlyData=self.Irr_MonthlyData,
                                                        TemporalInterpolation=self.TemporalInterpolation,
                                                        Domestic_R=self.Domestic_R,
                                                        Livestock_Buffalo=self.Livestock_Buffalo,
                                                        Livestock_Cattle=self.Livestock_Cattle,
                                                        Livestock_Goat=self.Livestock_Goat,
                                                        Livestock_Sheep=self.Livestock_Sheep,
                                                        Livestock_Poultry=self.Livestock_Poultry,
                                                        Livestock_Pig=self.Livestock_Pig,
                                                        Coord=self.Coord,
                                                        Area=self.Area,
                                                        InputBasinFile=self.InputBasinFile,
                                                        BasinNames=self.BasinNames,
                                                        Population_GPW=self.Population_GPW,
                                                        Population_HYDE=self.Population_HYDE,
                                                        Irrigation_GMIA=self.Irrigation_GMIA,
                                                        Irrigation_HYDE=self.Irrigation_HYDE,
                                                        DemeterOutputFolder=self.DemeterOutputFolder,
                                                        OutputUnit=self.OutputUnit,
                                                        basin_state_area=self.basin_state_area,
                                                        SpatialResolution=self.SpatialResolution,
                                                        demand='Withdrawals',
                                                        variant=' GCAMUSA' if self.GCAMUSA else ''
                                                        )

            print(gridded_data)

            logging.info(f"Disaggregation completed in : {(time.time() - t0)} seconds")

            t0 = time.time()
            logging.info('Writing outputs...')
            write_outputs(OutputUnit=self.OutputUnit,
                          OutputFormat=self.OutputFormat,
                          OutputFolder=self.OutputFolder,
                          PerformTemporal=self.PerformTemporal,
                          TDYears=TDYears,
                          years=self.years,
                          OUT=gridded_data,
                          GISData=gis_data)
            logging.info(f"Outputs writen in: {(time.time() - t0)}")

        if self.PerformConsumption == 1:

            # Create OutputFolder if doesn't exist
            # Check whether the specified path exists or not
            if not os.path.exists(self.OutputFolder + "_C"):
                # Create a new directory because it does not exist
                os.makedirs(self.OutputFolder + "_C")
                print(f"Consumption Output folder created: {self.OutputFolder + '_C'}")

            TDYears, gridded_data, gis_data = run_disaggregation(years=self.years,
                                                                 InputRegionFile=self.InputRegionFile,
                                                                 mapsize=self.mapsize,
                                                                 UseDemeter=self.UseDemeter,
                                                                 PerformDiagnostics=self.PerformDiagnostics,
                                                                 PerformTemporal=self.PerformTemporal,
                                                                 RegionNames=self.RegionNames,
                                                                 gcam_basin_lu=self.gcam_basin_lu,
                                                                 buff_fract=self.buff_fract,
                                                                 goat_fract=self.goat_fract,
                                                                 GCAM_DBpath=self.GCAM_DBpath,
                                                                 GCAM_DBfile=self.GCAM_DBfile,
                                                                 query_file=self.query_file,
                                                                 OutputFolder=self.OutputFolder + '_C',
                                                                 temporal_climate=self.temporal_climate,
                                                                 Irr_MonthlyData=self.Irr_MonthlyData,
                                                                 TemporalInterpolation=self.TemporalInterpolation,
                                                                 Domestic_R=self.Domestic_R,
                                                                 Livestock_Buffalo=self.Livestock_Buffalo,
                                                                 Livestock_Cattle=self.Livestock_Cattle,
                                                                 Livestock_Goat=self.Livestock_Goat,
                                                                 Livestock_Sheep=self.Livestock_Sheep,
                                                                 Livestock_Poultry=self.Livestock_Poultry,
                                                                 Livestock_Pig=self.Livestock_Pig,
                                                                 Coord=self.Coord,
                                                                 Area=self.Area,
                                                                 InputBasinFile=self.InputBasinFile,
                                                                 BasinNames=self.BasinNames,
                                                                 Population_GPW=self.Population_GPW,
                                                                 Population_HYDE=self.Population_HYDE,
                                                                 Irrigation_GMIA=self.Irrigation_GMIA,
                                                                 Irrigation_HYDE=self.Irrigation_HYDE,
                                                                 DemeterOutputFolder=self.DemeterOutputFolder,
                                                                 OutputUnit=self.OutputUnit,
                                                                 basin_state_area=self.basin_state_area,
                                                                 SpatialResolution=self.SpatialResolution,
                                                                 demand='Consumption',
                                                                 variant=' GCAMUSA' if self.GCAMUSA else ''
                                                                 )

            print(gridded_data)

            logging.info(f"Consumption Disaggregation completed in : {(time.time() - t0)} seconds")

            t0 = time.time()
            logging.info('Writing Consumption outputs...')
            write_outputs(OutputUnit=self.OutputUnit,
                          OutputFormat=self.OutputFormat,
                          OutputFolder=self.OutputFolder + "_C",
                          PerformTemporal=self.PerformTemporal,
                          TDYears=TDYears,
                          years=self.years,
                          OUT=gridded_data,
                          GISData=gis_data)

            for filename in os.listdir(self.OutputFolder + '_C'): #TODO make write_outputs write these right instead
                if 'wd' in filename:
                    oldname = os.path.join(self.OutputFolder + '_C', filename)
                    newname = os.path.join(self.OutputFolder + '_C', filename.replace('wd', 'cd', 1))
                    try:
                        os.rename(oldname, newname)
                    except:
                        os.remove(newname)
                        os.rename(oldname, newname)

            logging.info(f"Consumption Outputs writen in: {(time.time() - t0)}")

        logging.info(f'Tethys model run completed in {round(time.time() - self.start_time, 7)}')

        # clean up log
        self.close_logger()


def run_model(config_file=None, **kwargs):
    """Run the Tethys model based on a user-defined configuration.

    :param config_file:                 Full path with file name and extension to the input configuration file.
    :type config_file:                  str

    :returns:                           model instance housing configuration and output data

    """

    if config_file is not None:
        config = config_file

    print(f"kwargs:  {kwargs}")

    config = kwargs.get('config', config)

    model = Tethys(config)

    model.execute()

    return model
