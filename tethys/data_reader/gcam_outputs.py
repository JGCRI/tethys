"""
Import and process sector data from GCAM source database.

@author: Chris R. Vernon (chris.vernon@pnnl.gov), Xinya Li (xinya.li@pnl.gov)

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute
"""

import gcamreader
import numpy as np
import pandas as pd


# codes for 50 states + DC + PR
states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL',
          'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA',
          'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE',
          'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR',
          'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI',
          'WV', 'WY']


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


def population_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for population. Place in format required by
    Tethys.
    In unit:  thousands
    Out unit:  ones

    :param conn:          gcamreader database object
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

    # Remove NA's
    df = df[df['region'].notnull()]

    # Remove USA if using GCAM USA
    if any(item in d_reg_name for item in states):
        df.loc[df.region == 1, 'value'] = 0

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region'], columns='Year', fill_value=0)

    return piv.values * 1000


def df_to_array(df, d_reg_name, years):
    # pivot df to region - year array, then filter, expand, and order regions and years
    pivot = pd.pivot_table(df, values='value', index='region', columns='Year', fill_value=0, aggfunc=np.sum)
    pivot = pivot.reindex(index=sorted(d_reg_name.values()), columns=years, fill_value=0)
    return pivot.to_numpy()


def nonag_water_demand_to_array(conn, query, d_reg_name, years):
    """
    Query GCAM database for industrical manufacturing water demand (billion m3).
    Place in format required by Tethys.

    :param conn:          gcamreader database object
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

    # Restructure data (For GCAM USA queries)
    # Check if column name "input" exists it means that the new GCAM USA queries were used.
    # Rename this to "output" to conform with original format
    if 'output' in df.columns:
        df.rename(columns={"output": "input"}, inplace=True)

    # Remove USA if using GCAM USA
    if any(item in d_reg_name for item in states):
        df.loc[df.region == 1, 'value'] = 0

    return df_to_array(df, d_reg_name, years)


def livestock_water_demand_to_array(conn, query, query_core, d_reg_name, years):
    """
    Query GCAM database for livestock water demand (billion m3).
    Place in format required by Tethys.

    :param conn:          gcamreader database object
    :param query:         XPath Query
    :param query_core:    XPath Query for GCAM core
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param years:         list of years to use

    :return:              NumPy array of (regions per type, years) shape
    """
    # query content to data frame
    df = conn.runQuery(query)

    # If using GCAM USA queries
    # Restructure data (For GCAM USA queries) & also read in core GCAM values to distribute by animal
    # Check if column name "input" exists it means that the new GCAM USA queries were used.
    # Rename this to "output" to conform with original format
    if 'output' in df.columns:
        df.rename(columns={"output": "input"}, inplace=True)
        df_core = conn.runQuery(query_core)
        df_core_sum = df_core.groupby(['region', 'Year', 'sector', 'Units', 'scenario', 'input']).agg({'value': 'sum'}).reset_index()
        df_core_non_us = df_core_sum[~df_core_sum['region'].str.contains("USA")]
        df_core_us = df_core_sum[df_core_sum['region'].str.contains("USA")]
        df_core_us_ratio = df_core_us.assign(
            ratio=lambda x: x['value'] / (x.groupby(['region', 'Year']).transform('sum')['value'])
        )
        d_reg_name_us = dict(filter(lambda elem: elem[1] > 32, d_reg_name.items()))
        search_list = '|'.join(d_reg_name_us.keys())
        df_us = df[df['region'].str.contains(search_list)]
        df_us_new = pd.merge(df_us[['Units', 'scenario', 'region', 'input', 'Year', 'value']],
                             df_core_us_ratio[['Year', 'sector', 'ratio']], on=['Year'], how='left')
        df_us_new['value'] = df_us_new['ratio']*df_us_new['value']
        df_us_new = df_us_new.drop('ratio', 1)
        df = df_us_new.append(df_core_non_us)

    # drop unneeded cols
    df.drop(['Units', 'scenario', 'input'], axis=1, inplace=True)

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # Remove USA if using GCAM USA
    if any(item in d_reg_name for item in states):
        df.loc[df.region == 1, 'value'] = 0

    # set ordering of livestock
    # combine beef and dairy into "bovine" that will be proxied by buffalo + cattle
    # keep sheepgoat and use sheep + goat as proxy
    df['sector'] = df['sector'].map({'Beef': 0, 'Dairy': 0, 'SheepGoat': 1, 'Poultry': 2, 'Pork': 3})

    # convert shape for use in Tethys, handle order and filter years
    piv = pd.pivot_table(df, values='value', index=['sector', 'region'], columns='Year', fill_value=0, aggfunc=np.sum)
    piv = piv.reindex(index=[(i, j) for i in range(4) for j in sorted(d_reg_name.values())], columns=years, fill_value=0)

    return np.reshape(piv.to_numpy(), (4, len(d_reg_name), len(years)))


def land_to_array(conn, query, query_core, basin_state_area, d_reg_name, d_basin_name, sub_to_sector, sector_to_id, years):
    """
    Query GCAM database for irrigated land area per region, subregion,
    and crop type.  Place in format required by Tethys.

    :param conn:          gcamreader database object
    :param query:         XPath Query
    :param query_core:    XPath Query for GCAM core
    :param basin_state_area:  state basin area ratios for GCAM USA
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

    # If using GCAM USA queries
    # Restructure data (For GCAM USA queries) & also read in core GCAM values to distribute by basin
    # Check if length of d_reg_name are more than 33 which indicates it includes states from GCAM USA
    # Apply the distribution per basin to state/basin
    if any(item in d_reg_name for item in states):
        # Get US land allocation by basin
        df_us = df[df['region'].str.contains("USA")].copy()
        df_us['basin'] = df_us['land-allocation'].str.replace("^.*?_", "")
        df_us['basin'] = df_us['basin'].str.replace("_IRR.*$", "")
        df_us['basin'] = df_us['basin'].str.replace("_RFD.*$", "")
        df_us = df_us.drop('region', axis=1)
        # Get US states and basins
        df_core = conn.runQuery(query_core)
        df_core_st_basin = df_core[df_core['region'].str.contains("USA")].copy()
        df_core_st_basin = df_core_st_basin[['subsector', 'sector']].drop_duplicates().reset_index(drop=True)
        df_core_st_basin.rename(columns={"subsector": "region", "sector": "basin"}, inplace=True)
        df_core_st_basin['basin'] = df_core_st_basin['basin'].str.replace("water_td_irr_", "")
        df_core_st_basin['basin'] = df_core_st_basin['basin'].str.replace("_W", "")
        df_core_st_basin['basin'] = df_core_st_basin['basin'].str.replace("_C", "")  # added this to fix consumption
        # Make a copy of US values for each state by joining by basin
        df_us_new = pd.merge(df_us, df_core_st_basin, on=['basin'], how='left')
        df_area = pd.read_csv(basin_state_area)  # Get area ratio of each state in basins
        df_area = df_area[['basin', 'subRegion_State', 'area_ratio']]
        df_area.rename(columns={"subRegion_State": "region"}, inplace=True)
        df_us_new_area = pd.merge(df_us_new, df_area, on=['basin', 'region'], how='left')
        df_us_new_area['valueNew'] = df_us_new_area['value']*df_us_new_area['area_ratio']
        df_us_new_area = df_us_new_area.drop(['basin', 'value', 'area_ratio'], axis=1)
        df_us_new_area.rename(columns={"valueNew": "value"}, inplace=True)
        df = df.append(df_us_new_area)
        # Check US Total
        # df_us_new_check = df_us_new_area.groupby(['Year', 'Units', 'land-allocation','scenario']).agg(
        #    {'value': 'sum'}).reset_index()

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # Remove USA if using GCAM USA
    if any(item in d_reg_name for item in states):
        df.loc[df.region == 1, 'value'] = 0

    # drop unused columns
    df.drop(['Units', 'scenario'], axis=1, inplace=True)

    # replace region name with region number
    df['region'] = df['region'].map(d_reg_name)

    temp = df['land-allocation'].apply(lambda x: x.split('_')[-1])
    if 'IRR' in temp.unique():
        df['crop'] = df['land-allocation'].apply(lambda x: x.split('_')[:-2][0])  # 'Root_Tuber' will be 'Root'
        df['subreg'] = df['land-allocation'].apply(lambda x: x.split('_')[-2]).map(d_basin_name)
        df['use'] = df['land-allocation'].apply(lambda x: x.split('_')[-1])
        df = df.loc[df['use'] == 'IRR'].copy()
        df.drop('land-allocation', axis=1, inplace=True)
    else:
        # create management type column
        df['mgmt'] = df['land-allocation'].apply(lambda x: x.split('_')[-1])
        df['crop'] = df['land-allocation'].apply(lambda x: x.split('_')[:-3][0])  # 'Root_Tuber' will be 'Root'
        df['subreg'] = df['land-allocation'].apply(lambda x: x.split('_')[-3]).map(d_basin_name)
        df['use'] = df['land-allocation'].apply(lambda x: x.split('_')[-2])
        df = df.loc[df['use'] == 'IRR'].copy()
        df.drop('land-allocation', axis=1, inplace=True)
    
        # sum hi and lo management allocation
        df = df.drop(['mgmt'], axis=1)
        df = df.groupby(['region', 'subreg', 'crop', 'use', 'Year']).sum()
        df = df.reset_index()

    # aggregate all biomass crops
    df['crop'] = df['crop'].map(sub_to_sector)
    grp = df.groupby(['region', 'subreg', 'crop', 'Year']).sum()
    grp.reset_index(inplace=True)

    # convert crop name to number reference
    grp['crop'] = grp['crop'].map(sector_to_id)

    # convert shape for use in Tethys
    piv = pd.pivot_table(grp, values='value', index=['region', 'subreg', 'crop'], columns='Year', fill_value=0, aggfunc=np.sum)
    piv.reset_index(inplace=True)

    return piv.values


