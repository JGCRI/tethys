"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

"""

import os
import re
import csv
import numpy as np
from tethys.Utils.DataParser import getContentArray as ArrayCSVReader
from tethys.Utils.DataParser import GetArrayCSV
from tethys.Utils.Logging import Logger


def getIrrYearData(settings):
    
    '''Update the irrigation maps to include a unique map for each historical time period'''
    
    irr = {}
    GMIA_irr = ArrayCSVReader(settings.Irrigation_GMIA,1)
    HYDE_irr = ArrayCSVReader(settings.Irrigation_HYDE,1)
    H_years  = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000]
    G_years  = [2005]
    years    = [int(x) for x in settings.years]
    years_new= years[:]

    mainlog = Logger.getlogger()
    oldlvl = mainlog.setlevel(Logger.DEBUG)
    
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
            mainlog.write('------Use HYDE ' + str(years_new[i]) + ' Irrigation Area Data for ' +
                          str(years[i]) + '\n')
                                                              
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
            mainlog.write('------Use FAO-GMIA ' + str(years_new[i]) + ' Irrigation Area Data for ' +
                          str(years[i]) + '\n')
                
    irr['years'] = years # years (integer) from settings
    irr['years_new'] = years_new # years to import irrigation data (integer) corresponding to years  

    mainlog.setlevel(oldlvl)
    
    return irr

def getIrrYearData_Crops(settings):
    
    """
    Update the irrigation maps to include a unique map for each historical time period from Demeter outputs by crop types
    """
    
    irr = {}
    folder = settings.DemeterOutputFolder
    D_years = [] # is the range of years from Demeter outputs
    D_irr = {}
    
    for filename in os.listdir(folder): # Folder contains Demeter outputs in the fraction of a 0.5 degree grid cell
        if filename.endswith('.csv'):
            # yearstr = filename.split('.')[0].split('_')[-1]
            yearstr = re.sub("[^0-9]", "", filename)
            D_years.append(int(yearstr)) 
    
    years     = [int(x) for x in settings.years] # is the range of years from GCAM
    D_years = [number for number in D_years if number in years]
    D_years = sorted(D_years)
    years_new = years[:]
    inter     = list(set(D_years) & set(years)) # intersection of Demeter years and GCAM years

    for filename in os.listdir(folder): # Folder contains Demeter outputs in the fraction of a 0.5 degree grid cell
        if filename.endswith('.csv'):
            # yearstr = filename.split('.')[0].split('_')[-1]
            yearstr = re.sub("[^0-9]", "", filename)
            if int(yearstr) in inter:
                D_years.append(int(yearstr))
                tmp = GetArrayCSV(os.path.join(folder, filename), 1)
                index = check_header_Demeter_outputs(os.path.join(folder, filename))
                data = tmp[:,index] # irrigation fraction for 12 crops except biomass
                # 0.5 degree total grid cell square kilometers can be calculated using:  np.cos(np.radians(latitude)) * (111.32 * 110.57) * (0.5**2)
                latitude = np.cos(np.radians(tmp[:,-1])) * (111.32 * 110.57) * (0.5**2);
                newdata = data*latitude[:,np.newaxis] # The irrigated cropland area for each type of crop: total_grid_cell_square_kilometers * irrigated_crop_fraction
                newdata = np.insert(newdata,0,0, axis = 1) # no fraction data from Demeter for biomass, all zeros
                D_irr[yearstr] = newdata
    
    mainlog = Logger.getlogger()
    oldlvl = mainlog.setlevel(Logger.DEBUG)
    
    for i in range(0, len(years)):
        if years[i] >= max(D_years):
            years_new[i] = max(D_years)
        else:
            for j in range (0, len(D_years)-1):
                if years[i] >= D_years[j] and years[i] < D_years[j+1]:
                    years_new[i] = D_years[j] # use previous year
                    
        if not str(years_new[i]) in irr:
            irr[str(years_new[i])] = D_irr[str(years_new[i])][:,:]       
        mainlog.write('------Use Demeter ' + str(years_new[i]) + ' Irrigation Area Data for ' +
                      str(years[i]) + '\n')
    
    irr['years'] = years # years (integer) from settings
    irr['years_new'] = years_new # years to import irrigation data (integer) corresponding to years
    
    mainlog.setlevel(oldlvl)
    return irr

def getPopYearData(settings):
    
    '''Update the population maps to include a unique map for each historical time period'''
    
    pop = {}
    GPW_pop = ArrayCSVReader(settings.Population_GPW,1)
    HYDE_pop = ArrayCSVReader(settings.Population_HYDE,1)
    
    H_years  = [1750, 1760, 1770, 1780, 1790, 1800, 1810, 1820, 1830, 1840, 1850, 1860, 1870, 1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980]
    G_years  = [1990, 1995, 2000, 2005, 2010, 2015]
    years    = [int(x) for x in settings.years]
    years_new= years[:]

    mainlog = Logger.getlogger()
    oldlvl = mainlog.setlevel(Logger.DEBUG)

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
            mainlog.write('------Use HYDE ' + str(years_new[i]) + ' Population Data for ' +
                          str(years[i]) + '\n')
                                                              
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
            mainlog.write('------Use GPW ' + str(years_new[i]) + ' Population Data for ' +
                          str(years[i]) + '\n') 
                
    pop['years'] = years # years (integer) from settings
    pop['years_new'] = years_new # years to import population data (integer) corresponding to years

    mainlog.setlevel(oldlvl)
                   
    return pop

def check_header_Demeter_outputs(filename):
    # check the header (order) of the Demeter outputs are consistent and corresponding to the crops used in GCAM
    d_crops = ['corn_irr', 'fibercrop_irr', 'foddergrass_irr','fodderherb_irr',
               'misccrop_irr', 'oilcrop_irr', 'othergrain_irr', 'palmfruit_irr',
               'rice_irr', 'root_tuber_irr', 'sugarcrop_irr','wheat_irr']

    f = open(filename, "rU")
    reader = csv.reader(f, delimiter=",")
    headers = next(reader, None)
    f.close()
    headers = [x.lower() for x in headers]
    index = []
    for i in range(len(d_crops)):
        index.append(headers.index(d_crops[i]))

    return index