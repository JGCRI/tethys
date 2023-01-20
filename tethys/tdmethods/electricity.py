import os
import numpy as np
import pandas as pd
import xarray as xr
from tethys.datareader.regional import elec_sector_weights
from tethys.datareader.gridded import load_file, interp_helper


def temporal_distribution(model):
    """Temporal downscaling of water demand for electricity generation using algorithm from Voisin et al. (2013)"""
    years = range(model.years[0], model.years[-1] + 1)
    hdd = load_file(model.temporal_files['hdd'], model.resolution, years, regrid_method='intensive')['hdd']
    cdd = load_file(model.temporal_files['cdd'], model.resolution, years, regrid_method='intensive')['cdd']

    weights = elec_sector_weights(os.path.join(model.root, model.gcam_db))
    weights = weights[(weights.region.isin(model.inputs.region[model.inputs.sector == 'Electricity'])) &
                      (weights.region.isin(model.region_masks.region.data)) &
                      (weights.year.isin(model.years))].set_index(['region', 'sector', 'year']
                                                                  )['value'].to_xarray().fillna(0).astype(np.float32)
    weights = interp_helper(weights)

    region_masks = model.region_masks.sel(region=weights.region)

    # this formula is annoying to implement because of the hdd/cdd thresholds and reallocation of weights
    hdd_sums = hdd.sum(dim='month')
    cdd_sums = cdd.sum(dim='month')

    # when hdd under threshold but cdd above threshold, cooling percent is added to heating signal
    hdd = xr.where((hdd_sums < 650) & (cdd_sums >= 450), cdd, hdd)
    # when cdd under threshold but hdd above threshold, heating percent is added to cooling signal
    cdd = xr.where((cdd_sums < 450) & (hdd_sums >= 650), hdd, cdd)
    # when neither are above threshold, both are reallocated to other category, and demand does not depend hdd or cdd
    hdd = xr.where((hdd_sums < 650) & (cdd_sums < 450), 1 / 12, hdd)
    cdd = xr.where((hdd_sums < 650) & (cdd_sums < 450), 1 / 12, cdd)

    # redo sums based on reallocation
    hdd_sums = hdd.sum(dim='month')
    cdd_sums = cdd.sum(dim='month')
    # prevent 0/0
    hdd_sums = xr.where(hdd_sums != 0, hdd_sums, 1)
    cdd_sums = xr.where(cdd_sums != 0, cdd_sums, 1)
    hdd /= hdd_sums
    cdd /= cdd_sums

    distribution = xr.concat([hdd, cdd, xr.full_like(hdd, 1/12)],
                             dim=pd.Series(['Heating', 'Cooling', 'Other'], name='sector'))

    distribution = distribution.where(region_masks, 0)
    distribution = distribution.dot(weights, dims=('sector', 'region'))

    return distribution
