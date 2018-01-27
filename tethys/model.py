"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov); Chris R. Vernon (chris.vernon@pnnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

This is the Tethys class of showing how to evaluate the input settings and
call the function running water disaggregation
"""

import os
import sys
import time
import tethys.DataReader.IniReader as IniReader
from tethys.Utils.Logging import Logger
from tethys.DataWriter.OUTWriter import OutWriter
from tethys.run_disaggregation import run_disaggregation as disagg


class Tethys:

    def __init__(self, config='config.ini'):
        
        print "Tethys starts..."
        
        # instantiate functions
        self.Disaggregation = disagg
        self.OutWriter = OutWriter

        # compile config file
        self.settings = IniReader.getSimulatorSettings(config)

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
        
        sys.stdout = sys.__stdout__
        print "Tethys ends."

    def run_model(self):
        """
        Execute the model and save the outputs.
        """
        print('Start Disaggregation... ')
        s1 = time.time()
        self.gridded_data, self.gis_data = self.Disaggregation(self.settings)
        e1= time.time()
        print('End Disaggregation... ')
        print("---Disaggregation: %s seconds ---" % (e1 - s1))

        print('Saving outputs... ')
        self.OutWriter(self.settings, self.gridded_data, self.gis_data)
        e2 = time.time()
        print("---Output: %s seconds ---" % (e2 - e1))

        print('End Project:   ', self.settings.ProjectName)