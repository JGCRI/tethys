"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


This is the class to define logging process: 

print command will write only to a logging file
"""
import os, sys

def clearfolder(pathname):
    """
    if the folder not exists, create the folder
    if the folder exists, clean the files inside
    """

    if not os.path.exists(pathname):
        os.makedirs(pathname)
    else:
        for the_file in os.listdir(pathname):
            file_path = os.path.join(pathname, the_file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
                

class Logger(object):

    def __init__(self):
        self.terminal = sys.stdout
        self.log = None

    def write(self, message):
        #self.terminal.write(message) # include this line: print command will write to console
        self.log.write(message)  

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass