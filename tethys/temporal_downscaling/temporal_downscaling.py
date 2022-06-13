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

from tethys.utils.data_parser import get_array_csv
from tethys.temporal_downscaling.neighbor_basin import NeighborBasin


def GetDownscaledResults(temporal_climate, Irr_MonthlyData, years, UseDemeter, TemporalInterpolation, Domestic_R,
                         ele,
                         coords, OUT, regionID, basinID):
    # Determine the temporal downscaling years

    # Determine the available temporal downscaling years according to other models and future years (not covered by other models)
    startyear = int(temporal_climate.split("_")[-2][:4])
    endyear = int(temporal_climate.split("_")[-1][:4])
    startyear1 = int(Irr_MonthlyData.split("_")[-2][:4])
    endyear1 = int(Irr_MonthlyData.split("_")[-1][:4])
    TempYears = list(range(max(startyear, startyear1), min(endyear, endyear1) + 1))
    TDYears = sorted(list(set(TempYears).intersection(years)))
    TDYears = sorted(TDYears + [i for i in years if int(i) > endyear])
    TDYearsD = np.diff(TDYears)  # Interval of TD Years
    GCAM_TDYears_Index = [years.index(i) for i in TDYears]
    
    if UseDemeter:  # Calculated the fraction values of each crop in each year for each cell
        NC = np.shape(OUT.crops_wdirr)[1]
        NM = np.shape(regionID)[0]
        NY = np.shape(GCAM_TDYears_Index)[0]
        F = np.zeros((NM, NC, NY), dtype=float)  # Fraction of each crop for each cell and each year.
        for j in range(np.shape(OUT.crops_wdirr)[1]):
            W1 = OUT.wdirr[:, GCAM_TDYears_Index]
            W2 = OUT.crops_wdirr[:, j, GCAM_TDYears_Index]
            F[:, j, :] = np.divide(W2, W1, out=np.zeros_like(W2), where=W1 != 0)  # NY > 1

    if TemporalInterpolation and all(item > 1 for item in TDYearsD):  # Linear interpolation to GCAM time periods
        OUT.WDom = LinearInterpolationAnnually(OUT.wddom[:, GCAM_TDYears_Index], TDYears)
        OUT.WEle = LinearInterpolationAnnually(OUT.wdelec[:, GCAM_TDYears_Index], TDYears)
        OUT.WIrr = LinearInterpolationAnnually(OUT.wdirr[:, GCAM_TDYears_Index], TDYears)
        OUT.WLiv = LinearInterpolationAnnually(OUT.wdliv[:, GCAM_TDYears_Index], TDYears)
        OUT.WMin = LinearInterpolationAnnually(OUT.wdmin[:, GCAM_TDYears_Index], TDYears)
        OUT.WMfg = LinearInterpolationAnnually(OUT.wdmfg[:, GCAM_TDYears_Index], TDYears)
        
        if UseDemeter:  # Linear interpolation to fraction matrix
            Nyears = np.interp(np.arange(min(TDYears), max(TDYears) + 1), TDYears, TDYears)
            FNew = np.zeros((NM, NC, len(Nyears)), dtype=float)
            for j in range(np.shape(OUT.crops_wdirr)[1]):
                FNew[:, j, :] = LinearInterpolationAnnually(F[:, j, :], TDYears)

        # Update the TDYears to new values
        TDYears = list(np.interp(np.arange(min(TDYears), max(TDYears) + 1), TDYears, TDYears).astype(int))    

    else:
        OUT.WDom = OUT.wddom[:, GCAM_TDYears_Index]
        OUT.WEle = OUT.wdelec[:, GCAM_TDYears_Index]
        OUT.WIrr = OUT.wdirr[:, GCAM_TDYears_Index]
        OUT.WLiv = OUT.wdliv[:, GCAM_TDYears_Index]
        OUT.WMin = OUT.wdmin[:, GCAM_TDYears_Index]
        OUT.WMfg = OUT.wdmfg[:, GCAM_TDYears_Index]
        
        if UseDemeter:
            FNew = np.copy(F)

    # Index of TDYears in Temperature data and GCAM
    Temp_TDYears_Index = []
    for i in TDYears:
        if i > endyear:
            Temp_TDYears_Index.append(TempYears.index(endyear))
        else:
            Temp_TDYears_Index.append(TempYears.index(i))
        
    Temp_TDMonths_Index = np.zeros((len(TDYears)*12,), dtype=int)
    N = 0

    for i in Temp_TDYears_Index:
        Temp_TDMonths_Index[N*12:(N+1)*12] = np.arange(i*12, (i+1)*12)
        N += 1

    logging.debug('------ Temporal downscaling is available for Year: {}'.format(TDYears))

    # load climate data
    tclim = np.load(temporal_climate)
    
    dom = {}

    dom['tas'] = tclim['tas'][:, Temp_TDMonths_Index]
    dom['DomesticR'] = get_array_csv(Domestic_R, 1)
    
    ele['hdd'] = tclim['hdd'][:, Temp_TDMonths_Index]
    ele['cdd'] = tclim['cdd'][:, Temp_TDMonths_Index]

    # The parameters pb, ph, pc, pu, pit are all obtained from GCAM.
    ele['region'] = regionID

    """Domestic"""
    OUT.twddom = Domestic_Temporal_Downscaling(dom, OUT.WDom, TDYears)
    
    """Electricity"""
    OUT.twdelec = Electricity_Temporal_Downscaling(ele, OUT.WEle, TDYears)
    
    # Monthly Irrigation Data from other models only available during 1971-2010
    irr, irrprofile = GetMonthlyIrrigationData(Irr_MonthlyData, Temp_TDMonths_Index, coords)
    
    """Irrigation"""
    OUT.twdirr = Irrigation_Temporal_Downscaling(irr, irrprofile, OUT.WIrr, TDYears, basinID)
    if UseDemeter:  # Divide the temporal downscaled irrigation water demand ("twdirr") by crops
        OUT.crops_twdirr = Irrigation_Temporal_Downscaling_Crops(OUT.twdirr, FNew)

    """Livestock, Mining and Manufacturing"""
    
    OUT.twdliv = AnnualtoMonthlyUniform(OUT.WLiv, TDYears)
    OUT.twdmin = AnnualtoMonthlyUniform(OUT.WMin, TDYears)
    OUT.twdmfg = AnnualtoMonthlyUniform(OUT.WMfg, TDYears)

    OUT.twdtotal = OUT.twddom + OUT.twdelec + OUT.twdirr + OUT.twdliv + OUT.twdmin + OUT.twdmfg  # add to get total

    return TDYears
    

