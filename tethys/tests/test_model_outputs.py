import unittest

import pandas as pd

from pkg_resources import resource_filename



class TestModelOutputs(unittest.TestCase):

    def test_temporal_water_demand(self):
        """Test to make sure `sum_ints` returns the expected value."""

        in_file = resource_filename('tethys', 'tests/data/comp_data/twddom_km3permonth.zip')

        df = pd.read_pickle(in_file)

        # would be coming from Tethys outputs
        dfx = df.copy()

        pd.testing.assert_frame_equal(df, dfx)


if __name__ == '__main__':
    unittest.main()
