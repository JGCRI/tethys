"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import numpy as np
import pandas as pd
import gcamreader
import xarray as xr
import sparse


def downscale(df, proxies, regions):
    """Actual downscaling here

    :param df: pandas dataframe of region scale demand inputs, with columns 'region', 'sector', 'year', 'value'
    :param proxies: xarray DataArray giving distribution of demand, with dimensions 'sector', 'year', 'lat', 'lon'
    :param regions: xarray DataArray with labeled regions, dimensions 'lat', 'lon', and attribute names
    :return: out: xarray DataArray with dimensions 'sector', 'year', 'lat', 'lon'
    """
    regionids = pd.Series(regions.names, name='regionid').astype(int).sort_index().rename_axis('region').to_xarray()

    index = pd.MultiIndex.from_product([regionids.region.to_series(), proxies.sector.to_series(), proxies.year.to_series()])
    input_data = df.set_index(['region', 'sector', 'year']).reindex(index, fill_value=0)['value'].to_xarray()

    # groupby was slow so we do this hack with sparse arrays
    # multiply the proxy by a bool array region mask to group, then operate on each layer
    groups = regions == regionids
    out = proxies * groups

    sums = out.sum(dim=('lat', 'lon'))
    sums.data.fill_value = 1  # avoid 0/0

    out *= input_data / sums  # demand_cell = demand_region * (proxy_cell / proxy_region), but calculate efficiently

    out = out.sum(dim='region')

    return out


def rename_sector(x):
    """Helper for converting full GCAM sector names to Tethys demand categories"""
    if x in ('domestic water', 'municipal water') or x.startswith('water_td_dom_'):
        return 'Domestic'
    elif x.startswith('elec') or x.startswith('water_td_elec_'):
        return 'Electricity'
    elif x.startswith('industr') or x.startswith('water_td_ind_'):
        return 'Manufacturing'
    elif x in ('regional coal', 'nuclearFuelGenIII', 'regional natural gas', 'unconventional oil production', 'regional oil', 'nuclearFuelGenII') or x.startswith('water_td_pri_'):
        return 'Mining'
    elif x.startswith('water_td_irr_'):
        return 'Irrigation'
    elif x.startswith('water_td_an_'):
        return 'Livestock'
    return x


def load_region_data(df=None, csv=None, query=None, query_file=None, query_title=None, conn=None, gcam_db_path=None, gcam_db_file=None, basin_column=None):
    if csv is not None:
        df = pd.read_csv(csv)
    elif df is None:
        if conn is None:
            conn = gcamreader.LocalDBConn(gcam_db_path, gcam_db_file, suppress_gabble=False)
        if query is None:
            query = next(i for i in gcamreader.parse_batch_query(query_file) if i.title == query_title)
        df = conn.runQuery(query)
    df['sector'] = df['sector'].map(rename_sector)
    if basin_column is not None:
        df['region'] += df[basin_column].apply(lambda x: x.strip('_W').strip('_C').split('_')[-1])
    df.columns = df.columns.str.lower()
    df = df.groupby(['region', 'sector', 'year'])[['value']].sum().reset_index()

    return df


