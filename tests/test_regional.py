import unittest

import os
import pandas as pd
import tethys.datareader.regional as regional


class TestRegional(unittest.TestCase):

    def test_extract_basin_name(self):

        self.assertEqual(regional.extract_basin_name('water_td_irr_basin_C'), '_basin')
        self.assertEqual(regional.extract_basin_name('water_td_elec_C'), '')

    def test_friendly_sector_name(self):

        self.assertEqual(regional.friendly_sector_name('water_td_dom_'), 'Domestic')
        self.assertEqual(regional.friendly_sector_name('Beef'), 'Beef')

    def test_unfriendly_sector_name(self):
        self.assertEqual(regional.unfriendly_sector_name('Domestic'), 'water_td_dom_*')
        self.assertEqual(regional.unfriendly_sector_name('Beef'), 'Beef')

    def test_elec_sector_rename(self):
        self.assertEqual(regional.elec_sector_rename('comm heating'), 'Heating')
        self.assertEqual(regional.elec_sector_rename('comm cooling'), 'Cooling')
        self.assertEqual(regional.elec_sector_rename('other'), 'Other')

    def test_load_region_data(self):
        gcamdb = os.path.join(os.path.dirname(__file__), 'data/testdb')
        print(gcamdb)


        df = regional.load_region_data(gcamdb, sectors=['municipal water'])

        expected = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data/testdb.csv'))
        pd.testing.assert_frame_equal(df, expected)


if __name__ == '__main__':
    unittest.main()
