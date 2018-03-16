'''
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
'''

import GCAMOutputs
import GCAMutil


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


class ConfigSettings():
    
    def __init__(self):
        self.ProjectName       = None
        self.InputFolder       = None
        self.OutputFolder      = None        
        self.rgnmapdir         = None        
        self.NY                = None      # Number of Years
        self.mapsize           = [360,720] # Default value
        self.PerformDiagnostics= 1         # Perform diagnostics, default is 1
        self.PerformTemporal   = 0
        self.UseGCAMDatabase   = 1         # Read from GCAM Database, default is 1
        self.GCAM_DBpath       = None        
        self.GCAM_DBfile       = None
        self.GCAM_query        = None
        self.OutputFormat      = 0         # csv and/or netcdf, default is 0
        self.OutputUnit        = 0         # default is None
        self.years             = None      # List of Year Names according to NY
        self.read_irrS         = 0
        
        
    def setGCAMDataFiles(self):

        if not self.UseGCAMDatabase:
            (_, self.regions_ordered) = GCAMutil.rd_rgn_table(self.RegionNames)
        else:
            # clearfolder(self.GCAM_CSV)
            GCAMOutputs.GCAMData(self) # Query GCAM database
        
        pathname = self.GCAM_CSV
        
        # All the following files are csv files and no header line                
        self.pop_tot           = pathname + 'pop_tot.csv'
        self.rgn_wddom         = pathname + 'withd_dom.csv'
        self.rgn_wdelec        = pathname + 'withd_elec.csv'
        self.rgn_wdmfg         = pathname + 'withd_manuf.csv'
        self.rgn_wdmining      = pathname + 'withd_mining.csv'
        self.wdliv             = pathname + 'withd_liv.csv'
        self.irrArea           = pathname + 'irrA.csv'
        self.irrV              = pathname + 'withd_irrV.csv'
        if  self.read_irrS:
            self.irrShare      = pathname + 'irrS.csv'
        else:
            self.irrShare      = None
    
    def help(self):
        
        print 
    '''
    License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
    Copyright (c) 2017, Battelle Memorial Institute

    Class: DataReader.ConfigSettings
    
    Stores required input information and control parameters
     
    '''   
