"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""
import os

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