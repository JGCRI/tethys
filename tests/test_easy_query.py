import unittest

import tethys.datareader.easy_query as easy_query


class TestEasyQuery(unittest.TestCase):

    COMP_QUERY_STRING = """<dummyQuery title="">
    <axis1 name="axis">axis</axis1>
    <axis2 name="year">demand-physical[@vintage]</axis2>
    <xPath>*[@type='sector' and (@name='Beef' or @name='Dairy')]//*[@type='technology' and not (starts-with(@name, 'water_td_'))]//*[@type='input' and ((ends-with(@name, '_water withdrawals')) or (starts-with(@name, 'water_td_') and ends-with(@name, '_W')))]//demand-physical/node()</xPath>
    </dummyQuery>"""

    def test_easy_query(self):
        query = easy_query.easy_query('demand-physical', sector=['Beef', 'Dairy'], technology='!water_td_*',
                                      input=['*_water withdrawals', 'water_td_*_W'])

        self.assertEqual(query.querystr, TestEasyQuery.COMP_QUERY_STRING)


if __name__ == '__main__':
    unittest.main()
