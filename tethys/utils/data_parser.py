"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""
import numpy as np


def get_array_csv(filename, skip_header):
    return np.genfromtxt(filename, delimiter=',', skip_header=skip_header, filling_values='0')


def get_array_txt(filename, skip_header):
    return np.genfromtxt(filename, delimiter=' ', skip_header=skip_header, filling_values='0')
