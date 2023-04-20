import numpy as np
import xarray as xr


def load_file(filename, target_resolution, years, variables=None, flags=None, regrid_method='extensive'):
    """Prepare a dataset from single file to be merged into a dataset of all proxies

    handles many oddities found in proxies

    :param filename: name of file
    :param target_resolution: resolution in degrees to regrid to
    :param years: years to extract from the file
    :param variables: variables to extract from the file
    :param flags: list potentially containing 'cell_area_share' or 'short_name_as_name'
    :param regrid_method: passed along to regrid
    :return: preprocessed data set
    """

    flags = [] if flags is None else flags

    ds = xr.open_dataset(filename, chunks='auto')

    # handle tif (can only handle single band single variable single year currently)
    if 'band' in ds.coords:
        ds = ds.squeeze('band').drop_vars('band')
        ds = ds.rename(y='lat', x='lon', band_data=variables[0])

    # handle an option that lets us use netcdf short_name instead of name (handle "PFT0")
    if 'short_name_as_name' in flags:
        ds = ds.rename({i: ds.get(i).attrs['short_name'] for i in ds.data_vars})
    if 'long_name_as_name' in flags:
        ds = ds.rename({i: ds.get(i).attrs['long_name'] for i in ds.data_vars})

    # filter to desired variables
    if variables is not None:
        ds = ds[variables]

    # create a year dimension if missing, with the years reported for this file in the catalog
    if 'year' not in ds.coords:
        ds = ds.expand_dims(year=len(years))
    else:
        ds = ds.sel(year=years, method='nearest')  # nearest used for temporal files
    ds['year'] = years

    # do the year filtering
    if years is not None and 'year' in ds.coords:
        ds = ds.sel(year=years, method='nearest').chunk(chunks=dict(year=1))
        ds['year'] = years

    # numeric stuff
    ds = ds.fillna(0).astype(np.float32)

    # rename to lat lon and handle some wacky stuff
    ds = clean_spatial_dims(ds)

    if 'cell_area_share' in flags:
        ds = percent_to_area(ds)

    # spatial aligning
    ds = pad_global(ds)
    ds = regrid(ds, target_resolution, method=regrid_method)

    ds = ds.chunk(chunks=dict(lat=-1, lon=-1))
    if 'month' in ds.coords:
        ds = ds.chunk(chunks=dict(month=12))

    return ds


def clean_spatial_dims(ds):
    # coerce spatial dimension names
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

    return ds


def percent_to_area(ds):
    """Convert landcover dataset from cell proportion to area

    :param ds: xarray Dataset where values represent proportion of grid cell
    :return: xarray Dataset where values represent area in square kilometers
    """

    source_resolution = (ds.lat.data[0] - ds.lat.data[-1]) / (ds.lat.size - 1)

    # formula for total grid cell area (km^2) based on latitude and cell resolution
    cell_areas = xr.DataArray(np.cos(np.radians(ds.lat)) * (111.32 * 110.57) * source_resolution * source_resolution,
                              coords=dict(lat=ds.lat)).astype(np.float32)

    return ds * cell_areas


def set_global_coords(ds, resolution):
    offset = resolution / 2
    ds['lat'] = np.linspace(90 - offset, -90 + offset, round(180 / resolution))
    ds['lon'] = np.linspace(-180 + offset, 180 - offset, round(360 / resolution))

    return ds


def pad_global(ds):
    """pad inputs to global resolution

    :param ds: xarray Dataset
    :return: xarray Dataset with global extent
    """

    source_resolution = (ds.lat.data[0] - ds.lat.data[-1]) / (ds.lat.size - 1)

    lat_offset = round((90 - ds.lat.data[0]) / source_resolution - 0.5)
    lon_offset = round((ds.lon.data[0] + 180) / source_resolution - 0.5)

    ds = ds.pad(lat=(lat_offset, round(180 / source_resolution) - lat_offset - ds.lat.size),
                lon=(lon_offset, round(360 / source_resolution) - lon_offset - ds.lon.size),
                constant_values=0)

    ds = set_global_coords(ds, source_resolution)

    return ds


def regrid(ds, target_resolution, method='extensive'):
    """Simple regridding algorithm

    :param ds: xarray Dataset or DataArray, needs lat and lon and global extent
    :param target_resolution: target resolution in degrees
    :param method: choice of 'extensive' (preserves sums, default), 'intensive' (take average), or 'label' (for maps)
    :return: ds regridded to target_resolution
    """

    target_lat_size = round(180 / target_resolution)

    lcm = np.lcm(ds.lat.size, target_lat_size)
    r = lcm // ds.lat.size
    s = lcm // target_lat_size

    if method == 'label':
        ds = ds.isel(lon=np.arange(ds.lon.size).repeat(r)).coarsen(lon=s).max()
        ds = ds.isel(lat=np.arange(ds.lat.size).repeat(r)).coarsen(lat=s).max()
    else:
        ds = ds.isel(lon=np.arange(ds.lon.size).repeat(r)).coarsen(lon=s).sum()
        ds = ds.isel(lat=np.arange(ds.lat.size).repeat(r)).coarsen(lat=s).sum()
        if method == 'extensive':
            ds = ds / (r * r)  # preserve original sum
        elif method == 'intensive':
            ds = ds / (s * s)  # take average

    # set coordinates
    ds = set_global_coords(ds, target_resolution)

    return ds


def interp_helper(da, target_years=None):
    """Linearly interpolate da to target_years
    more control over chunks, works with sparse

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
    out = lower * xr.DataArray(lower_weights, dict(year=target_years)) + \
        upper * xr.DataArray(upper_weights, dict(year=target_years))

    out = out.rename(da.name)

    return out
