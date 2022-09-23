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

    out = np.zeros((int(180 / resolution), int(360 / resolution)))
    out[y_offset:y_offset + temp.shape[0], x_offset:x_offset + temp.shape[1]] = temp

    return out


def load_nc(filename, short_name):
    grp = nc4.Dataset(filename, format='NETCDF3_CLASSIC')
    grp.set_auto_mask(False)
    var = grp.get_variables_by_attributes(short_name=short_name)[0]
    temp = var[:].copy()
    temp[np.isnan(temp)] = 0
    if 'lon' in var.dimensions[0]:
        temp = temp.T
    grp.close()
    return temp


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
            out[i, j] = regrid(temp[i, j], resolution, preserve_sum=False)[mask]

    return out


def regrid(array, resolution, preserve_sum=True, thematic=False):
    # quick regridding of 2d input array to a close output resolution with reasonable lcm (e.g., 5 to 7.5 arcmins)
    # does not adjust weights for cell areas, but probably shouldn't be used for cases where that would matter
    iny, inx = array.shape
    outy, outx = int(180 / resolution), int(360 / resolution)
    lcm = np.lcm(iny, outy)
    r = lcm // iny
    s = lcm // outy

    if thematic:  # take center
        temp = array.repeat(r, axis=1).reshape(iny, outx, s)[:, :, s//2]
        out = temp.repeat(r, axis=0).reshape(outy, s, outx)[:, s//2, :]
        return out
    else:
        temp = array.repeat(r, axis=1).reshape(iny, outx, s).sum(axis=2)
        out = temp.repeat(r, axis=0).reshape(outy, s, outx).sum(axis=1)

        if preserve_sum:
            return out / (r * r)
        else:
            return out / (s * s)
