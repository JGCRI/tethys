"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project:Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""
import logging
import numpy as np
from tethys.utils.exceptions import DataError


# Convert subscripts to linear indices
def sub2ind(array_size, row_sub, col_sub):

    linear_ind = []
    if len(row_sub) != len(col_sub):
        msg = 'sub2ind: row_sub and col_sub must have equal lengths.  len(row_sub) = {}  len(col_sub) = {}'.format(
            len(row_sub), len(col_sub))
        logging.error(msg)

        raise DataError(msg)

    arr = tuple(array_size)
    for i in range(0, len(row_sub)):
        temp = np.ravel_multi_index((row_sub[i], col_sub[i]), arr, order='F')
        linear_ind.append(temp)
        
    return np.array(linear_ind)
