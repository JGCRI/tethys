"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-W V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


% All the following files are csv files and no header line:
% pop_tot        -
% rgn_wddom      -
% rgn_wdelec     -
% rgn_wdmfg      -
% rgn_wdmining   -
% wdliv          -
% irrArea        -
% irrV           -
% irrShare       - data of irrigation share

% Note that pop_tot should have data for all regions, even ones
% that never appear in a region mapping together (e.g., China and its provinces).
"""

from Utils.CSVParser import getContentArray as ArrayCSVReader
from shutil import copyfile

def getGCAMData(settings):
    
    '''dictionary GISData{} saves the data related to GCAM data'''
    GCAMData = {}
    #GCAMData['pop_fac']      = ArrayCSVReader(settings.pop_fac,0)
    GCAMData['pop_tot']      = ArrayCSVReader(settings.pop_tot,0)
    GCAMData['rgn_wddom']    = ArrayCSVReader(settings.rgn_wddom,0)
    GCAMData['rgn_wdelec']   = ArrayCSVReader(settings.rgn_wdelec,0)
    GCAMData['rgn_wdmfg']    = ArrayCSVReader(settings.rgn_wdmfg,0)
    GCAMData['rgn_wdmining'] = ArrayCSVReader(settings.rgn_wdmining,0)
    GCAMData['wdliv']        = ArrayCSVReader(settings.wdliv,0)
    GCAMData['irrArea']      = ArrayCSVReader(settings.irrArea,0)
    GCAMData['irrV']         = ArrayCSVReader(settings.irrV,0)

    if settings.read_irrS:
        GCAMData['irrShare'] = ArrayCSVReader(settings.irrShare,0)
        print '------Used pre-calculated irrigation shares---'
    else:
    # GCAM has already calculated irrigated (vice total) area.  
    # Setting irrShare to a scalar will signal the disaggregation function to ignore this factor.    
        GCAMData['irrShare'] = 1        
    
    # copy the pop_tot file to output folder
    copyfile(settings.pop_tot, settings.OutputFolder + 'GCAM_pop_tot.csv')
    
    return GCAMData
