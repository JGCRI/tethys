import numpy as np
import pandas as pd
import xarray as xr

from tethys.region_map import region_masks
from tethys.spatial_proxies import pad_global, regrid


def load_monthly_data(filename, target_resolution, years=None, method='intensive'):

    da = xr.open_dataarray(filename, chunks=dict(year=1, month=1)).astype(np.float32)

    if years is not None and 'year' in da.coords:
        da = da.sel(year=years, method='nearest').chunk(chunks=dict(year=1))
        da['year'] = years

    # handle flipped latitudes
    if da.lat.data[0] < da.lat.data[-1]:
        da = da.isel(lat=slice(None, None, -1))

    da = da.fillna(0)

    da = pad_global(da)
    da = regrid(da, target_resolution, method)

    da = da.chunk(chunks=dict(lat=360, lon=360))
    if 'month' in da.coords:
        da = da.chunk(chunks=dict(month=12))

    return da


def monthly_distribution_domestic(tas, amplitude):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    out = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return out


def monthly_distribution_electricty(hdd, cdd, weights, regionmasks):
    """Temporal downscaling of water demand for electricity generation using algorithm from Voisin et al. (2013)"""

    hdd_sums = hdd.sum(dim='month')
    cdd_sums = cdd.sum(dim='month')
    hdd = xr.where((hdd_sums < 650) & (cdd_sums >= 450), cdd, hdd)
    cdd = xr.where((cdd_sums < 450) & (hdd_sums >= 650), hdd, cdd)
    hdd = xr.where((hdd_sums < 650) & (cdd_sums < 450), 1 / 12, hdd)
    cdd = xr.where((hdd_sums < 650) & (cdd_sums < 450), 1 / 12, cdd)
    hdd_sums = hdd.sum(dim='month')
    cdd_sums = cdd.sum(dim='month')
    hdd_sums = xr.where(hdd_sums != 0, hdd_sums, 1)
    cdd_sums = xr.where(cdd_sums != 0, cdd_sums, 1)
    hdd /= hdd_sums
    cdd /= cdd_sums

    out = xr.concat([hdd, cdd, xr.full_like(hdd, 1/12)],
                    dim=pd.Series(['Heating', 'Cooling', 'Other'], name='sector'))

    out = out.where(regionmasks, 0)
    out = out.dot(weights, dims=('sector', 'region'))

    return out


def monthly_distribution_irrigation(irr, regionmasks):
    """Temporal downscaling of irrigation water demand"""

    irr_grouped = irr.where(regionmasks, 0)
    month_sums = irr_grouped.sum(dim=('lat', 'lon'))
    year_sums = month_sums.sum(dim='month').where(lambda x: x != 0, 1)  # avoid 0/0

    out = regionmasks.dot(month_sums / year_sums, dims='region')

    return out
