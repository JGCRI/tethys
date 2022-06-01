"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""
import pandas as pd


def get_array_csv(filename, skip_header):
    # a little roundabout but meant to replicate behavior of previous version that used np genfromtxt
    if skip_header == 0:
        header_opt = None
    else:
        header_opt = 0
    data = pd.read_csv(filename, header=header_opt).to_numpy()
    if data.shape[1] == 1:
        data = data[:, 0]
    return data
