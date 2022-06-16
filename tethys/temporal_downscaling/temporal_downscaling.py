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

import logging
import calendar

import numpy as np
import scipy.io as spio

from tethys.utils.data_parser import get_array_csv


def GetDownscaledResults(temporal_climate, Irr_MonthlyData, years, UseDemeter, TemporalInterpolation, Domestic_R,
                         ele, basinlookup, OUT, regionID):

    TDYears = years

    if TemporalInterpolation:  # Linear interpolation to GCAM time periods

        logging.info('Linearly interpolating from GCAM years to annual timesteps')

        OUT.WDom = LinearInterpolationAnnually(OUT.wddom, years)
        OUT.WEle = LinearInterpolationAnnually(OUT.wdelec, years)
        OUT.WIrr = LinearInterpolationAnnually(OUT.wdirr, years)
        OUT.WLiv = LinearInterpolationAnnually(OUT.wdliv, years)
        OUT.WMin = LinearInterpolationAnnually(OUT.wdmin, years)
        OUT.WMfg = LinearInterpolationAnnually(OUT.wdmfg, years)

        # Update the TDYears to new values
        TDYears = list(range(min(TDYears), max(TDYears) + 1))

    else:
        OUT.WDom = OUT.wddom
        OUT.WEle = OUT.wdelec
        OUT.WIrr = OUT.wdirr
        OUT.WLiv = OUT.wdliv
        OUT.WMin = OUT.wdmin
        OUT.WMfg = OUT.wdmfg

    if UseDemeter:  # Calculated the fraction values of each crop in each year for each cell
        ncells = np.shape(OUT.crops_wdirr)[0]
        ncrops = np.shape(OUT.crops_wdirr)[1]
        W1 = OUT.wdirr.reshape(ncells, 1, -1)
        F = np.divide(OUT.crops_wdirr, W1, out=np.zeros_like(OUT.crops_wdirr), where=W1 != 0)
        if TemporalInterpolation:
            FNew = np.zeros((ncells, ncrops, max(TDYears) - min(TDYears) + 1), dtype=float)
            for j in range(ncrops):
                FNew[:, j, :] = LinearInterpolationAnnually(F[:, j, :], years)
        else:
            FNew = np.copy(F)

    logging.info('Loading monthly proxies')

    # Determine the available temporal downscaling years according to other models and future years
    temp_data_start = int(temporal_climate.split("_")[-2][:4])
    temp_data_end = int(temporal_climate.split("_")[-1][:4])
    irr_data_start = int(Irr_MonthlyData.split("_")[-2][:4])
    irr_data_end = int(Irr_MonthlyData.split("_")[-1][:4])

    temp_indices = [max(min(i, temp_data_end) - temp_data_start, 0) for i in TDYears]
    irr_indices = [max(min(i, irr_data_end) - irr_data_start, 0) for i in TDYears]
    elec_param_indices = [years.index(max(j for j in years if j <= i)) for i in TDYears]

    # load climate data
    tclim = np.load(temporal_climate)
    
    dom = {'tas': tclim['tas'].reshape(tclim['tas'].shape[0], -1, 12)[:, temp_indices],
           'DomesticR': get_array_csv(Domestic_R, 1).reshape(-1, 1, 1)}

    # The parameters pb, ph, pc, pu, pit are all obtained from GCAM.
    ele['hdd'] = tclim['hdd'].reshape(tclim['hdd'].shape[0], -1, 12)[:, temp_indices]
    ele['cdd'] = tclim['cdd'].reshape(tclim['cdd'].shape[0], -1, 12)[:, temp_indices]
    ele['region'] = regionID

    # Monthly Irrigation Data from other models only available during 1971-2010
    irr, irrprofile = GetMonthlyIrrigationData(Irr_MonthlyData, irr_indices)

    logging.info('Temporally downscaling domestic sector')
    OUT.twddom = Domestic_Temporal_Downscaling(dom, OUT.WDom, TDYears)
    
    logging.info('Temporally downscaling electricity sector')
    OUT.twdelec = Electricity_Temporal_Downscaling(ele, OUT.WEle, elec_param_indices)

    logging.info('Temporally downscaling irrigation sector')
    OUT.twdirr = Irrigation_Temporal_Downscaling(irr, irrprofile, OUT.WIrr, TDYears, basinlookup)
    if UseDemeter:  # Divide the temporal downscaled irrigation water demand ("twdirr") by crops
        OUT.crops_twdirr = Irrigation_Temporal_Downscaling_Crops(OUT.twdirr, FNew)

    logging.info('Temporally downscaling livestock, mining, and manufacturing sectors')
    OUT.twdliv = AnnualtoMonthlyUniform(OUT.WLiv, TDYears)
    OUT.twdmin = AnnualtoMonthlyUniform(OUT.WMin, TDYears)
    OUT.twdmfg = AnnualtoMonthlyUniform(OUT.WMfg, TDYears)

    logging.info('Calculating total')
    OUT.twdtotal = OUT.twddom + OUT.twdelec + OUT.twdirr + OUT.twdliv + OUT.twdmin + OUT.twdmfg  # add to get total

    return TDYears
    

