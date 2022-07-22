"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

Perform diagnostics to ensure that the spatially downscaled results and initial aggregate results from GCAM are Consistent

"""

import os
import logging

import numpy as np
import pandas as pd

from tethys.data_writer.outputs import OUTSettings


def compare_downscaled_GCAMinput(PerformDiagnostics, NY, years, OutputFolder, RegionNames, GCAMData, OUT):
    # These calculations will be performed ONLY if we are logging debug-level output.
    # Otherwise, we skip the output and the calculations
    if PerformDiagnostics != 1:
        return

    logging.info(
        f"Spatial Downscaling diagnostics (Global Total): downscaled results vs. aggregated results from GCAM (Total Water, km3/yr)")

    NY = NY
    value = np.zeros((NY, 3), dtype=float)
    for y in range(0, NY):  # Global Total For Each Year in log

        # Global_DS     Global Total [km3/yr] from downscaled results
        value[y, 0] = sum(OUT.rtotal[:, y])
        # Global_GCAM   Global Total [km3/yr] from GCAM inputs
        value[y, 1] = sum(GCAMData['rgn_wddom'][:, y]) + sum(GCAMData['rgn_wdelec'][:, y]) + sum(
            GCAMData['rgn_wdmfg'][:, y]) + sum(GCAMData['rgn_wdmining'][:, y]) \
                      + sum(GCAMData['irrV'][:, y + 3]) + np.sum(GCAMData['wdliv'][:, :, y])
        value[y, 2] = value[y, 0] - value[y, 1]
        if years:
            yrout = years[y]
        else:
            yrout = y + 1

        msg = f'Year {yrout:4d}:  {value[y, 0]:12.6f}  {value[y, 1]:12.6f}  Diff= {value[y, 2]:12.6f}'
        logging.info(msg)

    # Comprehensive diagnostics information to file:
    category = ['Domestic', 'Electricity', 'Manufacturing', 'Mining', 'Livestock', 'Irrigation', 'Non-Agriculture',
                'Agriculture', 'Total']
    group = ['Downscaled_', 'GCAM_', 'Diff_']
    Sector = ['Year', 'Region ID', 'Region Name', 'GCAM Population (millions)']
    Unit = " (km3/yr)"

    headerline = ",".join(Sector) + "," + ",".join([prefix + s + Unit for prefix in group for s in category])
    extension = '.csv'
    OutputFilename = os.path.join(OutputFolder, 'Diagnostics_Spatial_Downscaling{}'.format(extension))

    Regions = pd.read_csv(RegionNames, index_col='region_id').to_dict()['region']
    NR = len(Regions)

    # Regions.insert(0, 'Global') # Add "Global" to regions
    Regions[0] = 'Global'
    Years = years
    Population = GCAMData['pop_tot'] / 1e6

    # Add Global data to all
    Population = np.vstack([sum(Population), Population])
    OUT.rtotal = np.vstack([sum(OUT.rtotal), OUT.rtotal])
    OUT.rnonag = np.vstack([sum(OUT.rnonag), OUT.rnonag])
    OUT.rdom = np.vstack([sum(OUT.rdom), OUT.rdom])
    OUT.relec = np.vstack([sum(OUT.relec), OUT.relec])
    OUT.rmfg = np.vstack([sum(OUT.rmfg), OUT.rmfg])
    OUT.rmin = np.vstack([sum(OUT.rmin), OUT.rmin])
    OUT.rirr = np.vstack([sum(OUT.rirr), OUT.rirr])
    OUT.rliv = np.vstack([sum(OUT.rliv), OUT.rliv])

    GCAMOUT = OUTSettings()
    wdliv = np.zeros((NR, NY), dtype=float)
    irrV = np.zeros((NR, NY), dtype=float)

    for IN in range(0, NR):
        wdliv[IN, :] = np.sum(GCAMData['wdliv'][:, IN], axis=0)

        ls = np.where(GCAMData['irrV'][:, 0].astype(int) - 1 == IN)[0]
        irrV[IN, :] = sum(GCAMData['irrV'][ls, 3:])

    nonAG = GCAMData['rgn_wddom'] + GCAMData['rgn_wdelec'] + GCAMData['rgn_wdmfg'] + GCAMData['rgn_wdmining']
    AG = irrV + wdliv
    total = nonAG + AG
    GCAMOUT.rtotal = np.vstack([sum(total), total])
    GCAMOUT.rnonag = np.vstack([sum(nonAG), nonAG])
    GCAMOUT.rdom = np.vstack([sum(GCAMData['rgn_wddom']), GCAMData['rgn_wddom']])
    GCAMOUT.relec = np.vstack([sum(GCAMData['rgn_wdelec']), GCAMData['rgn_wdelec']])
    GCAMOUT.rmfg = np.vstack([sum(GCAMData['rgn_wdmfg']), GCAMData['rgn_wdmfg']])
    GCAMOUT.rmin = np.vstack([sum(GCAMData['rgn_wdmining']), GCAMData['rgn_wdmining']])
    GCAMOUT.rirr = np.vstack([sum(irrV), irrV])
    GCAMOUT.rliv = np.vstack([sum(wdliv), wdliv])

    values = []  # 'Year', 'Region ID', 'Region Name', 'GCAM Population (millions)' and all the category*group
    for j in range(0, NY):
        for i in range(0, NR + 1):

            DS = np.array(
                [OUT.rdom[i, j], OUT.relec[i, j], OUT.rmfg[i, j], OUT.rmin[i, j], OUT.rliv[i, j], OUT.rirr[i, j],
                 OUT.rnonag[i, j], OUT.rliv[i, j] + OUT.rirr[i, j], OUT.rtotal[i, j]])

            GCAM = np.array(
                [GCAMOUT.rdom[i, j], GCAMOUT.relec[i, j], GCAMOUT.rmfg[i, j], GCAMOUT.rmin[i, j], GCAMOUT.rliv[i, j],
                 GCAMOUT.rirr[i, j],
                 GCAMOUT.rnonag[i, j], GCAMOUT.rliv[i, j] + GCAMOUT.rirr[i, j], GCAMOUT.rtotal[i, j]])

            Diff = DS.tolist() + GCAM.tolist() + (DS - GCAM).tolist()

            if Years is not None:
                data = [Years[j], str(i), Regions[i]] + ["%.2f" % Population[i, j]] + ["%.3f" % x for x in Diff]
            else:
                data = ['Index ' + str(j), str(i), Regions[i]] + ["%.2f" % Population[i, j]] + ["%.3f" % x for x in
                                                                                                Diff]
            values.append(data)

    values = np.array(values)

    with open(OutputFilename, 'w') as outfile:
        np.savetxt(outfile, values, delimiter=',', header=headerline, fmt='%s', comments='')

    logging.info(f'------diagnostics information is saved to: {OutputFilename}')


def compare_downscaled_GCAMinput_irr_by_crops(PerformDiagnostics, NY, years, GCAMData, OUT):
    # These calculations will be performed ONLY if we are logging debug-level output.
    # Otherwise, we skip the output and the calculations
    if PerformDiagnostics != 1:
        return

    logging.info(
        '---Spatial Downscaling diagnostics (Irr by Crops): downscaled results vs. aggregated results from GCAM (Total Water, km3/yr)')

    NY = NY
    NCrops = OUT.crops_wdirr.shape[1]
    d_crops = ['biomass', 'corn', 'fibercrop', 'foddergrass', 'fodderherb',
               'misccrop', 'oilcrop', 'othergrain', 'palmfruit',
               'rice', 'root_tuber', 'sugarcrop', 'wheat']
    for y in range(NY):
        value = np.zeros((3,), dtype=float)
        # Irr Total For Each Year in log
        # Global Total [km3/yr] from downscaled results
        value[0] = sum(OUT.wdirr[:, y])
        # Global Total [km3/yr] from GCAM inputs
        value[1] = sum(GCAMData['irrV'][:, y + 3])
        value[2] = value[0] - value[1]
        if years:
            yrout = years[y]
        else:
            yrout = y + 1

        logging.info(f'Year {yrout:4d}: AllCrops  {value[0]:12.6f}  {value[1]:12.6f}  Diff= {value[2]:12.6f}')

        for c in range(NCrops):
            value = np.zeros((3,), dtype=float)

            # GLobal Total [km3/yr] from downscaled results
            value[0] = sum(OUT.crops_wdirr[:, c, y])

            # Global Total [km3/yr] from GCAM inputs
            index = np.where(GCAMData['irrV'][:, 2] == c + 1)[0]
            value[1] = sum(GCAMData['irrV'][index, y + 3])
            value[2] = value[0] - value[1]
            if years:
                yrout = years[y]
            else:
                yrout = y + 1

            logging.info(f'Year {yrout:4d}: {d_crops[c]:12} {value[0]:12.6f} {value[1]:12.6f} Diff= {value[2]:12.6f}')
