"""model.py which defines the Tethys class and calls the run_model() method to run remaining model.
"""

import logging
import time

from tethys.config_reader import ReadConfig
from tethys.data_writer.outputs import write_outputs
from tethys.run_disaggregation import run_disaggregation


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

        gridded_data, gis_data = run_disaggregation(settings=self,
                                                    years=self.years,
                                                    InputRegionFile=self.InputRegionFile,
                                                    mapsize=self.mapsize,
                                                    subreg=self.subreg,
                                                    UseDemeter=self.UseDemeter,
                                                    PerformDiagnostics=self.PerformDiagnostics,
                                                    PerformTemporal=self.PerformTemporal)

        print(gridded_data)

        logging.info(f"Disaggregation completed in : {(time.time() - t0)} seconds")

        # t0 = time.time()
        # logging.info('Writing outputs...')
        # write_outputs(self, self.gridded_data, self.gis_data)
        # logging.info(f"Outputs writen in: {(time.time() - t0)}")

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


