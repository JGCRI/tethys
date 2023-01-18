import numpy as np
import pandas as pd
import xarray as xr

from tethys.spatial_data import regrid


def load_region_map(mapfile, masks=False, namefile=None, target_resolution=None, nodata=None, flip_lat=False):
    """ Load region map.

    :param mapfile: path to map file
    :param masks: bool whether to convert categorical map to layer of region masks
    :param namefile: optional path to csv with region names
    :param target_resolution: resolution to coerce map to. If None (default), use base resolution
    :param nodata: nodata value (like 9999), will be replaced with 0
    :param flip_lat: bool, whether the map is "upside down"
    """

    da = xr.load_dataarray(mapfile, engine='rasterio', chunks='auto')

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
        da = regrid(da, target_resolution, method='label')
        da = da.chunk(chunks=dict(lat=-1, lon=-1))

    # use region names provided in CSV namefile, otherwise check metadata for a names dict
    if namefile is not None:
        df = pd.read_csv(namefile)
        da = da.assign_attrs(names=dict(zip(df.iloc[:, 0], df.iloc[:, 1].astype(str))))
    elif 'names' in da.attrs:
        # ew
        temp = da.attrs['names'].replace('{', '').replace('}', '').replace("'", '')
        da.attrs['names'] = dict(i.split(': ') for i in temp.split(', '))

    da = da.rio.set_spatial_dims(x_dim='lon', y_dim='lat')
    da.name = 'regionid'

    if masks:
        names = pd.Series(da.names, name='regionid').astype(int).sort_index().rename_axis('region')
        da = da == names.to_xarray().chunk(chunks=dict(region=1))

    return da


def intersection(da1, da2):
    """Convenience function for producing a map of intersections"""
    key, array = np.unique(np.stack((np.asarray(da1), np.asarray(da2))).reshape(2, -1), axis=1, return_inverse=True)

    out = da1.copy(data=array.reshape(da1.shape).astype(np.uint16))

    df = pd.DataFrame(key.T)
    df[0] = df[0].map({int(v): k for k, v in da1.names.items()})
    df[1] = df[1].map({int(v): k for k, v in da2.names.items()})
    names = (df[0] + '_' + df[1]).to_dict()
    out.attrs['names'] = {v: str(k) for k, v in names.items() if k != 0}

    return out