def load_regionmap(mapfile, namefile=None, target_resolution=None, nodata=None, flip_lat=False):
    """ Load region map

    :param mapfile: path to map file
    :param namefile: optional path to csv with region names
    :param target_resolution: resolution to coerce map to. If None (default), use base resolution
    """

    da = xr.load_dataarray(mapfile, engine='rasterio')

    if nodata is not None:
        da.data[da.data == nodata] = 0

    da = da.astype(np.uint16)

    # coerce names
    if 'y' in da.coords:
        da = da.rename(y='lat')
    if 'x' in da.coords:
        da = da.rename(x='lon')

    # set dimension order
    da = da.transpose(..., 'lat', 'lon')

    # handle flipped latitudes
    if flip_lat:
        da['lat'] = -da.lat

    # drop band
    if 'band' in da.coords:
        da = da.squeeze('band').drop_vars('band')

    if target_resolution is not None:
        lcm = np.lcm(da.lat.size, round(180 / target_resolution))
        r = lcm // da.lat.size
        s = lcm // round(180 / target_resolution)

        da = da.isel(lon=np.arange(da.lon.size).repeat(r)).coarsen(lon=s).max()
        da = da.isel(lat=np.arange(da.lat.size).repeat(r)).coarsen(lat=s).max()
    else:
        target_resolution = 180 / da.lat.size

    offset = target_resolution / 2
    da['lat'] = np.linspace(90 - offset, -90 + offset, round(180 / target_resolution))
    da['lon'] = np.linspace(-180 + offset, 180 - offset, round(360 / target_resolution))

    if namefile is not None:
        df = pd.read_csv(namefile)
        da = da.assign_attrs(names=dict(zip(df.iloc[:, 0], df.iloc[:, 1].astype(str))))
    elif 'names' in da.attrs:
        # ew
        temp = da.attrs['names'].replace('{', '').replace('}', '').replace("'", '')
        da.attrs['names'] = dict(i.split(': ') for i in temp.split(', '))

    da = da.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
    da.name = 'regionid'

    da.data = sparse.COO(da.data)


    return da


def _preprocess(ds, catalog, target_resolution):
    """ add missing metadata, filter

    :type ds: xarray.Dataset
    """
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

    # regridding
    source_resolution = (ds.lat.data[0] - ds.lat.data[-1])/(ds.lat.size - 1)

    if 'cell_area_share' in flags:
        areas = np.cos(np.radians(ds.lat)) * (111.32 * 110.57) * source_resolution * source_resolution
        ds = ds * areas

    lat_offset = round((90 - ds.lat.data[0]) / source_resolution - 0.5)
    lon_offset = round((ds.lon.data[0] + 180) / source_resolution - 0.5)

    ds = ds.pad(lat=(lat_offset, round(180 / source_resolution) - lat_offset - ds.lat.size),
                lon=(lon_offset, round(360 / source_resolution) - lon_offset - ds.lon.size),
                constant_values=0)

    target_lat_size = round(180 / target_resolution)

    lcm = np.lcm(ds.lat.size, target_lat_size)
    r = lcm // ds.lat.size
    s = lcm // target_lat_size

    ds = ds.isel(lon=np.arange(ds.lon.size).repeat(r)).coarsen(lon=s).sum()
    ds = ds.isel(lat=np.arange(ds.lat.size).repeat(r)).coarsen(lat=s).sum()
    ds = ds / (r * r)  # correct for repetition

    offset = target_resolution / 2
    ds['lat'] = np.linspace(90 - offset, -90 + offset, round(180 / target_resolution))
    ds['lon'] = np.linspace(-180 + offset, 180 - offset, round(360 / target_resolution))

    for _, da in ds.items():
        da.data = sparse.COO(da.data.astype(np.float32))

    return ds


def load_proxies(catalog, target_resolution, target_years):

    print('Loading Proxy Data')
    dataarrays = [da for i in catalog for da in _preprocess(xr.open_dataset(i), catalog, target_resolution).values()]

    print('Interpolating Proxies')
    ds = xr.merge(interp_sparse(xr.concat([da for da in dataarrays if da.name == variable], 'year'), target_years)
                  for variable in set(da.name for da in dataarrays))

    return ds


def interp_sparse(da, target_years):
    """Linearly interpolate da to target_years
    scipy interp1d fails on sparse arrays so implement here by taking linear combinations of neighboring years

    :param da: xarray DataArray with source years
    :param target_years: list of target years to interpolate to
    :return: da linearly interpolated to target_years
    """

    source_years = da.year.data
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

    # convert weights and indices to a sparse backed DataArray
    interpolator = xr.DataArray(data=sparse.COO(np.block([[np.arange(target_years.size), np.arange(target_years.size)],
                                                          [lower_idx, upper_idx]]),
                                                np.concatenate((lower_weights, upper_weights))),
                                coords=dict(target_year=target_years, year=source_years),
                                name=da.name)

    # multiply by interpolator, sum by years, rename
    da = interpolator * da
    da = da.sum(dim='year').rename(target_year='year')

    return da
