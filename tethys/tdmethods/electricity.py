import numpy as np
import pandas as pd
import xarray as xr
from tethys.datareader.regional import elec_sector_weights
from tethys.datareader.gridded import load_file, interp_helper
from tethys.datareader.maps import load_region_map


def temporal_distribution(years, resolution, hddfile, cddfile, regionfile, gcam_db, hddvar='hdd', cddvar='cdd',
                          bounds=None):
    """Temporal downscaling of water demand for electricity generation using algorithm from Voisin et al. (2013)"""

    # get weights of heating/cooling/other by location and time
    regions = load_region_map(regionfile, masks=True, target_resolution=resolution, bounds=bounds)
    weights = elec_sector_weights(gcam_db)
    weights = weights[(weights.region.isin(regions.region.data)) & (weights.year.isin(years))]
    weights = weights.set_index(['region', 'sector', 'year'])['value'].to_xarray().fillna(0).astype(np.float32)
    weights = weights.dot(regions.sel(region=weights.region), dims='region')
    weights = interp_helper(weights)

    hdd = load_file(hddfile, resolution, years, bounds=bounds, regrid_method='intensive', variables=[hddvar])[hddvar]
    cdd = load_file(cddfile, resolution, years, bounds=bounds, regrid_method='intensive', variables=[cddvar])[cddvar]

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

    # prevent 0/0
    hdd /= hdd.sum(dim='month').where(lambda x: x != 0, 1)
    cdd /= cdd.sum(dim='month').where(lambda x: x != 0, 1)

    distribution = xr.concat([hdd, cdd, xr.full_like(hdd, 1/12)],
                             dim=pd.Series(['Heating', 'Cooling', 'Other'], name='sector'))

    distribution = distribution.dot(weights, dims='sector')

    return distribution
