"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project:Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""
import numpy as np

from tethys.Utils.Logging import Logger

#__all__ = ['sub2ind', 'ind2sub']

# get the size of a 2D array
def Size(l): 
    nrow = len(l)
    try:
        ncol = len(l[0])
    except:
        ncol = 1
    return nrow, ncol

def SizeR(l):
    nr = len(l)
    return nr

def SizeC(l):
    try:
        nc = len(l[0])
    except:
        nc = 1
    return nc
    
# Convert subscripts to linear indices
def sub2ind(arraySize,rowSub,colSub):
    linearInd  = []
    if len(rowSub) != len(colSub):
        mainlog = logger.getlogger()
        msg = 'sub2ind: rowSub and colSub must have equal lengths.  len(rowSub) = {}  len(colSub) = {}'.format(
            len(rowSub), len(colSub))
        mainlog.write(msg + '\n',
                      Logger.ERROR)
        raise DataError(msg)

    arr = tuple(arraySize)
    for i in range(0, len(rowSub)):
        temp = np.ravel_multi_index((rowSub[i],colSub[i]), arr, order='F')
        linearInd.append(temp)
        
    return np.array(linearInd)

# Convert linear indices to subscripts
def ind2sub(arraySize,index):
    ''' index is a list or 1d array'''
    linearInd  = np.zeros((len(index),2),dtype = int)
    arr = tuple(arraySize)
    for i in range(0, len(index)):
        temp = np.unravel_index(index[i], arr, order='F')
        linearInd[i] = np.array(temp)
    return linearInd