def AnnualtoMonthlyUniform(WD, years):
    """
    Global gridded annual water withdrawal to monthly water withdrawal
    For Livestock, Mining and Manufacturing: Uniform distribution
    WD : spatially downscaled water withdrawal (dimension: 67420 x nyear)
    years : list of years for temporal downscaling
    """

    month_lens = np.asarray([month_lengths(year) for year in years]).reshape(1, len(years), 12)
    year_lens = np.sum(month_lens, axis=2, keepdims=True)

    WT = WD[:, :, np.newaxis] * month_lens / year_lens
        
    return WT.reshape(-1, len(years) * 12)


def month_lengths(year):
    # return the days in each month of a year

    if calendar.isleap(year):  # leap year
        return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else:  # regular year
        return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def GetMonthlyIrrigationData(filename, yearindex):
    """
    Get the monthly irrigation Data (irrdata) from other model as weighting factors; 
    converted into the format (Year: 1971-2010; Unit: kg m-2 s-1; Dimension: 67420, number of TDYears*12)
    
    Get the irrigation monthly profiles (irrprofile) using averaged monthly irrigation from historical data 
    as weighting factors for futures years
    """

    datagrp = spio.netcdf.netcdf_file(filename, 'r')
    irrdataall = datagrp.variables['pirrww'][:].copy()
    datagrp.close()

    irrdataall = irrdataall.reshape(irrdataall.shape[0], -1, 12)
    irrdata = irrdataall[:, yearindex]
    
    # Calculate the irr profile (Averaged monthly irrigation from historical data, e.g. averaged 1971-2010)
    irrprofile = np.mean(irrdataall, axis=1, keepdims=True)

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

    tas = data['tas']
    tas[np.isnan(tas)] = 0
    tas_mean = np.mean(tas, axis=2, keepdims=True)
    tas_range = np.max(tas, axis=2, keepdims=True) - np.min(tas, axis=2, keepdims=True)

    # cells with no month temperature data are downscaled uniformly across months
    temp = data['DomesticR'] * np.divide(tas - tas_mean, tas_range, out=np.zeros_like(tas), where=tas_range != 0) + 1
    TDW = W[:, :, np.newaxis] * temp / 12

    return TDW.reshape(W.shape[0], len(years) * 12)


def Electricity_Temporal_Downscaling(data, W, elec_param_indices):
    
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
    hdd_month = data['hdd']
    cdd_month = data['cdd']
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
    Bu = data['building'][data['region'] - 1][:, elec_param_indices, np.newaxis]
    In = data['industry'][data['region'] - 1][:, elec_param_indices, np.newaxis]
    He = data['heating'][data['region'] - 1][:, elec_param_indices, np.newaxis]
    Co = data['cooling'][data['region'] - 1][:, elec_param_indices, np.newaxis]
    Ot = data['others'][data['region'] - 1][:, elec_param_indices, np.newaxis]

    # formula reduces to uniform when hdd_year < 650 & cdd_year < 450
    P = np.ones((W.shape[0], len(elec_param_indices), 12)) / 12
    P = np.where((hdd_year >= 650) & (cdd_year >= 450), Bu * (He*hdd_frac + Co*cdd_frac + Ot/12) + In/12, P)
    P = np.where((hdd_year >= 650) & (cdd_year < 450), Bu * ((He+Co)*hdd_frac + Ot/12) + In/12, P)
    P = np.where((hdd_year < 650) & (cdd_year >= 450), Bu * ((He+Co)*cdd_frac + Ot/12) + In/12, P)

    # apply calculated monthly elec demand distribution to yearly elec water demand
    TDW = W[:, :, np.newaxis] * P

    return TDW.reshape(W.shape[0], len(elec_param_indices)*12)


def Irrigation_Temporal_Downscaling(data, dataprofile, W, years, basinlookup):
    
    """
    data: Irrigation Data (Monthly) from other model as weighting factors; converted into the format 
           (Year: 1971-2010; Unit: kg m-2 s-1; Dimension: 67420, number of TDYears*12)
    W: water withdrawal of irrigation sector, dimension: 67420,nyears
    years: the list of years for temporal downscaling
    The weighting factors will be aggregated and performed at basin scale (nbasins = 235)
    basins: the basin ID (1-235) for 67420 grids, 67420*1
    TDW: Temporally Downscaled W, dimension: 67420, nyears*12
    """
    
    ncells = W.shape[0]
    nyears = len(years)
    TDW = np.zeros((ncells, nyears, 12), dtype=float)

    data2 = data.reshape(data.shape[0], -1, 12)

    for basin, cells in basinlookup.items():
        irr_basin_months = np.sum(data2[cells], axis=0, keepdims=True)
        irr_basin_year = np.sum(irr_basin_months, axis=2, keepdims=True)
        TDW[cells] = W[cells, :, np.newaxis] * np.divide(irr_basin_months, irr_basin_year,
                                                         out=np.ones_like(irr_basin_months) / 12,
                                                         where=irr_basin_year != 0)

    return TDW.reshape(ncells, nyears * 12)


def Irrigation_Temporal_Downscaling_Crops(twdirr, Fraction):
    """
    Divide the temporal downscaled irrigation water demand ("twdirr") by crops
    For each year, the fraction of a certain crop for each cell is stored in "Fraction"
    """

    ncells = twdirr.shape[0]
    ncrops = Fraction.shape[1]

    # reshape to broadcast with common (cell, crop, year, month) dimensions
    TDW = twdirr.reshape(ncells, 1, -1, 12) * Fraction.reshape(ncells, ncrops, -1, 1)

    return TDW.reshape(ncells, ncrops, -1)


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
