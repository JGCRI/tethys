"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


Perform diagnostics to ensure that the temporally downscaled results of electricity, domestic and irrigation are reasonable
Livestock, Mining and Manufacturing Sectors are uniformly downscaled, thus diagnostics are not needed.

"""
import os
import logging

import numpy as np


def compare_temporal_downscaled(PerformDiagnostics, TDYears, OutputFolder, OUT, GISData):

    ## The outputs produced in this function are an extension of the debugging
    ## logs; therefore, if the logging level is set above DEBUG, we skip the
    ## calculations and the output
    if PerformDiagnostics != 1:
        return

    BasinNames = GISData['BasinNames']
    years = TDYears
    logging.info(f'Temporal Downscaling diagnostics (Global): downscaled results vs. results before temporal downscaling (Total Water, km3/yr)')
    
    # Print out the basin level comparison
    Sector = ['Year', 'Basin ID', 'Basin Name', 'After Spatial Downscaling', 'After Temporal Downscaling', 'Diff']
    Unit = " (km3/yr)"
    headerline = ",".join(Sector) + Unit

    values = []
    for i, name in enumerate(BasinNames):
        cells = GISData['basinlookup'][i + 1]
        year_values = np.sum(OUT.WIrr[cells], axis=0)
        month_sums = np.sum(OUT.twdirr.reshape(-1, len(years), 12)[cells], axis=(0, 2))

        for N, j in enumerate(years):
            values.append([str(j), str(i + 1), name, "%.3f" % year_values[N], "%.3f" % month_sums[N],
                           "%.3f" % (year_values[N] - month_sums[N])])
                
    with open(os.path.join(OutputFolder, 'Diagnostics_Temporal_Downscaling_Irrigation.csv'), 'w') as outfile:
        np.savetxt(outfile, values, delimiter=',', header=headerline, fmt='%s', comments='')

    logging.info('------Irrigation------')
    for N, j in enumerate(years):
        month_sum = np.sum(OUT.twdirr[:, N*12:(N+1)*12])
        year_value = np.sum(OUT.WIrr[:, N])
        diff = month_sum - year_value
        logging.info(f'Year {j:4d}:   {month_sum:.6f}    {year_value:.6f}    Diff= {diff:.6e}')

    logging.info('------Domestic------')
    for N, j in enumerate(years):
        month_sum = np.sum(OUT.twddom[:, N*12:(N+1)*12])
        year_value = np.sum(OUT.WDom[:, N])
        diff = month_sum - year_value
        logging.info(f'Year {j:4d}:   {month_sum:.6f}    {year_value:.6f}    Diff= {diff:.6e}')
        
    logging.info('------Electricity Generation------')
    for N, j in enumerate(years):
        month_sum = np.sum(OUT.twdelec[:, N*12:(N+1)*12])
        year_value = np.sum(OUT.WEle[:, N])
        diff = month_sum - year_value
        logging.info(f'Year {j:4d}:   {month_sum:.6f}    {year_value:.6f}    Diff= {diff:.6e}')
