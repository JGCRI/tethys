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
def sub2ind(arraySize,rowSub,colSub):

    linearInd  = []
    if len(rowSub) != len(colSub):

        msg = 'sub2ind: rowSub and colSub must have equal lengths.  len(rowSub) = {}  len(colSub) = {}'.format(
            len(rowSub), len(colSub))
        logging.error(msg)

        raise DataError(msg)

    arr = tuple(arraySize)
    for i in range(0, len(rowSub)):
        temp = np.ravel_multi_index((rowSub[i],colSub[i]), arr, order='F')
        linearInd.append(temp)
        
    return np.array(linearInd)
