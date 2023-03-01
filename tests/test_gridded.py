import unittest

import os
import xarray as xr

import tethys.datareader.gridded as gridded


class TestGridded(unittest.TestCase):

    COMP_CLEAN_SPATIAL_DIMS = xr.DataArray(data=[[0, 0, 0, 0, 0, 0],
                                                 [0, 0, 0, 0, 0, 0],
                                                 [0, 0, 0, 0, 0, 0]],
                                           coords=dict(lat=[60, 0, -60],
                                                       lon=[-150, -90, -30, 30, 90, 150]))

    COMP_PERCENT_TO_AREA = xr.DataArray(data=[[0., 2215557.432, 4431114.864, 11077787.16, 17724459.456, 22155574.32],
                                              [0., 4431114.864, 8862229.728, 22155574.32, 35448918.912, 44311148.64],
                                              [0., 2215557.432, 4431114.864, 11077787.16, 17724459.456, 22155574.32]],
                                        coords=dict(lat=[60, 0, -60],
                                                    lon=[-150, -90, -30, 30, 90, 150]))

    COMP_PAD_GLOBAL = xr.DataArray(data=[[0, 1, 1, 1, 1, 0],
                                         [0, 1, 1, 1, 1, 0],
                                         [0, 0, 0, 0, 0, 0]],
                                   coords=dict(lat=[60, 0, -60],
                                               lon=[-150, -90, -30, 30, 90, 150]))

    COMP_REGRID = xr.DataArray(data=[[2.25, 2.25, 2.25, 2.25],
                                     [2.25, 2.25, 2.25, 2.25]],
                               coords=dict(lat=[45, -45],
                                           lon=[-135, -45, 45, 135]))

    COMP_INTERP_HELPER = xr.DataArray(data=[100, 100, 150, 200, 200],
                                      coords=dict(year=[2005, 2010, 2015, 2020, 2025]))

    COMP_LOAD_FILE_NC = xr.Dataset(data_vars=dict(proxy=(['year', 'lat', 'lon'],
                                                         [[[0.75, 2.25, 2.25, 0.75],
                                                           [0.25, 0.75, 0.75, 0.25]]])),
                                   coords=dict(year=[2010],
                                               lat=[45, -45],
                                               lon=[-135, -45, 45, 135]))

    def test_clean_spatial_dims(self):
        da_in = xr.DataArray(data=[[0, 0, 0, 0, 0, 0],
                                   [0, 0, 0, 0, 0, 0],
                                   [0, 0, 0, 0, 0, 0],
                                   [0, 0, 0, 0, 0, 0]],
                             coords=dict(latitude=[-60, 0, 0.00000000001, 60],
                                         longitude=[-150, -90, -30, 30, 90, 150]))

        da_out = gridded.clean_spatial_dims(da_in)

        xr.testing.assert_equal(da_out, TestGridded.COMP_CLEAN_SPATIAL_DIMS)

    def test_percent_to_area(self):
        da_in = xr.DataArray(data=[[0.0, 0.1, 0.2, 0.5, 0.8, 1.0],
                                   [0.0, 0.1, 0.2, 0.5, 0.8, 1.0],
                                   [0.0, 0.1, 0.2, 0.5, 0.8, 1.0]],
                             coords=dict(lat=[60, 0, -60],
                                         lon=[-150, -90, -30, 30, 90, 150]))

        da_out = gridded.percent_to_area(da_in)

        xr.testing.assert_allclose(da_out, TestGridded.COMP_PERCENT_TO_AREA)

    def test_pad_global(self):

        da_in = xr.DataArray(data=[[1, 1, 1, 1],
                                   [1, 1, 1, 1]],
                             coords=dict(lat=[60, 0],
                                         lon=[-90, -30, 30, 90]))

        da_out = gridded.pad_global(da_in)

        xr.testing.assert_equal(da_out, TestGridded.COMP_PAD_GLOBAL)

    def test_regrid(self):
        da_in = xr.DataArray(data=[[1, 1, 1, 1, 1, 1],
                                   [1, 1, 1, 1, 1, 1],
                                   [1, 1, 1, 1, 1, 1]],
                             coords=dict(lat=[60, 0, -60],
                                         lon=[-150, -90, -30, 30, 90, 150]))

        da_out = gridded.regrid(da_in, target_resolution=90, method='extensive')

        xr.testing.assert_equal(da_out, TestGridded.COMP_REGRID)

    def test_interp_helper(self):

        da_in = xr.DataArray(data=[100, 200],
                             coords=dict(year=[2010, 2020]))

        da_out = gridded.interp_helper(da_in, [2005, 2010, 2015, 2020, 2025])

        xr.testing.assert_equal(da_out, TestGridded.COMP_INTERP_HELPER)

    def test_load_file_nc(self):

        filename = os.path.join(os.path.dirname(__file__), 'data/netcdf.nc')
        ds_out = gridded.load_file(filename,
                                   target_resolution=90,
                                   years=[2010],
                                   variables=['proxy'],
                                   flags=['short_name_as_name']).compute()

        xr.testing.assert_equal(ds_out, TestGridded.COMP_LOAD_FILE_NC)


if __name__ == '__main__':
    unittest.main()