def irr_water_demand_to_array(conn, query, query_core, d_reg_name, d_basin_name, years):
    """
    Query GCAM database for irrigated water demand (billion m3).  Place
    in format required by Tethys.

    :param conn:          gcam_reader database object
    :param query:         XPath Query
    :param query_core:    XPath Query for GCAM core
    :param d_reg_name:    A dictionary of 'region_name': region_id
    :param d_crops:       A dictionary of 'crop_name': crop_id
    :param years:         list of years to use

    :return:               NumPy array where col_1: region_id, col_2: subreg_id,
                           col_3: crop_number, col_n...n: irrigated demand per year in
                           billion m3
    """
    # query content to data frame
    df = conn.runQuery(query)

    # If using GCAM USA queries
    # Restructure data (For GCAM USA queries) & also read in core GCAM values to distribute by crop
    # Check if column name "input" exists it means that the new GCAM USA queries were used.
    # Rename this to "output" to conform with original format
    if 'output' in df.columns:
        df = df.drop(['region', 'output'], axis=1)
        df.rename(columns={"sector": "input", "subsector": "region"}, inplace=True)
        df_core = conn.runQuery(query_core)
        df_core_sum = df_core.groupby(['region', 'Year', 'sector', 'subsector', 'Units', 'scenario', 'input']).agg(
            {'value': 'sum'}).reset_index()
        df_core_non_us = df_core_sum[~df_core_sum['region'].str.contains("USA")]
        df_core_us = df_core_sum[df_core_sum['region'].str.contains("USA")]
        df_core_us_ratio = df_core_us.assign(
            ratio=lambda x: x['value'] / (x.groupby(['input', 'Year']).transform('sum')['value'])
        )
        d_reg_name_us = dict(filter(lambda elem: elem[1] > 32, d_reg_name.items()))
        search_list = '|'.join(d_reg_name_us.keys())
        df_us = df[df['region'].str.contains(search_list)]
        df_us_new = pd.merge(df_us[['Units', 'scenario', 'region', 'input', 'Year', 'value']],
                             df_core_us_ratio[['Year', 'sector', 'subsector', 'input', 'ratio']], on=['Year', 'input'], how='left')
        df_us_new['value'] = df_us_new['ratio'] * df_us_new['value']
        df_us_new = df_us_new.drop('ratio', 1)
        df = df_us_new.append(df_core_non_us)
        # Check US Total
        # df_us_new_check = df_us_new.groupby(['Year', 'region', 'Units', 'scenario', 'input']).agg(
        #    {'value': 'sum'}).reset_index()

    df2 = df.loc[:, ['subsector', 'sector']]
    df2['subsector'] = df2['subsector'].str.replace('_.*$', '', regex=True)
    df2.set_index('subsector', inplace=True)
    sub_to_sector = df2.to_dict()['sector']
    sector_to_id = dict((k, v + 1) for v, k in enumerate(sorted(set(sub_to_sector.values()), key=str.upper)))

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # drop unused columns
    df.drop(['Units', 'scenario', 'input'], axis=1, inplace=True)

    # replace region name with region number
    df['region'] = df['region'].map(d_reg_name)

    df['subreg'] = df['subsector'].apply(lambda x: x.split('_')[-1]).map(d_basin_name)

    df['crop'] = df['sector'].map(sector_to_id)

    # drop sector
    df.drop('sector', axis=1, inplace=True)

    # Remove USA if using GCAM USA
    if any(item in d_reg_name for item in states):
        df.loc[df.region == 1, 'value'] = 0

    # convert shape for use in Tethys
    piv = pd.pivot_table(df, values='value', index=['region', 'subreg', 'crop'], columns='Year', fill_value=0, aggfunc=np.sum)
    piv.reset_index(inplace=True)

    return piv.values, sub_to_sector, sector_to_id


