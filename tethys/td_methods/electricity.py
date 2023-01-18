import os
import numpy as np
import pandas as pd
import xarray as xr
from tethys.temporal_downscaling import load_monthly_data
from tethys.region_data import elec_sector_weights
from tethys.spatial_proxies import interp_helper


def monthly_distribution(self):
    """Temporal downscaling of water demand for electricity generation using algorithm from Voisin et al. (2013)"""

    hdd = load_monthly_data(self.temporal_files['hdd'], self.resolution, range(self.years[0], self.years[-1] + 1))
    cdd = load_monthly_data(self.temporal_files['cdd'], self.resolution, range(self.years[0], self.years[-1] + 1))

    weights = elec_sector_weights(os.path.join(self.root, self.gcam_db))
    weights = weights[(weights.region.isin(self.inputs.region[self.inputs.sector == 'Electricity'])) &
                      (weights.region.isin(self.region_masks.region.data)) &
                      (weights.year.isin(self.years))].set_index(
        ['region', 'sector', 'year'])['value'].to_xarray().fillna(0).astype(np.float32)
    weights = interp_helper(weights)

    region_masks = self.region_masks.sel(region=weights.region)

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

    out = xr.concat([hdd, cdd, xr.full_like(hdd, 1/12)], dim=pd.Series(['Heating', 'Cooling', 'Other'], name='sector'))

    out = out.where(region_masks, 0)
    out = out.dot(weights, dims=('sector', 'region'))

    return out
