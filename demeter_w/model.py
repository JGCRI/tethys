"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

This is the an example program of showing how to evaluate the input settings and
call the function running water disaggregation
"""

import time
import sys
import os

import demeter_w.DataReader.IniReader as IniReader
from demeter_w.Utils.Logging import Logger
from demeter_w.DataWriter.OUTWriter import OutWriter
from demeter_w.run_disaggregation import run_disaggregation as disagg


class DemeterW:

    def __init__(self, config='config.ini'):

        # instantiate functions
        self.Disaggregation = disagg
        self.OutWriter = OutWriter

        # compile config file
        self.settings = IniReader.getSimulatorSettings(config)

        # check input and output directories
        self.make_dirs()

        # instantiate logger and log file
        sys.stdout = Logger()
        sys.stdout.log = open(self.settings.OutputFolder + "logfile.log", "w")

        # write settings to log
        IniReader.PrintInfo(self.settings)

        # instantiate output variables for model run
        self.gridded_data = None
        self.gis_data = None

        # run model and save outputs
        self.run_model()

        # clean up log
        sys.stdout.log.close()

    def make_dirs(self):
        """
        Check for input and create output directories if not exists.
        """
        # Check if outputFolder exist or not
        if not os.path.exists(self.settings.InputFolder):

            print self.settings.InputFolder
            print("Error: Please specify Input Folder!")
            sys.exit(1)

        if not os.path.exists(self.settings.OutputFolder):
            os.makedirs(self.settings.OutputFolder)

    def run_model(self):
        """
        Execute the model and save the outputs.
        """
        print('Start disaggregation... ')
        s1 = time.time()
        self.gridded_data, self.gis_data = self.Disaggregation(self.settings)
        e1= time.time()
        print('End disaggregation... ')
        print("---Disaggregation: %s seconds ---" % (e1 - s1))

        print('Saving outputs... ')
        self.OutWriter(self.settings, self.gridded_data, self.gis_data)
        e2 = time.time()
        print("---Output: %s seconds ---" % (e2 - e1))

        print('End Project:   ', self.settings.ProjectName)