import numpy as np
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
