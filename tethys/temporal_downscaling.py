import numpy as np
import pandas as pd
import xarray as xr

from tethys.spatial_proxies import pad_global, regrid


def load_monthly_data(filename, target_resolution, years=None, method='intensive'):
    """Load and prepare files used in

    :param filename: file name
    :param target_resolution: resolution to regrid to (in degrees)
    :param years: years to select
    :param method: regridding method (see regrid function)
    :return:
    """

    da = xr.open_dataarray(filename, chunks=dict(year=1, month=1))

    # do the year filtering
    if years is not None and 'year' in da.coords:
        da = da.sel(year=years, method='nearest').chunk(chunks=dict(year=1))
        da['year'] = years

    # handle flipped latitudes
    if da.lat.data[0] < da.lat.data[-1]:
        da = da.isel(lat=slice(None, None, -1))

    # numeric stuff
    da = da.fillna(0)
    da = da.astype(np.float32)

    # spatial stuff
    da = pad_global(da)
    da = regrid(da, target_resolution, method)

    # chunking
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
