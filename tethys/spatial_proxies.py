import numpy as np
import xarray as xr


def load_proxies(catalog, target_resolution, target_years):

    print('Loading Proxy Data')
    dataarrays = [da for i in catalog for da in _preprocess(xr.open_dataset(i, chunks='auto'), catalog, target_resolution).values()]

    print('Interpolating Proxies')
    ds = xr.merge(interp_sparse(xr.concat([da for da in dataarrays if da.name == variable], 'year'), target_years)
                  for variable in set(da.name for da in dataarrays))

    return ds


def _preprocess(ds, catalog, target_resolution):
    """ add missing metadata, filter

    :type ds: xarray.Dataset
    """

    # TODO: break out steps into functions as sensible (for testing)

    # get details from files catalog
    filename = ds.encoding['source']
    variables = sorted(catalog[filename]['variables'])
    years = sorted(catalog[filename]['years'])
    flags = catalog[filename]['flags']

    print(f'Loading {filename}\n\tVariables: {variables}\n\tYears: {years}\n')

    # handle tif (can only handle single band single variable single year currently)
    if 'band' in ds.coords:
        ds = ds.squeeze('band').drop_vars('band')
        ds = ds.rename(y='lat', x='lon', band_data=variables[0])

    if 'short_name_as_name' in flags:
        ds = ds.rename({i: ds.get(i).attrs['short_name'] for i in ds.data_vars})

    ds = ds[variables]  # filter to desired variables

    # pad year dimension if not existent
    if 'year' not in ds.coords:
        ds = ds.expand_dims(year=len(years)).assign_coords(year=('year', years))

    ds = ds.isel(year=ds.year.isin(years))  # filter to desired years

    # coerce names
    if 'latitude' in ds.coords:
        ds = ds.rename(latitude='lat')
    if 'longitude' in ds.coords:
        ds = ds.rename(longitude='lon')

    # set dimension order
    ds = ds.transpose(..., 'lat', 'lon')

    # handle flipped latitudes
    if ds.lat.data[0] < ds.lat.data[-1]:
        ds = ds.isel(lat=slice(None, None, -1))

    # drop repeated latitudes
    ds['lat'] = ds.lat.round(10)  # 10 decimal-place tolerance
    ds = ds.drop_duplicates(dim='lat')

    ds = ds.fillna(0)
    ds = ds.astype(np.float32)

    if 'cell_area_share' in flags:
        ds = percent_to_area(ds)

    ds = pad_global(ds)
    ds = regrid(ds, target_resolution, method='extensive')

    ds = ds.chunk(chunks=dict(lat=1440, lon=1440))

    return ds


def percent_to_area(ds):
    source_resolution = (ds.lat.data[0] - ds.lat.data[-1]) / (ds.lat.size - 1)
    cell_areas = xr.DataArray(np.cos(np.radians(ds.lat)) * (111.32 * 110.57) * source_resolution * source_resolution,
                              coords=dict(lat=ds.lat))
    ds = ds * cell_areas
    return ds


def pad_global(ds):
    # pad inputs to global resolution

    source_resolution = (ds.lat.data[0] - ds.lat.data[-1]) / (ds.lat.size - 1)

    lat_offset = round((90 - ds.lat.data[0]) / source_resolution - 0.5)
    lon_offset = round((ds.lon.data[0] + 180) / source_resolution - 0.5)

    ds = ds.pad(lat=(lat_offset, round(180 / source_resolution) - lat_offset - ds.lat.size),
                lon=(lon_offset, round(360 / source_resolution) - lon_offset - ds.lon.size),
                constant_values=0)

    return ds


def regrid(ds, target_resolution, method='extensive'):
    """

    :param ds: xarray Dataset or DataArray
    :param target_resolution: target resolution in degrees
    :param method: choice of 'extensive' (preserves sums, default), 'intensive' (take average), or 'label' (for maps)
    :return:
    """

    target_lat_size = round(180 / target_resolution)

    lcm = np.lcm(ds.lat.size, target_lat_size)
    r = lcm // ds.lat.size
    s = lcm // target_lat_size

    ds = ds.chunk(chunks=dict(lat=int(360*s/r), lon=int(720*s/r)))

    if method == 'label':
        ds = ds.isel(lon=np.arange(ds.lon.size).repeat(r)).coarsen(lon=s).max()
        ds = ds.isel(lat=np.arange(ds.lat.size).repeat(r)).coarsen(lat=s).max()
    else:
        ds = ds.isel(lon=np.arange(ds.lon.size).repeat(r)).coarsen(lon=s).sum()
        ds = ds.isel(lat=np.arange(ds.lat.size).repeat(r)).coarsen(lat=s).sum()
        if method == 'extensive':
            ds = ds / (r * r)  # correct for repetition
        elif method == 'intensive':
            ds = ds / (s * s)  # take average

    # set coordinates
    offset = target_resolution / 2
    ds['lat'] = np.linspace(90 - offset, -90 + offset, round(180 / target_resolution))
    ds['lon'] = np.linspace(-180 + offset, 180 - offset, round(360 / target_resolution))

    return ds


def interp_sparse(da, target_years=None):
    """Linearly interpolate da to target_years
    scipy interp1d fails on sparse arrays so implement here by taking linear combinations of neighboring years

    :param da: xarray DataArray with source years
    :param target_years: list of target years to interpolate to. If None, then interpolate to annual
    :return: da linearly interpolated to target_years
    """

    source_years = da.year.data
    if target_years is None:
        target_years = range(source_years[0], source_years[-1] + 1)
    target_years = np.asarray(target_years)

    # calculate indices of nearest data years above and below (or equal to) target years
    # target years outside the available data are assigned the nearest (end point)
    lower_idx = np.maximum(0, np.searchsorted(source_years, target_years, 'right') - 1)
    upper_idx = np.minimum(np.searchsorted(source_years, target_years, 'left'), len(source_years) - 1)

    # calculate weights of the upper and lower indices
    # When the same, lower is given 1 and upper is 0
    lower_weights = np.divide(source_years[upper_idx] - target_years, source_years[upper_idx] - source_years[lower_idx],
                              where=upper_idx != lower_idx, out=np.ones_like(target_years, dtype=np.float32))
    upper_weights = np.divide(target_years - source_years[lower_idx], source_years[upper_idx] - source_years[lower_idx],
                              where=upper_idx != lower_idx, out=np.zeros_like(target_years, dtype=np.float32))

    lower = da.isel(year=lower_idx).assign_coords(year=target_years)
    upper = da.isel(year=upper_idx).assign_coords(year=target_years)
    out = lower * xr.DataArray(lower_weights, dict(year=target_years)) + upper * xr.DataArray(upper_weights, dict(year=target_years))

    out = out.rename(da.name).chunk(chunks=dict(year=1))

    return out
