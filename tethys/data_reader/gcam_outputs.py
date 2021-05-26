"""
Import and process sector data from GCAM source database.

@author: Chris R. Vernon (chris.vernon@pnnl.gov), Xinya Li (xinya.li@pnl.gov)

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""

import gcam_reader
import numpy as np
import pandas as pd


# crop name to crop_id
d_crops = {'biomass': 1, 'Corn': 2, 'FiberCrop': 3, 'FodderGrass': 4, 'FodderHerb': 5,
           'MiscCrop': 6, 'OilCrop': 7, 'OtherGrain': 8, 'PalmFruit': 9, 'Rice': 10,
           'Root_Tuber': 11, 'SugarCrop': 12, 'Wheat': 13}

# list of functional types to be combined into biomass category
l_biomass = ["eucalyptus", "Jatropha", "miscanthus", "willow", "biomassOil"]
    
# set ordering of livestock
d_liv_order = {'Buffalo': 0, 'Cattle': 1, 'Goat': 2, 'Sheep': 3, 'Poultry': 4, 'Pork': 5}


def get_buffalo_frac(f):
    """
    Create a dictionary of buffalo fraction per region id.

    :param f:           full path to CSV file containing buffalo fraction per region
    :return:            dictionary; {region_id:  buffalo_fraction, ...}
    """
    df = pd.read_csv(f, usecols=['buffalo-fraction'])
    df['region_id'] = df.index.copy() + 1
    df.set_index('region_id', inplace=True)

    return df.to_dict()['buffalo-fraction']


def get_goat_frac(f):
    """
    Create a dictionary of goat fraction per region id.

    :param f:           full path to CSV file containing goat fraction per region
    :return:            dictionary; {region_id:  goat_fraction, ...}
    """
    df = pd.read_csv(f, usecols=['goat-fraction'])
    df['region_id'] = df.index.copy() + 1
    df.set_index('region_id', inplace=True)

    return df.to_dict()['goat-fraction']


def get_region_info(f):
    """
    Get a dictionary of {region_name: region_id, ...}

    :param f:           full path to CSV file of GCAM region names and ids
    :return:            dictionary, {region_name: region_id, ...}
    """
    return pd.read_csv(f).groupby('region').sum().to_dict()['region_id']


def get_basin_info(f):
    """
    Get a dictionary of {region_name: region_id, ...}

    :param f:           full path to CSV file of GCAM basin names and ids
    :return:            dictionary, {basin_name: basin_id, ...}
    """
    return pd.read_csv(f, usecols=['glu_name', 'basin_id'], index_col='glu_name').to_dict()['basin_id']


def get_gcam_queries(db_path, db_file, f_queries):
    """
    Return available queries from GCAM database.

    :param db_path:         full path to the directory containing the input GCAM database
    :param db_file:         directory name of the GCAM database
    :param f_queries:       full path to the XML query file
    :return:                gcam_reader db and queries objects
    """
    # instantiate GCAM db
    c = gcam_reader.LocalDBConn(db_path, db_file, suppress_gabble=False)

    # get queries
    q = gcam_reader.parse_batch_query(f_queries)

    return c, q


def population_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for population. Place in format required by
    Tethys.
    In unit:  thousands
    Out unit:  ones

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use in YYYY integer format

    :return:              NumPy array of (regions, value per year) shape.
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0)

    return piv.values * 1000


def irr_water_demand_to_array(conn, query, subreg, d_reg_name, d_basin_name, d_crops, years):
    """
    Query GCAM database for irrigated water demand (billion m3).  Place
    in format required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param subreg:        Either 0 (AEZ) or 1 (BASIN)
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param d_crops:       A dictionary of 'crop_name': crop_id
    :param years:         list of years to use

    :return:               NumPy array where col_1: region_id, col_2: subreg_id,
                           col_3: crop_number, col_n...n: irrigated demand per year in
                           billion m3
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # drop unused columns
    df.drop(['Units', 'scenario', 'input'], axis=1, inplace=True)

    # replace region name with region number
    df['region'] = df['region'].map(d_reg_name)

    if subreg == 0:
        # break out subregion number
        df['subreg'] = df['subsector'].apply(lambda x: int(x.split('AEZ')[1]))

    elif subreg == 1:
        df['subreg'] = df['subsector'].apply(lambda x: x.split('_')[-1]).map(d_basin_name)

    # break out crop and map the id to it
    df['crop'] = df['sector'].apply(lambda x: 'biomass' if x in l_biomass else x)
    df['crop'] = df['crop'].map(d_crops)

    # drop sector
    df.drop('sector', axis=1, inplace=True)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region', 'subreg', 'crop'], columns='Year', fill_value=0,aggfunc=np.sum)
    piv.reset_index(inplace=True)

    return piv.values


def dom_water_demand_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for domestic water demand (billion m3). Place in format
    required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use

    :return:              NumPy array of (regions, years) shape
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0, aggfunc=np.sum)

    return piv.values


