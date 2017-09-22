"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import numpy as np
from demeter_w.Utils.Math import sub2ind
from demeter_w.Utils.Math import SizeR

def Rearranging(mapsize, GISData, rgnmapData):
    
    '''mapsize: [360,720]'''
    
    row0      = SizeR(GISData['area']) # row  = 67420
    # Create a matrix with all data 1. area 2 region #
    data      = np.zeros((row0,2), dtype=float)
    data[:,0] = GISData['area'] #1. Area of each grid
    data[:,1] = rgnmapData['rgnmapNONAG'][:] #GCAM 'primary' region
    
    nrow      = mapsize[0]
    ncol      = mapsize[1]
        
    # create various map structures: 1D
    mapAreaExt     = np.zeros((nrow*ncol,), dtype=float)
    # maps of the various GCAM region mappings: 1D
    map_rgn_nonag  = np.zeros((nrow*ncol,), dtype=int)
    map_rgn_ag     = np.zeros((nrow*ncol,), dtype=int)
    # linear index of map cell for each grid cell with coordinates (67420 cells)
    mapindex       = sub2ind(mapsize,GISData['coord'][:,4].astype(int)-1, GISData['coord'][:,3].astype(int)-1)
    # unit in km2 (conversion was applied earlier, 1 ha = 0.01 km2)
    mapAreaExt[mapindex]    = GISData['area']
    map_rgn_nonag[mapindex] = rgnmapData['rgnmapNONAG'][:]
    map_rgn_ag[mapindex]    = rgnmapData['rgnmapAG'][:]
    
    # Update classes GISData and rgnmapData
    GISData['mapAreaExt']       = mapAreaExt
    GISData['mapindex']         = mapindex # mapindex is the most needed output variable from this def
    rgnmapData['map_rgn_nonag'] = map_rgn_nonag
    rgnmapData['map_rgn_ag']    = map_rgn_ag