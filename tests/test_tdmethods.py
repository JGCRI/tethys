import unittest

import os
import xarray as xr
import tethys


class TestTDMethods(unittest.TestCase):

    def test_domestic(self):
        from tethys.tdmethods.domestic import temporal_distribution

        tas_file = os.path.join(os.path.dirname(__file__), 'data/tas.nc')
        amplitude_file = os.path.join(os.path.dirname(__file__), 'data/amplitude.nc')

        m = tethys.model.Tethys(years=[2010, 2015], resolution=90, proxy_files={},
                                temporal_files=dict(tas=tas_file, domr=amplitude_file))
        da_out = temporal_distribution(m).compute()

        expected_output = xr.open_dataarray(
            os.path.join(os.path.dirname(__file__), 'data/expected_output_monthly_domestic.nc'))

        xr.testing.assert_allclose(da_out, expected_output)

    def test_irrigation(self):
        from tethys.tdmethods.irrigation import temporal_distribution

        dummy_csv = os.path.join(os.path.dirname(__file__), 'data/irr.csv')
        dummy_map = os.path.join(os.path.dirname(__file__), 'data/map.tif')
        irr_file = os.path.join(os.path.dirname(__file__), 'data/pirrww.nc')

        m = tethys.model.Tethys(years=[2010, 2015], resolution=90, proxy_files={},
                                csv=dummy_csv, map_files=[dummy_map],
                                temporal_files=dict(irr=irr_file))
        m._load_region_masks()
        m._load_inputs()
        da_out = temporal_distribution(m).compute()

        expected_output = xr.open_dataarray(
            os.path.join(os.path.dirname(__file__), 'data/expected_output_monthly_irrigation.nc'))

        xr.testing.assert_allclose(da_out, expected_output)


if __name__ == '__main__':
    unittest.main()