def elec_water_demand_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for industrial electricity water demand (billion m3).
    Place in format required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use

    :return:              NumPy array of (regions, years) shape
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0, aggfunc=np.sum)

    return piv.values


def manuf_water_demand_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for industrical manufacturing water demand (billion m3).
    Place in format required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use

    :return:              NumPy array of (regions, years) shape
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0,aggfunc=np.sum)

    return piv.values


def mining_water_demand_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for industrical manufacturing water demand (billion m3).
    Place in format required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use

    :return:              NumPy array of (regions, years) shape
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0, aggfunc=np.sum)

    return piv.values


def livestock_water_demand_to_array(conn, query, d_reg_name, d_buf_frac, d_goat_frac, d_liv_order, years):
    """
    Query GCAM database for livestock water demand (billion m3).
    Place in format required by Tethys.

    Outputs are ordered by region and then by [Buffalo, Cattle, Goat, Sheep, Poultry, Pig]

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use

    :return:              NumPy array of (regions per type, years) shape
    """
    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # drop unneeded cols
    df.drop(['Units', 'scenario', 'input'], axis=1, inplace=True)

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region', 'sector'], columns='Year', fill_value=0, aggfunc=np.sum)
    piv.reset_index(inplace=True)

    # group beef and dairy
    bovine = piv.loc[piv['sector'].isin(('Beef', 'Dairy'))].copy().groupby(['region']).sum()
    bovine.reset_index(inplace=True)
    bovine['b_frac'] = bovine['region'].map(d_buf_frac)

    # break out fraction of buffalo
    buffalo = bovine.copy()
    buffalo['sector'] = 'Buffalo'
    buffalo[years] = buffalo[years].multiply(buffalo['b_frac'], axis='index')
    buffalo.drop('b_frac', axis=1, inplace=True)
    piv = pd.concat([piv, buffalo], sort=True)

    # break out fraction of cattle
    cattle = bovine.copy()
    cattle['sector'] = 'Cattle'
    cattle[years] = cattle[years].multiply((1 - cattle['b_frac']), axis='index')
    cattle.drop('b_frac', axis=1, inplace=True)
    piv = pd.concat([piv, cattle], sort=True)

    # extract sheepgoat and add goat fraction
    sheepgoat = piv.loc[piv['sector'] == 'SheepGoat'].copy()
    sheepgoat['g_frac'] = sheepgoat['region'].map(d_goat_frac)

    # break out fraction of goat
    goat = sheepgoat.copy()
    goat['sector'] = 'Goat'
    goat[years] = goat[years].multiply(goat['g_frac'], axis='index')
    goat.drop('g_frac', axis=1, inplace=True)
    piv = pd.concat([piv, goat], sort=True)

    # break out fraction of sheep
    sheep = sheepgoat.copy()
    sheep['sector'] = 'Sheep'
    sheep[years] = sheep[years].multiply((1 - sheep['g_frac']), axis='index')
    sheep.drop('g_frac', axis=1, inplace=True)
    piv = pd.concat([piv, sheep], sort=True)

    # drop aggregated sectors
    piv = piv.loc[piv['sector'].isin(tuple(d_liv_order))].copy()

    # add livestock order number
    piv['sector'] = piv['sector'].map(d_liv_order)

    # get set of expected regions
    actual_regions = set(d_reg_name.values())

    # create dict of regions in each sector from the data
    d_chk_regions = piv.groupby('sector')['region'].apply(set).to_dict()

    for sec in tuple(d_liv_order.values()):

        # get set of missing regions in sector
        miss_regions = actual_regions - d_chk_regions[sec]

        # add data as zeros for missing regions in each sector
        if len(miss_regions) > 0:
            for reg in miss_regions:
                d = {}
                d['region'] = [reg]
                d['sector'] = [sec]
                for i in years:
                    d[i] = [0.0]
                piv = pd.concat([piv, pd.DataFrame(d)])

    # sort outputs by region, sector
    piv.sort_values(by=['sector', 'region'], inplace=True)

    piv.set_index(['sector', 'region'], inplace=True)

    return piv.values