def elec_proportions_to_array(conn, query, d_reg_name, years):

    # query content to data frame
    df = conn.runQuery(query)

    # get only target years
    df = df.loc[df['Year'].isin(years)].copy()

    # map region_id to region name
    df['region'] = df['region'].map(d_reg_name)

    # Remove USA if using GCAM USA
    if any(item in d_reg_name for item in states):
        df.loc[df.region == 1, 'value'] = 0

    # comm/resid heating/cooling is from regular GCAM, the rest is categories from states that might be equivalent
    # "other" building elec sector is implicit by what's left
    heating_sectors = ['comm heating', 'resid heating', 'comm hot water', 'resid furnace fans', 'resid hot water']
    cooling_sectors = ['comm cooling', 'resid cooling', 'comm refrigeration', 'resid freezers', 'resid refrigerators']

    bld_array = df_to_array(df[df.input == 'elect_td_bld'], d_reg_name, years)
    heating_array = df_to_array(df[df.sector.isin(heating_sectors)], d_reg_name, years)
    cooling_array = df_to_array(df[df.sector.isin(cooling_sectors)], d_reg_name, years)
    total_array = df_to_array(df, d_reg_name, years)

    # build output dict of ratios, handle 0/0 case
    ele = {'building': np.divide(bld_array, total_array, out=np.zeros_like(bld_array), where=total_array != 0),
           'heating': np.divide(heating_array, bld_array, out=np.zeros_like(heating_array), where=bld_array != 0),
           'cooling': np.divide(cooling_array, bld_array, out=np.zeros_like(cooling_array), where=bld_array != 0)
           }
    ele['industry'] = 1 - ele['building']
    ele['others'] = 1 - ele['heating'] - ele['cooling']

    return ele


