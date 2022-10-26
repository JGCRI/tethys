"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import numpy as np
import tifffile as tf
import netCDF4 as nc4


def load_tiff(filename):
    with tf.TiffFile(filename) as tif:
        temp = tif.asarray()
        nodata = tif.pages.first.nodata
        metadata = tif.geotiff_metadata

    temp[temp == nodata] = 0

    # place in global grid
    resolution = metadata['ModelPixelScale'][0]  # assuming lat and lon same resolution
    y_offset = round((90 - metadata['ModelTiepoint'][4]) / resolution)
    x_offset = round((180 + metadata['ModelTiepoint'][3]) / resolution)

    out = np.zeros((round(180 / resolution), round(360 / resolution)))
    out[y_offset:y_offset + temp.shape[0], x_offset:x_offset + temp.shape[1]] = temp

    return out


def load_nc(filename, name):
    grp = nc4.Dataset(filename)
    grp.set_auto_mask(False)

    if name in grp.variables.keys():
        var = grp.variables[name]
    else:  # check short name (for earlier versions of Demeter outputs)
        var = grp.get_variables_by_attributes(short_name=name)[0]

    temp = var[:].copy()
    # handle different names

    if 'lat' in grp.variables.keys():
        lat = grp.variables['lat'][:].copy()
        lon = grp.variables['lon'][:].copy()
    else:
        lat = grp.variables['latitude'][:].copy()
        lon = grp.variables['longitude'][:].copy()

    # handle swapped lat-lon dimension order
    if var.dimensions[0].lower().startswith('lon'):
        temp = temp.T

    grp.close()

    # handle ascending lat
    if lat[0] < lat[1]:
        lat = np.flip(lat, axis=0)
        temp = np.flip(temp, axis=0)

    # replace nans
    temp[np.isnan(temp)] = 0

    # remove indices of repeated latitudes
    diffs = lat[:-1] - lat[1:]
    avg_diff = (lat[0] - lat[-1]) / (len(lat) - 1)
    valid = np.where(diffs > 0.5 * avg_diff)[0]
    temp = temp[valid]
    lat = lat[valid]

    # place in global grid
    resolution = (lat[0] - lat[-1])/(len(lat) - 1)  # assuming lat and lon same resolution
    y_offset = round((90 - lat[0]) / resolution - 0.5)
    x_offset = round((180 + lon[0]) / resolution - 0.5)

    out = np.zeros((round(180 / resolution), round(360 / resolution)))
    out[y_offset:y_offset + temp.shape[0], x_offset:x_offset + temp.shape[1]] = temp

    return out


def from_monthly_npz(filename, variable, firstyear, lastyear, resolution, mask):
    file = np.load(filename)
    years = file['years']
    data = file[variable]
    _, _, nlat, nlon = data.shape
    temp = np.zeros((lastyear - firstyear + 1, 12, nlat, nlon), dtype=np.float32)
    start = max(years[0], firstyear)
    end = min(years[-1], lastyear)
    temp[:start - firstyear] = data[start - years[0]]
    temp[start - firstyear:end - firstyear] = data[start - years[0]:end - years[0]]
    temp[end - firstyear:] = data[end - years[0]]

    out = np.zeros((lastyear - firstyear + 1, 12, np.count_nonzero(mask)))
    for i in range(lastyear - firstyear + 1):
        for j in range(12):
            out[i, j] = regrid(temp[i, j], resolution, method='intensive')[mask]

    return out


def regrid(array, out_resolution, in_resolution=None, method='extensive'):
    """ quick regridding of 2d input array to an output resolution with reasonable lcm (e.g., 1/12 to 1/8 degrees)

    :param array: 2d array to be regridded
    :param out_resolution: desired output resolution
    :param in_resolution: resolution of array. if None (default), will be assumed to be 180 / array.shape[0]
    :param method: choice of 'extensive' (preserves sum, default), 'intensive' (average), or 'thematic' (categories)
    :return: array regridded to output resolution
    """

    iny, inx = array.shape

    if in_resolution is None:
        in_resolution = 180 / iny

    scale = in_resolution / out_resolution
    outy, outx = round(iny * scale), round(inx * scale)

    lcm = np.lcm(iny, outy)
    r = lcm // iny
    s = lcm // outy

    if method == 'thematic':  # take center
        temp = array.repeat(r, axis=1).reshape(iny, outx, s)[:, :, s//2]
        out = temp.repeat(r, axis=0).reshape(outy, s, outx)[:, s//2, :]
        return out

    else:
        temp = array.repeat(r, axis=1).reshape(iny, outx, s).sum(axis=2)
        out = temp.repeat(r, axis=0).reshape(outy, s, outx).sum(axis=1)

        if method == 'extensive':  # divide by repetitions to preserve sum
            return out / (r * r)

        elif method == 'intensive':  # take average within the output cells
            return out / (s * s)

        else:
            print('invalid method')
