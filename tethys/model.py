"""model.py which defines the Tethys class and calls the run_model() method to run remaining model.
"""

import time
from datetime import datetime
import tethys.Utils.Logging as Logging

from tethys.DataReader.IniReader import Settings
from tethys.DataWriter.OUTWriter import OutWriter
from tethys.run_disaggregation import run_disaggregation as disagg


class Tethys:
    """Tethys class which evaluates inputs from a configuration input 'config'
    and calls other methods to disaggregate water use.

    :param config: Configuration file with input settings. Default = 'config.ini'
    :type config: str
    """

    def __init__(self, config='config.ini'):
        """Default Constructor Method
        """

        # instantiate functions
        self.Disaggregation = disagg
        self.OutWriter = OutWriter

        # compile config file
        self.settings = Settings(config)

        # instantiate logger and log file
        Logging._setmainlog(Logging.Logger(self.settings.Logger))
        mainlog = Logging.Logger.getlogger()
        mainlog.write('Log start\n', Logging.Logger.INFO)
        mainlog.write(str(datetime.now()) + '\n', Logging.Logger.INFO)

        # write settings to log
        self.settings.print_info()

        # instantiate output variables for model run
        self.gridded_data = None
        self.gis_data = None

        # run model and save outputs
        self.run_model()

        # clean up log
        Logging._shutdown()

    def run_model(self):
        """
        Execute the model and save the outputs.
        """
        Logger = Logging.Logger
        mainlog = Logger.getlogger()
        mainlog.write('Start Disaggregation... \n', Logger.INFO)
        s1 = time.time()
        self.gridded_data, self.gis_data = self.Disaggregation(self.settings)
        e1= time.time()
        mainlog.write('End Disaggregation... \n', Logger.INFO)
        mainlog.write("---Disaggregation: %s seconds ---\n" % (e1 - s1), Logger.INFO)

        mainlog.write('Saving outputs...\n', Logger.INFO)
        self.OutWriter(self.settings, self.gridded_data, self.gis_data)
        e2 = time.time()
        mainlog.write("---Output: %s seconds ---\n" % (e2 - e1), Logger.INFO)

        mainlog.write('End Project: %s\n'%self.settings.ProjectName, Logger.INFO)