def get_gcam_data(years, RegionNames, gcam_basin_lu, GCAM_DBpath, GCAM_DBfile, query_file,
                  basin_state_area, PerformTemporal, demand, variant):
    """
    Import and format GCAM data from database for use in Tethys.

    :return:                dictionary, {metric: numpy array, ...}
    """

    # get region info as dict
    d_reg_name = get_region_info(RegionNames)

    # get basin info as dict
    d_basin_name = get_basin_info(gcam_basin_lu)

    # get GCAM database connection and queries objects
    conn = gcamreader.LocalDBConn(GCAM_DBpath, GCAM_DBfile, suppress_gabble=False)
    queries = {i.title: i for i in gcamreader.parse_batch_query(query_file)}

    d = {'pop_tot': population_to_array(conn, queries['Population by region'], d_reg_name, years),
         'rgn_wddom': nonag_water_demand_to_array(conn, queries[f'Water {demand} (Domestic)'], d_reg_name, years),
         'rgn_wdelec': nonag_water_demand_to_array(conn, queries[f'Water {demand} (Industrial - Electricity)'], d_reg_name, years),
         'rgn_wdmfg': nonag_water_demand_to_array(conn, queries[f'Water {demand} (Industrial-Manufacturing)'], d_reg_name, years),
         'rgn_wdmining': nonag_water_demand_to_array(conn, queries[f'Water {demand} (Resource Extraction){variant}'], d_reg_name, years),
         'wdliv': livestock_water_demand_to_array(conn, queries[f'Water {demand} (Livestock){variant}'],
                                                  queries[f'Water {demand} (Livestock)'], d_reg_name, years)}

    d['irrV'], sub_to_sector, sector_to_id = irr_water_demand_to_array(conn, queries[f'Water {demand} (Agriculture by subsector){variant}'],
                                                                       queries[f'Water {demand} (Agriculture by subsector)'],
                                                                       d_reg_name, d_basin_name, years)
    d['irrArea'] = land_to_array(conn, queries[f'Crop Land Allocation'], queries[f'Water {demand} (Agriculture by subsector){variant}'], basin_state_area, d_reg_name, d_basin_name, sub_to_sector, sector_to_id, years)

    if PerformTemporal:  # only query this if needed, otherwise save time
        d['elec_p'] = elec_proportions_to_array(conn, queries['elec consumption by demand sector'], d_reg_name, years)

    return d
