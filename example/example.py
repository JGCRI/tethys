"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov); Chris R. Vernon (chris.vernon@pnnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

This is an example program showing how to run the model.

"""

import os
from demeter_w.model import DemeterW


if __name__ == "__main__":

    # get path to config.ini in the example dir
    cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

    # run the demeter-w model and save outputs
    dmw = DemeterW(config=cfg)

    # if needed, reuse the gridded data or gis data output by the model
    grid_outputs = dmw.gridded_data
    gis_outputs = dmw.gis_data