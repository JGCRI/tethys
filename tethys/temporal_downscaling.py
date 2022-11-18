import numpy as np
import pandas as pd
import xarray as xr
import sparse

from tethys.spatial_proxies import pad_global, regrid


def load_monthly_data(filename, target_resolution, years=None, method='intensive'):

    da = xr.open_dataarray(filename, chunks=dict(year=1, month=12, lat=360, lon=360)).astype(np.float32)

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

    #da.data = da.data.map_blocks(sparse.COO)

    return da


def monthly_distribution_domestic(tas, amplitude):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    out = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return out


def monthly_distribution_electricty(hdd, cdd, weights, regions):
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

    regionids = pd.Series(regions.names, name='regionid').astype(int).sort_index().rename_axis('region').to_xarray()

    index = pd.MultiIndex.from_product([regionids.region.to_series(),
                                        out.sector.to_series(),
                                        out.year.to_series()])
    input_data = weights.set_index(['region', 'sector', 'year']).reindex(index, fill_value=0)['value'].to_xarray()

    groups = regions == regionids
    out = out * groups

    out = out * input_data
    out = out.sum(dim=('sector', 'region'))

    return out


def monthly_distribution_irrigation(irr, regions):
    """Temporal downscaling of irrigation water demand"""

    regionids = pd.Series(regions.names, name='regionid').astype(int).sort_index().rename_axis('region').to_xarray()
    groups = regions == regionids

    out = irr * groups
    month_share_by_region = out.sum(dim=('lat', 'lon')) / out.sum(dim=('month', 'lat', 'lon'))
    out = groups * month_share_by_region
    out = out.sum(dim='region')

    return out
