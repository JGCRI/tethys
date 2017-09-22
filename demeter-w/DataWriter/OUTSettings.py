"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""

class OUTSettings():
# Output file names

    def __init__(self):
        
        '''gridded results, 2D array, size: (360*720, NY)'''
        self.wdtotal  = None
        self.wdnonag  = None
        self.wddom    = None
        self.wdelec   = None
        self.wdmfg    = None
        self.wdmin    = None
        self.wdirr    = None
        self.wdliv    = None
        
        '''regional aggregates, 2D array, size: (NRegion, NY)'''       
        self.rtotal   = None
        self.rnonag   = None
        self.rdom     = None
        self.relec    = None
        self.rmfg     = None
        self.rmin     = None
        self.rirr     = None
        self.rliv     = None
        