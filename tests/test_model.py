import unittest

import os
import xarray as xr
import tethys


class TestModel(unittest.TestCase):

    def test_run_model(self):

        config_file = os.path.join(os.path.dirname(__file__), 'data/config_test.yml')

        m = tethys.run_model(config_file)
        expected_output = xr.open_dataset(os.path.join(os.path.dirname(__file__), 'data/expected_output.nc'))

        xr.testing.assert_allclose(m.outputs, expected_output)


if __name__ == '__main__':
    unittest.main()
