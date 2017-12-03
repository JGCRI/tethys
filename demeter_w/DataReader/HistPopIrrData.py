"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Demeter-WD V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import numpy as np
from demeter_w.Utils.DataParser import getTXTContentArray as ArrayTXTRead
from demeter_w.Utils.DataParser import getContentArray as ArrayCSVReader

def getIrrYearData(settings):
    
    '''Update the irrigation maps to include a unique map for each historical time period'''
    
    irr = {}
    GMIA_irr = ArrayCSVReader(settings.Irrigation_GMIA,1)
    HYDE_irr = ArrayCSVReader(settings.Irrigation_HYDE,1)
    H_years  = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]
    G_years  = [2005]
    years    = [int(x) for x in settings.years]
    years_new= years[:]
    
    for i in range(0, len(years)):
        if years[i] < 2005:
            if years[i] >= max(H_years):
                years_new[i] = max(H_years)
            else:                
                for j in range (0, len(H_years)-1):
                    if years[i] >= H_years[j] and years[i] < H_years[j+1]:
                        years_new[i] = H_years[j] # use previous year
                        
            if not str(years_new[i]) in irr:      
                irr[str(years_new[i])] = HYDE_irr[:,H_years.index(years_new[i])]       
                #irr[str(years_new[i])] = importHYDE(settings.irr1 + "HYDE/crop" + str(years_new[i]) + "AD.asc", settings.mapsize)
            print '------Use HYDE ' + str(years_new[i]) + ' Irrigation Area Data for ' + str(years[i])       
                                                              
        elif years[i] >= 2005:
            if years[i] >= max(G_years):
                years_new[i] = max(G_years)
            else:
                for j in range (0, len(G_years)-1):
                    if years[i] >= G_years[j] and years[i] < G_years[j+1]:
                        years_new[i] = G_years[j] # use previous year
                        
            if not str(years_new[i]) in irr:
                irr[str(years_new[i])] = GMIA_irr[:]        
                #irr[str(years_new[i])] = importGMIA(settings.irr1 + "GMIA/gmia_v5_aei_ha.asc", settings.mapsize)
            print '------Use FAO-GMIA ' + str(years_new[i]) + ' Irrigation Area Data for ' + str(years[i])  
                
    irr['years'] = years # years (integer) from settings
    irr['years_new'] = years_new # years to import irrigation data (integer) corresponding to years  
    
    return irr

# def importHYDE(filename, mapsize):
#     
#     orig = ArrayTXTRead(filename,6)
#     orig[orig == -9999] = 0
#     new  = np.zeros(mapsize, dtype=float)
#     for i in range(0, mapsize[0]):
#         for j in range(0, mapsize[1]):
#             new[mapsize[0]-1-i,j] = np.sum(orig[i*6:i*6+6,j*6:j*6+6])
#     
#     return new
#     
#     
# def importGMIA(filename, mapsize):
#     
#     orig = ArrayTXTRead(filename,6)
#     orig[orig == -9] = 0
#     new  = np.zeros(mapsize, dtype=float)
#     for i in range(0, mapsize[0]):
#         for j in range(0, mapsize[1]):
#             new[mapsize[0]-1-i,j] = np.sum(orig[i*6:i*6+6,j*6:j*6+6])*0.01 # ha to km2
#             
#     return new
# 
# 
# def import2000(filename, mapsize):
#     
#     orig = ArrayTXTRead(filename,0)
#     new  = np.zeros(mapsize, dtype=float)
#     for i in range(0, orig.shape[0]):
#         new[i,:] = orig[orig.shape[0]-1-i,:]
#             
#     return new

def getPopYearData(settings):
    
    '''Update the population maps to include a unique map for each historical time period'''
    
    pop = {}
    GPW_pop = ArrayCSVReader(settings.Population_GPW,1)
    HYDE_pop = ArrayCSVReader(settings.Population_HYDE,1)
    
    H_years  = [1750, 1760, 1770, 1780, 1790, 1800, 1810, 1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980]
    G_years  = [1990, 1995, 2000, 2005, 2010, 2015]
    years    = [int(x) for x in settings.years]
    years_new= years[:]

    for i in range(0, len(years)):
        if years[i] < 1990:
            if years[i] >= max(H_years):
                years_new[i] = max(H_years)
            else:                
                for j in range (0, len(H_years)-1):
                    if years[i] >= H_years[j] and years[i] < H_years[j+1]:
                        years_new[i] = H_years[j] # use previous year
                        
            if not str(years_new[i]) in pop:
                pop[str(years_new[i])] = HYDE_pop[:,H_years.index(years_new[i])]         
                #pop[str(years_new[i])] = importHYDE(settings.pop + "HYDE/popc_" + str(years_new[i]) + "AD.asc", settings.mapsize, settings.mapIndex)
            print '------Use HYDE ' + str(years_new[i]) + ' Population Data for ' + str(years[i])       
                                                              
        elif years[i] >= 1990:
            if years[i] >= max(G_years):
                years_new[i] = max(G_years)
            else:
                for j in range (0, len(G_years)-1):
                    if years[i] >= G_years[j] and years[i] < G_years[j+1]:
                        years_new[i] = G_years[j] # use previous year
                        
            if not str(years_new[i]) in pop: 
                pop[str(years_new[i])] = GPW_pop[:,G_years.index(years_new[i])]             
                #pop[str(years_new[i])] = importGPW(settings.pop + "GPW/popc_v3_" + str(years_new[i]) + ".asc", settings.mapsize, settings.mapIndex)
            print '------Use GPW ' + str(years_new[i]) + ' Population Data for ' + str(years[i])  
                
    pop['years'] = years # years (integer) from settings
    pop['years_new'] = years_new # years to import population data (integer) corresponding to years                
                   
    return pop

# def importHYDE(filename, mapsize):
#     
#     orig = ArrayTXTRead(filename,6)
#     orig[orig == -9999] = 0
#     new  = np.zeros(mapsize, dtype=float)
#     for i in range(0, mapsize[0]):
#         for j in range(0, mapsize[1]):
#             new[mapsize[0]-1-i,j] = np.sum(orig[i*6:i*6+6,j*6:j*6+6])
#     
#     return new
#     
# def importGPW(filename, mapsize):
#     
#     orig = ArrayTXTRead(filename,6) 
#     new  = np.zeros(mapsize, dtype=float)
#     for i in range(0, orig.shape[0]):
#         new[i+64,:] = orig[orig.shape[0]-1-i,:]
#             
#     return new
# 
# def importWRI2000(filename, mapsize):
#     
#     orig = ArrayTXTRead(filename,6) 
#     new  = np.zeros(mapsize, dtype=float)
#     for i in range(0, orig.shape[0]):
#         new[i+69,:] = orig[orig.shape[0]-1-i,:]
#             
#     return new   
