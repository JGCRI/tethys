"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

This is the an example program of showing how to evaluate the input settings and call the function running water disaggregation

"""

import time, sys, os
import DataReader.IniReader as IniReader
from Utils.Logging import Logger
from DataWriter.OUTWriter import OutWriter
from run_disaggregation import run_disaggregation as Disaggregation

"""
1. Configure "Settings" Class as the input for function "run_disaggregation"
"""
# Read simulator settings.
settingFile = 'config.ini'
settings = IniReader.getSimulatorSettings(settingFile)    
# Check if outputFolder exist or not
if not os.path.exists(settings.InputFolder):
    print "Error: Please specify Input Folder!"
    sys.exit(1)
if not os.path.exists(settings.OutputFolder):
    os.makedirs(settings.OutputFolder)
 
# Setup the log file, save it into the output folder    
sys.stdout     = Logger()
sys.stdout.log = open(settings.OutputFolder + "logfile.log", "w")

IniReader.PrintInfo(settings)

"""
2. Execute the function "run_disaggregation"
"""
print 'Start run_disaggregation... '
starttime1 = time.time() # Start time for disaggregation

OUT, GISData = Disaggregation(settings)

endtime1 = time.time() # End time for disaggregation
print 'End run_disaggregation... '
print("---Disaggregation: %s seconds ---" % (endtime1- starttime1))


"""
3. Output
"""

OutWriter(settings, OUT, GISData)

endtime2 = time.time()
print("---Output: %s seconds ---" % (endtime2 - endtime1))
    
print 'End Project:   ', settings.ProjectName

sys.stdout.log.close()