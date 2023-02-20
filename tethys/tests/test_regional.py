import unittest

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



if __name__ == '__main__':
    unittest.main()
