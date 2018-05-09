"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov); Chris R. Vernon (chris.vernon@pnnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute

This is an example program showing how to run the model.

"""

import os
from tethys.model import Tethys


if __name__ == "__main__":

    # get path to config.ini in the example dir
    cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')

    # run the Tethys model and save outputs
    dmw = Tethys(config=cfg)

    # if needed, reuse the gridded data or gis data output by the model
    grid_outputs = dmw.gridded_data
    gis_outputs = dmw.gis_data

    # import gcam_reader
    # import pandas as pd
    # import numpy as np
    # import sys
    # import os
    #
    # dbpath = '/Users/d3y010/projects/gcam_ecosystem/gcam_reader/from_xinya/GCAM_database'
    # dbfile = "outRefMrk"
    # dbqueries = '/Users/d3y010/repos/github/tethys/example/Input/GCAM/query_regaez.xml'
    # subreg = 'AEZ'
    #
    # # region and basin name references
    # f_region_name = '/Users/d3y010/repos/github/tethys/example/Input/rgn32/RgnNames.csv'
    # f_basin_name = '/Users/d3y010/repos/github/tethys/example/Input/gcam_basin_lookup.csv'
    #
    # # buffalo fraction per region
    # bfracFAO2005 = pd.read_csv('/Users/d3y010/repos/github/tethys/example/Input/rgn32/bfracFAO2005.csv',
    #                            usecols=['buffalo-fraction'])
    # bfracFAO2005['region_id'] = bfracFAO2005.index.copy() + 1
    # bfracFAO2005.set_index('region_id', inplace=True)
    # d_buf_frac = bfracFAO2005.to_dict()['buffalo-fraction']
    #
    # # goat fraction per region
    # gfracFAO2005 = pd.read_csv('/Users/d3y010/repos/github/tethys/example/Input/rgn32/gfracFAO2005.csv',
    #                            usecols=['goat-fraction'])
    # gfracFAO2005['region_id'] = gfracFAO2005.index.copy() + 1
    # gfracFAO2005.set_index('region_id', inplace=True)
    # d_goat_frac = gfracFAO2005.to_dict()['goat-fraction']
    #
    # # conn = gcam_reader.LocalDBConn(dbpath, dbfile, suppress_gabble=False)
    # # queries = gcam_reader.parse_batch_query(dbqueries)
    #
    # # show available queries
    # # print(['[{}] : {}'.format(idx, q.title) for idx, q in enumerate(queries)])
    #
    # # create dict of region_name: region_id
    # d_reg_name = pd.read_csv(f_region_name).groupby('region').sum().to_dict()[' region_id']
    #
    # # create dict of basin_name: basin_id
    # d_basin_name = pd.read_csv(f_basin_name, usecols=['glu_name', 'basin_id'], index_col='glu_name').to_dict()[
    #     'basin_id']
    #
    # # set crop type dictionary for crop to crop number lookup
    # d_crops = {'biomass': 1, 'Corn': 2, 'FiberCrop': 3, 'FodderGrass': 4, 'FodderHerb': 5,
    #            'MiscCrop': 6, 'OilCrop': 7, 'OtherGrain': 8, 'PalmFruit': 9, 'Rice': 10,
    #            'Root_Tuber': 11, 'SugarCrop': 12, 'Wheat': 13}
    #
    # # set ordering of livestorck
    # d_liv_order = {'Buffalo': 0, 'Cattle': 1, 'Goat': 2, 'Sheep': 3, 'Poultry': 4, 'Pork': 5}
    #
    #
    # def get_gcam_queries(db_path, db_file, f_queries):
    #     """
    #     Return available queries from GCAM database.
    #
    #     :param db_path:         full path to the directory containing the input GCAM database
    #     :param db_file:         directory name of the GCAM database
    #     :param f_queries:       full path to the XML query file
    #     :return:                gcam_reader db and queries objects
    #     """
    #
    #     # instantiate GCAM db
    #     c = gcam_reader.LocalDBConn(db_path, db_file, suppress_gabble=False)
    #
    #     # get queries
    #     q = gcam_reader.parse_batch_query(f_queries)
    #
    #     return c, q
    #
    #
    # def population_to_array(conn, query, d_reg_name, years=[2005, 2010, 2015, 2020, 2025]):
    #     """
    #     Query GCAM database for population. Place in format required by
    #     Tethys.
    #     In unit:  thousands
    #     Out unit:  ones
    #
    #     :param query:         XPath Query
    #     :param d_reg_name:    A dictionary of 'region_name': region_id
    #     :param years:         list of years to use in YYYY integer format
    #
    #     :return:              NumPy array of (regions, value per year) shape.
    #     """
    #     # query content to data frame
    #     df = conn.runQuery(query)
    #
    #     # get only target years
    #     df = df.loc[df['Year'].isin(years)].copy()
    #
    #     # map region_id to region name
    #     df['region'] = df['region'].map(d_reg_name)
    #
    #     # convert shape for use in Tethys
    #     piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0)
    #
    #     return piv.as_matrix() * 1000
    #
    #
    # conn, queries = get_gcam_queries(dbpath, dbfile, dbqueries)
    # print(queries[1].title)
    # print("CHECKED:  OK")
    # pop = population_to_array(conn, queries[1], d_reg_name)
    # print(pop.shape)
    # print(pop)
