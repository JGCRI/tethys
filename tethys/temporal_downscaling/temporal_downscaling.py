"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

Original Algorithms:
Huang, Z., Hejazi, M., Li, X., Tang, Q., Leng, G., Liu, Y., Döll, P., Eisner, S., Gerten, D., Hanasaki, N. and Wada, Y., 2018. 
Reconstruction of global gridded monthly sectoral water withdrawals for 1971-2010 and analysis of their spatiotemporal patterns. 
Hydrology and Earth System Sciences Discussions, 22, pp.2117-2133.

Pre-processed Input Data Files:
1. Monthly average temperatures of 67420 cells in a period of years (indicated by filename)
2. Calculated monthly cdd (cooling degree day) and hdd (Heating degree day) data of 67420 cells in a period of years
3. For electricity water withdrawal, five parameters, the proportion of building and industry(including transportation) electricity use, the share of heating, cooling and others in building electricity use.
4. Monthly Irrigation Water withdrawal Data from other model

Temporal Downscaling (Year to Month) for water withdrawal of five sectors:
Domestic: Wada et al. (2011), need input data 1
Electricity: Voisin et al. (2013), need input data 2&3
Livestock, Mining and Manufacturing: Uniform distribution (based on days and leap years)
Irrigation: Monthly Irrigation Data from other models as the weighting factor to downscale gridded annually irrigation water withdrawals, need input data 4
"""

import os
import logging
import calendar

import numpy as np
import scipy.io as spio

from tethys.utils.data_parser import getContentArray as ArrayCSVRead
from tethys.temporal_downscaling.neighbor_basin import NeighborBasin


def GetDownscaledResults(settings, OUT, mapindex, regionID, basinID):    
    # Determine the temporal downscaling years

    # Determine the available temporal downscaling years according to other models and future years (not covered by other models)
    startyear  = int(settings.temporal_climate.split("_")[-2][:4])
    endyear    = int(settings.temporal_climate.split("_")[-1][:4])
    startyear1 = int(settings.Irr_MonthlyData.split("_")[-2][:4])
    endyear1   = int(settings.Irr_MonthlyData.split("_")[-1][:4])
    TempYears  = list(range(max(startyear,startyear1), min(endyear,endyear1) + 1))
    TDYears    = sorted(list(set(TempYears).intersection(settings.years)))
    TDYears    = sorted(TDYears + [i for i in settings.years if i > endyear])
    TDYearsD   = np.diff(TDYears) # Interval of TD Years
    GCAM_TDYears_Index  = [settings.years.index(i) for i in TDYears]
    
    if settings.UseDemeter: # Calculated the fraction values of each crop in each year for each cell
        NC  = np.shape(OUT.crops_wdirr)[1]
        NM  = np.shape(mapindex)[0]
        NY  = np.shape(GCAM_TDYears_Index)[0]
        F   = np.zeros((NM,NC,NY),dtype = float) # Fraction of each crop for each cell and each year.
        for j in range(np.shape(OUT.crops_wdirr)[1]):
            W    = OUT.wdirr[mapindex,:]
            W1   = W[:,GCAM_TDYears_Index]
            W    = OUT.crops_wdirr[mapindex,j,:]
            W2   = W[:,GCAM_TDYears_Index]
            F[:,j,:] = np.divide(W2,W1, out=np.zeros_like(W2), where=W1!=0) # NY > 1
            

    if settings.TemporalInterpolation and all(item > 1 for item in TDYearsD): # Linear interpolation to GCAM time periods
        W    = OUT.wddom[mapindex,:]
        OUT.WDom = LinearInterpolationAnnually(W[:,GCAM_TDYears_Index],TDYears)
        W    = OUT.wdelec[mapindex,:]
        OUT.WEle = LinearInterpolationAnnually(W[:,GCAM_TDYears_Index],TDYears)
        W    = OUT.wdirr[mapindex,:]
        OUT.WIrr = LinearInterpolationAnnually(W[:,GCAM_TDYears_Index],TDYears)
        W    = OUT.wdliv[mapindex,:]
        OUT.WLiv = LinearInterpolationAnnually(W[:,GCAM_TDYears_Index],TDYears)
        W    = OUT.wdmin[mapindex,:]
        OUT.WMin = LinearInterpolationAnnually(W[:,GCAM_TDYears_Index],TDYears)
        W    = OUT.wdmfg[mapindex,:]
        OUT.WMfg = LinearInterpolationAnnually(W[:,GCAM_TDYears_Index],TDYears)        
        
        if settings.UseDemeter: # Linear interpolation to fraction matrix
            Nyears = np.interp(np.arange(min(TDYears), max(TDYears) + 1), TDYears, TDYears)
            FNew = np.zeros((NM,NC,len(Nyears)),dtype = float)
            for j in range(np.shape(OUT.crops_wdirr)[1]):
                FNew[:,j,:]  = LinearInterpolationAnnually(F[:,j,:],TDYears)    

        # Update the TDYears to new values
        TDYears = list(np.interp(np.arange(min(TDYears), max(TDYears) + 1), TDYears, TDYears).astype(int))    

    else:
        W    = OUT.wddom[mapindex,:]
        OUT.WDom = W[:,GCAM_TDYears_Index]
        W    = OUT.wdelec[mapindex,:]
        OUT.WEle = W[:,GCAM_TDYears_Index]
        W    = OUT.wdirr[mapindex,:]
        OUT.WIrr = W[:,GCAM_TDYears_Index]
        W    = OUT.wdliv[mapindex,:]
        OUT.WLiv = W[:,GCAM_TDYears_Index]
        W    = OUT.wdmin[mapindex,:]
        OUT.WMin = W[:,GCAM_TDYears_Index]
        W    = OUT.wdmfg[mapindex,:]
        OUT.WMfg = W[:,GCAM_TDYears_Index]
        
        if settings.UseDemeter:
            FNew = np.copy(F)

    settings.TDYears    = TDYears
    
    # Index of TDYears in Temperature data and GCAM
    Temp_TDYears_Index = []
    for i in TDYears:
        if i > endyear:
            Temp_TDYears_Index.append(TempYears.index(endyear))
        else:
            Temp_TDYears_Index.append(TempYears.index(i))
        
    Temp_TDMonths_Index = np.zeros((len(TDYears)*12,), dtype = int)
    N = 0

    for i in Temp_TDYears_Index:
        Temp_TDMonths_Index[N*12:(N+1)*12] = np.arange(i*12, (i+1)*12)
        N += 1

    logging.debug('------ Temporal downscaling is available for Year: {}'.format(TDYears))

    # load climate data
    tclim = np.load(settings.temporal_climate)
    
    dom = {}

    dom['tas'] = tclim['tas'][:, Temp_TDMonths_Index]
    dom['DomesticR'] = ArrayCSVRead(settings.Domestic_R, 1)
    
    ele = {}
    ele['hdd'] = tclim['hdd'][:, Temp_TDMonths_Index]
    ele['cdd'] = tclim['cdd'][:, Temp_TDMonths_Index]

    # The parameters pb, ph, pc, pu, pit are all obtained from GCAM.
    ele['building']  = ArrayCSVRead(settings.Elec_Building,0)[:,Temp_TDYears_Index]
    ele['industry']  = ArrayCSVRead(settings.Elec_Industry,0)[:,Temp_TDYears_Index]
    ele['heating']   = ArrayCSVRead(settings.Elec_Building_heat,0)[:,Temp_TDYears_Index]
    ele['cooling']   = ArrayCSVRead(settings.Elec_Building_cool,0)[:,Temp_TDYears_Index]
    ele['others']    = ArrayCSVRead(settings.Elec_Building_others,0)[:,Temp_TDYears_Index]
    ele['region']    = regionID

    """Domestic"""
    OUT.twddom = Domestic_Temporal_Downscaling(dom, OUT.WDom, settings.TDYears)
    
    """Electricity"""
    OUT.twdelec = Electricity_Temporal_Downscaling(ele, OUT.WEle, settings.TDYears)

    # Monthly Irrigation Data from other models only available during 1971-2010
    irr, irrprofile  = GetMonthlyIrrigationData(settings.Irr_MonthlyData, Temp_TDMonths_Index, settings.coords)
    
    # Monthly Irrigation Data from other models only available during 1971-2010
    irr, irrprofile  = GetMonthlyIrrigationData(settings.Irr_MonthlyData, Temp_TDMonths_Index, settings.coords)
    
    """Irrigation"""
    OUT.twdirr = Irrigation_Temporal_Downscaling(irr, irrprofile, OUT.WIrr, settings.TDYears, basinID)
    if settings.UseDemeter: # Divide the temporal downscaled irrigation water demand ("twdirr") by crops
        OUT.crops_twdirr = Irrigation_Temporal_Downscaling_Crops(OUT.twdirr,FNew)

    """Livestock, Mining and Manufacturing"""
    
    OUT.twdliv = AnnualtoMontlyUniform(OUT.WLiv, TDYears)
    OUT.twdmin = AnnualtoMontlyUniform(OUT.WMin, TDYears)
    OUT.twdmfg = AnnualtoMontlyUniform(OUT.WMfg, TDYears)
    

def AnnualtoMontlyUniform(WD, years):
    """
    Global gridded annual water withdrawal to monthly water withdrawal
    For Livestock, Mining and Manufacturing: Uniform distribution
    WD : spatially downscaled water withdrawal (dimension: 67420 x nyear)
    years : list of years for temporal downscaling
    """
    
    ny = len(years)
    nm = ny*12
    WT = np.zeros((np.shape(WD)[0],nm), dtype=float)

    for y in years:
        M = set_month_arrays(y)
        N = years.index(y)
        WT[:,N*12:(N+1)*12] = get_monthly_data(WD[:,N], M)
        
    return WT
    
def set_month_arrays(Year):
    # Calculate the days in each month of a year
    M  = np.zeros((12,), dtype=int) # year, month, number of days in month
    M1 = [31,    28,    31,    30,    31,    30,    31,    31,    30,    31,    30,    31]
    M2 = [31,    29,    31,    30,    31,    30,    31,    31,    30,    31,    30,    31]
    
    if calendar.isleap(Year): # leap year
        M = M2[:]
    else: # regular year
        M = M1[:]        
    return M

def get_monthly_data(data, M):
    # divide annual data into monthly data
    out  = np.zeros((data.shape[0],12),dtype = float)
    sumM = np.sum(M)
    for i in range(12):
        out[:,i] = data[:]*M[i]/sumM
    
    return out

def GetMonthlyIrrigationData(filename, monthindex, coords):
    """
    Get the monthly irrigation Data (irrdata) from other model as weighting factors; 
    converted into the format (Year: 1971-2010; Unit: kg m-2 s-1; Dimension: 67420, number of TDYears*12)
    
    Get the irrigation monthly profiles (irrprofile) using averaged monthly irrigation from historical data 
    as weighting factors for futures years
    """

    datagrp = spio.netcdf.netcdf_file(filename, 'r')
    
    nm  = int(len(datagrp.variables['months'][:].copy()))
    irrdataall = datagrp.variables['pirrww'][:,:].copy()
    irrdata    = irrdataall[:,monthindex]
    
    datagrp.close()
    
    # Calculate the irr profile (Averaged monthly irrigation from historical data, e.g. averaged 1971-2010)
    irrprofile = np.zeros((coords.shape[0],12),dtype = float)
    for m in range(12):
        mi = range(m, nm, 12)
        irrprofile[:, m] = np.mean(irrdataall[:, mi], 1)
    
    
    return irrdata, irrprofile

def Domestic_Temporal_Downscaling(data, W, years):
    """
    data: structure: 'tas' and 'R'
        'tas': Temp Data (Monthly) for domestic category; 
            converted into the format (Year: 1971-2010; Unit: C; Dimension: 67420, number of TDYears*12)
        'R'  : a dimensionless amplitude, which adjusts the relative difference in domestic water withdrawal 
            between the months with the warmest and the coldest temperatures
    W: water withdrawal of domestic sector, dimension: 67420,NY
    years: the list of years for temporal downscaling
    TDW: Temporally Downscaled W, dimension: 67420, NY*12
    """

    TDW = np.zeros((np.shape(data['tas'])[0],len(years)*12),dtype = float)
    
    for i in range(np.shape(data['tas'])[0]):
        R = data['DomesticR'][i]       
        for j in years:
            N = years.index(j)
            monT = data['tas'][i,N*12:(N+1)*12]
            monT[np.isnan(monT)]=0
            if np.sum(monT) == 0: # if the tas data is not available for this gird, use neighbor grid with higher temp
                monT1 = data['tas'][i-1,N*12:(N+1)*12]
                monT2 = data['tas'][i+1,N*12:(N+1)*12]
                if np.mean(monT1) >= np.mean(monT2):
                    tmp = (monT1-np.mean(monT1))/(np.max(monT1)-np.min(monT1))*R+1
                else:
                    tmp = (monT2-np.mean(monT2))/(np.max(monT2)-np.min(monT2))*R+1
            else:
                tmp = (monT-np.mean(monT))/(np.max(monT)-np.min(monT))*R+1
            TDW[i,N*12:(N+1)*12] = W[i,N]*tmp/12
        
    return TDW

def Electricity_Temporal_Downscaling(data, W, years):
    
    """
    data: structure:  'hdd', 'cdd','building','industry','heating','cooling','others'     
            'hdd':      calculated monthly HDD according to the original daily air temperature of Temp 
                        (Year: 1971-2010; Unit: C; Dimension: 67420, number of TDYears*12)
            'cdd':      calculated monthly CDD according to the original daily air temperature of Temp 
                        (Year: 1971-2010; Unit: C; Dimension: 67420, number of TDYears*12)
            'building': the proportion of total electricity use for building
            'industry': the proportion of total electricity use for industry; Pb + Pi = 1
            'heating':  the proportion of total building electricity use for heating
            'cooling':  the proportion of total building electricity use for cooling
            'others':   the proportion of total building electricity use for other home utilities; Ph + Pc + Po = 1
            'region":   the region ID for 67420 grids, 67420*1
    W:  water withdrawal of electricity sector, dimension: 67420,NY
    years: the list of years for temporal downscaling
    TDW: Temporally Downscaled W, dimension: 67420, NY*12
    """
    
    TDW = np.zeros((np.shape(W)[0],len(years)*12),dtype = float)
    
    for i in range(np.shape(W)[0]):
        ID = data['region'][i]-1
        if  ID >= 0:     
            for j in years:
                N = years.index(j)
                HDD = data['hdd'][i,N*12:(N+1)*12]
                CDD = data['cdd'][i,N*12:(N+1)*12]
                HDD[np.isnan(HDD)] = 0
                CDD[np.isnan(CDD)] = 0
                SH  = np.sum(HDD)
                SC  = np.sum(CDD)
                Bu  = data['building'][ID,N]
                In  = data['industry'][ID,N]
                He  = data['heating'][ID,N]
                Co  = data['cooling'][ID,N]
                Ot  = data['others'][ID,N]
                
                if SH >= 650 and SC >= 450:
                    P = Bu * (He*HDD/SH + Co*CDD/SC + Ot/12) + In/12
                elif SH >= 650 and SC < 450:
                    P = Bu * ((He+Co)*HDD/SH + Ot/12) + In/12
                elif SH < 650 and SC >= 450:
                    P = Bu * ((He+Co)*CDD/SC + Ot/12) + In/12
                else:
                    P = (Bu + In) / 12 * np.ones(12)                
                
                TDW[i,N*12:(N+1)*12] = W[i,N]*P
        
    return TDW

def Irrigation_Temporal_Downscaling(data, dataprofile, W, years, basins):
    
    """
    data: Irrigation Data (Monthly) from other model as weighting factors; converted into the format 
           (Year: 1971-2010; Unit: kg m-2 s-1; Dimension: 67420, number of TDYears*12)
    W: water withdrawal of irrigation sector, dimension: 67420,NY
    years: the list of years for temporal downscaling
    The weighting factors will be aggregated and performed at basin scale (NB = 235)
    basins: the basin ID (1-235) for 67420 grids, 67420*1
    TDW: Temporally Downscaled W, dimension: 67420, NY*12
    """
    
    NB = np.max(basins)
    NM = np.shape(W)[0]
    NT = len(years)*12
    Ndata = data.shape[1]
    NY = len(years)
    TDW = np.zeros((NM,NT),dtype = float)
    data_basin = np.zeros((NB,NT),dtype = float)
    W_basin = np.zeros((NB,NY),dtype = float)
    
    # Aggregate data into basin scale
    for index in range(0, NM):
        for m in range(0, NT): 
            if m >=  Ndata:  # For future years, use irr profile as weighting factors
                mi = m % 12
                data_basin[basins[index] - 1, m] += dataprofile[index, mi]
            else: # For available years, use irr data from other model as weighting factors
                if not np.isnan(data[index, m]) and basins[index] > 0:
                    data_basin[basins[index] - 1, m] += data[index, m]
        for y in range(0, NY): 
            if not np.isnan(W[index, y]) and basins[index] > 0:
                W_basin[basins[index] - 1, y] += W[index, y]   
                
    # Downscale the W data
    dist_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reference/dist.csv')
    Neigbor = NeighborBasin(dist_file) # dist.csv is in the reference folder
    for i in range(NM):
        for j in years:
            N = years.index(j)
            BasinID = basins[i] - 1
            monIrr = data_basin[BasinID, N*12:(N+1)*12]
            if W_basin[BasinID, N] > 0:
                if monIrr.sum() > 0:
                    TDW[i,N*12:(N+1)*12] = W[i,N]*monIrr/monIrr.sum()
                else:                    
                    IDs     = Neigbor.d[str(basins[i])][1:]
                    n       = 0
                    for d in IDs:
                        monIrr = data_basin[d-1, N*12:(N+1)*12]
                        if monIrr.sum() > 0:
                            TDW[i,N*12:(N+1)*12] = W[i,N]*monIrr/monIrr.sum()
                            break
                        else:
                            n += 1
                            continue 
                    if n == len(IDs):
                        AllIds = Neigbor.d_all[str(basins[i])][1]
                        for d in AllIds:
                            monIrr = data_basin[d-1, N*12:(N+1)*12]
                            if monIrr.sum() > 0:
                                TDW[i,N*12:(N+1)*12] = W[i,N]*monIrr/monIrr.sum()
                                break
                            else:
                                continue
                                      
    return TDW

def Irrigation_Temporal_Downscaling_Crops(twdirr,Fraction):
    
    """
    Divide the temporal downscaled irrigation water demand ("twdirr") by crops
    For each year, the fraction of a certain crop for each cell is stored in "Fraction"
    """

    NC  = np.shape(Fraction)[1]
    NT  = np.shape(twdirr)[1]
    NM  = np.shape(twdirr)[0]
    TDW = np.zeros((NM,NC,NT),dtype = float)

    for i in range(NC):
        for j in range(NT):
            index = int(j/12)
            TDW[:,i,j] = twdirr[:,j]*Fraction[:,i,index]
    
    return TDW

def LinearInterpolationAnnually(data,years):
    """
    data: dimension is [67420, NY]
    years: the list of years, length is NY, for example: [1990, 2005, 2010]
    Interpolate values linearly between years to create annual results
    Out: dimension is [67420, NNY], for example, NNY is 21
    """
    Nyears = np.interp(np.arange(min(years), max(years) + 1), years, years)
    NM     = np.shape(data)[0]
    out    = np.zeros((NM,len(Nyears)),dtype = float)
    for i in range(NM):
        out[i, :] = np.interp(np.arange(min(years), max(years) + 1), years, data[i, :])
    
    return out