def land_to_array(conn, query, subreg, d_reg_name, d_basin_name, d_crops, years):
    """
    Query GCAM database for irrigated land area per region, subregion,
    and crop type.  Place in format required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param subreg:        Either 0 (AEZ) or 1 (BASIN)
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param d_basin_name:  A dictionary of 'basin_name' : basin_id
    :param d_crops:       A dictionary of 'crop_name': crop_id
    :param years:         list of years to use

    :return:               NumPy array where col_1: region_id, col_2: subreg_id,
                           col_3: crop_number, col_n...n: irrigated area per year in
                           thousands km2
    """

    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()    

    # keep types
    allpft = list(d_crops.keys()) + l_biomass

    # drop unused columns
    df.drop(['Units', 'scenario'], axis=1, inplace=True)

    # replace region name with region number
    df['region'] = df['region'].map(d_reg_name)

    if subreg == 0:
        # create crop type column
        df['crop'] = df['land-allocation'].apply(lambda x: x.split('AEZ')[0])

        # create subreg number column
        df['subreg'] = df['land-allocation'].apply(lambda x: int(x.split('AEZ')[1][:2]))

        # create use column
        df['use'] = df['land-allocation'].apply(lambda x: x.split('AEZ')[1][-3:])

        # only keep irrigated crops
        df = df.loc[df['use'] == 'IRR'].copy()

        # drop cols
        df.drop('land-allocation', axis=1, inplace=True)

    elif subreg == 1:
        temp = df['land-allocation'].apply(lambda x: x.split('_')[-1])
        if 'IRR' in temp.unique():
            df['crop'] = df['land-allocation'].apply(lambda x: x.split('_')[:-2][0]) # 'Root_Tuber' will be 'Root'
            df['subreg'] = df['land-allocation'].apply(lambda x: x.split('_')[-2]).map(d_basin_name)
            df['use'] = df['land-allocation'].apply(lambda x: x.split('_')[-1])
            df = df.loc[df['use'] == 'IRR'].copy()
            df.drop('land-allocation', axis=1, inplace=True)
        else:
            # create management type column
            df['mgmt'] = df['land-allocation'].apply(lambda x: x.split('_')[-1])
            df['crop'] = df['land-allocation'].apply(lambda x: x.split('_')[:-3][0]) # 'Root_Tuber' will be 'Root'
            df['subreg'] = df['land-allocation'].apply(lambda x: x.split('_')[-3]).map(d_basin_name)
            df['use'] = df['land-allocation'].apply(lambda x: x.split('_')[-2])
            df = df.loc[df['use'] == 'IRR'].copy()
            df.drop('land-allocation', axis=1, inplace=True)
    
            # sum hi and lo management allocation
            df = df.drop(['mgmt'],axis=1)
            df = df.groupby(['region', 'subreg', 'crop', 'use', 'Year']).sum()
            df = df.reset_index()

    # only keep crops in target list
    df['crop'] = df['crop'].apply(lambda x: 'Root_Tuber' if x == 'Root' else x)  # Correct "Root" back to crop name
    df = df.loc[df['crop'].isin(allpft)].copy()

    # aggregate all biomass crops
    df['crop'] = df['crop'].apply(lambda x: 'biomass' if x in l_biomass else x)
    grp = df.groupby(['region', 'subreg', 'crop', 'Year']).sum()
    grp.reset_index(inplace=True)

    # convert crop name to number reference
    grp['crop'] = grp['crop'].map(d_crops)

    # convert shape for use in Tethys
    piv = pd.pivot_table(grp, values='value', index=['region', 'subreg', 'crop'], columns='Year', fill_value=0, aggfunc=np.sum)
    piv.reset_index(inplace=True)

    return piv.values


def get_gcam_data(s):
    """
    Import and format GCAM data from database for use in Tethys.

    :param s:               Settings object
    :return:                dictionary, {metric: numpy array, ...}
    """
    
    if type(s.years) is str: # a single year string, multiple years will be list
        s.years = [s.years]

    years = [int(i) for i in s.years]

    # get region info as dict
    d_reg_name = get_region_info(s.RegionNames)

    # get basin info as dict
    d_basin_name = get_basin_info(s.gcam_basin_lu)

    # get buffalo fraction of region as dict
    d_buf_frac = get_buffalo_frac(s.buff_fract)

    # get goad fraction of region as dict
    d_goat_frac = get_goat_frac(s.goat_fract)

    # get GCAM database connection and queries objects
    conn, queries = get_gcam_queries(s.GCAM_DBpath, s.GCAM_DBfile, s.GCAM_query)
    
#     for q in queries:
#         df = conn.runQuery(q)
#         df.to_csv(q.title + ".csv", sep=',')

    d = {}
    d['pop_tot']      = population_to_array(conn, queries[1], d_reg_name, years)
    d['rgn_wddom']    = dom_water_demand_to_array(conn, queries[3], d_reg_name, years)
    d['rgn_wdelec']   = elec_water_demand_to_array(conn, queries[4], d_reg_name, years)
    d['rgn_wdmfg']    = manuf_water_demand_to_array(conn, queries[6], d_reg_name, years)
    d['rgn_wdmining'] = mining_water_demand_to_array(conn, queries[7], d_reg_name, years)
    d['wdliv']        = livestock_water_demand_to_array(conn, queries[5], d_reg_name, d_buf_frac, d_goat_frac, d_liv_order, years)
    d['irrArea']      = land_to_array(conn, queries[0], s.subreg, d_reg_name, d_basin_name, d_crops, years)
    d['irrV']         = irr_water_demand_to_array(conn, queries[2], s.subreg, d_reg_name, d_basin_name, d_crops, years)
    
#    for key, value in d.iteritems():
#        np.savetxt(key + '.csv', d[key], delimiter=',')

    return d