def AnnualtoMonthlyUniform(WD, years):
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
        WT[:, N*12:(N+1)*12] = get_monthly_data(WD[:, N], M)
        
    return WT


def set_month_arrays(Year):
    # Calculate the days in each month of a year

    if calendar.isleap(Year):  # leap year
        return [31,    29,    31,    30,    31,    30,    31,    31,    30,    31,    30,    31]
    else:  # regular year
        return [31,    28,    31,    30,    31,    30,    31,    31,    30,    31,    30,    31]


def get_monthly_data(data, M):
    # divide annual data into monthly data
    out = np.zeros((data.shape[0], 12), dtype=float)
    sumM = np.sum(M)
    for i in range(12):
        out[:, i] = data[:]*M[i]/sumM
    
    return out


def GetMonthlyIrrigationData(filename, monthindex, coords):
    """
    Get the monthly irrigation Data (irrdata) from other model as weighting factors; 
    converted into the format (Year: 1971-2010; Unit: kg m-2 s-1; Dimension: 67420, number of TDYears*12)
    
    Get the irrigation monthly profiles (irrprofile) using averaged monthly irrigation from historical data 
    as weighting factors for futures years
    """

    datagrp = spio.netcdf.netcdf_file(filename, 'r')
    
    nm = int(len(datagrp.variables['months'][:].copy()))
    irrdataall = datagrp.variables['pirrww'][:, :].copy()
    irrdata = irrdataall[:, monthindex]
    
    datagrp.close()
    
    # Calculate the irr profile (Averaged monthly irrigation from historical data, e.g. averaged 1971-2010)
    irrprofile = np.zeros((coords.shape[0], 12), dtype=float)
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

    tas = data['tas'].reshape(-1, len(years), 12)
    tas[np.isnan(tas)] = 0
    tas_mean = np.mean(tas, axis=2, keepdims=True)
    tas_range = np.max(tas, axis=2, keepdims=True) - np.min(tas, axis=2, keepdims=True)

    # cells with no month temperature data are downscaled uniformly across months
    temp = data['DomesticR'].reshape(-1, 1, 1) * np.divide(tas - tas_mean, tas_range,
                                                           out=np.zeros_like(tas), where=tas_range != 0) + 1
    TDW = W[:, :, np.newaxis] * temp / 12

    return TDW.reshape(W.shape[0], len(years) * 12)


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

    # reshape to ncells x nyears x 12 months
    hdd_month = data['hdd'].reshape(W.shape[0], len(years), 12)
    cdd_month = data['cdd'].reshape(W.shape[0], len(years), 12)
    # replace nan with 0
    hdd_month[np.isnan(hdd_month)] = 0
    cdd_month[np.isnan(cdd_month)] = 0
    # compute yearly sums, keep axis for broadcasting
    hdd_year = np.sum(hdd_month, axis=2, keepdims=True)
    cdd_year = np.sum(cdd_month, axis=2, keepdims=True)
    # compute ratios
    hdd_frac = np.divide(hdd_month, hdd_year, out=np.zeros_like(hdd_month), where=hdd_year != 0)
    cdd_frac = np.divide(cdd_month, cdd_year, out=np.zeros_like(cdd_month), where=cdd_year != 0)

    # expand from regions to cells, add extra axis for broadcasting
    Bu = data['building'][data['region'] - 1, :, np.newaxis]
    In = data['industry'][data['region'] - 1, :, np.newaxis]
    He = data['heating'][data['region'] - 1, :, np.newaxis]
    Co = data['cooling'][data['region'] - 1, :, np.newaxis]
    Ot = data['others'][data['region'] - 1, :, np.newaxis]

    # formula reduces to uniform when hdd_year < 650 & cdd_year < 450
    P = np.ones((W.shape[0], len(years), 12)) / 12
    P = np.where((hdd_year >= 650) & (cdd_year >= 450), Bu * (He*hdd_frac + Co*cdd_frac + Ot/12) + In/12, P)
    P = np.where((hdd_year >= 650) & (cdd_year < 450), Bu * ((He+Co)*hdd_frac + Ot/12) + In/12, P)
    P = np.where((hdd_year < 650) & (cdd_year >= 450), Bu * ((He+Co)*cdd_frac + Ot/12) + In/12, P)

    # apply calculated monthly elec demand distribution to yearly elec water demand
    TDW = W[:, :, np.newaxis] * P

    return TDW.reshape(W.shape[0], len(years)*12)


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
    TDW = np.zeros((NM, NT), dtype=float)
    data_basin = np.zeros((NB, NT), dtype=float)
    W_basin = np.zeros((NB, NY), dtype=float)
    
    # Aggregate data into basin scale
    for index in range(0, NM):
        for m in range(0, NT): 
            if m >= Ndata:  # For future years, use irr profile as weighting factors
                mi = m % 12
                data_basin[basins[index] - 1, m] += dataprofile[index, mi]
            else:  # For available years, use irr data from other model as weighting factors
                if not np.isnan(data[index, m]) and basins[index] > 0:
                    data_basin[basins[index] - 1, m] += data[index, m]
        for y in range(0, NY): 
            if not np.isnan(W[index, y]) and basins[index] > 0:
                W_basin[basins[index] - 1, y] += W[index, y]   
                
    # Downscale the W data
    dist_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reference/dist.csv')
    Neighbor = NeighborBasin(dist_file)  # dist.csv is in the reference folder
    for i in range(NM):
        for j in years:
            N = years.index(j)
            BasinID = basins[i] - 1
            monIrr = data_basin[BasinID, N*12:(N+1)*12]
            if W_basin[BasinID, N] > 0:
                if monIrr.sum() > 0:
                    TDW[i, N*12:(N+1)*12] = W[i, N]*monIrr/monIrr.sum()
                else:                    
                    IDs = Neighbor.d[str(basins[i])][1:]
                    n = 0
                    for d in IDs:
                        monIrr = data_basin[d-1, N*12:(N+1)*12]
                        if monIrr.sum() > 0:
                            TDW[i, N*12:(N+1)*12] = W[i, N]*monIrr/monIrr.sum()
                            break
                        else:
                            n += 1
                            continue 
                    if n == len(IDs):
                        AllIds = Neighbor.d_all[str(basins[i])][1]
                        for d in AllIds:
                            monIrr = data_basin[d-1, N*12:(N+1)*12]
                            if monIrr.sum() > 0:
                                TDW[i, N*12:(N+1)*12] = W[i, N]*monIrr/monIrr.sum()
                                break
                            else:
                                continue
                                      
    return TDW


def Irrigation_Temporal_Downscaling_Crops(twdirr, Fraction):
    
    """
    Divide the temporal downscaled irrigation water demand ("twdirr") by crops
    For each year, the fraction of a certain crop for each cell is stored in "Fraction"
    """

    NC = np.shape(Fraction)[1]
    NT = np.shape(twdirr)[1]
    NM = np.shape(twdirr)[0]
    TDW = np.zeros((NM, NC, NT), dtype=float)

    for i in range(NC):
        for j in range(NT):
            index = int(j/12)
            TDW[:, i, j] = twdirr[:, j]*Fraction[:, i, index]
    
    return TDW


def LinearInterpolationAnnually(data, years):
    """
    data: dimension is [67420, NY]
    years: the list of years, length is NY, for example: [1990, 2005, 2010]
    Interpolate values linearly between years to create annual results
    Out: dimension is [67420, NNY], for example, NNY is 21
    """
    nyears = 1 + max(years) - min(years)
    ncells = np.shape(data)[0]
    out = np.zeros((ncells, nyears), dtype=float)
    for i in range(ncells):
        out[i, :] = np.interp(np.arange(min(years), max(years) + 1), years, data[i, :])
    
    return out
