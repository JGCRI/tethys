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


if __name__ == '__main__':
    unittest.main()
