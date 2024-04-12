import os
import gcamreader
from tethys.datareader.easy_query import easy_query


def load_region_data(gcam_db, sectors, demand_type='withdrawals'):
    """Load region-scale water demand from GCAM needed to carry out a configuration

    :param gcam_db: path to GCAM database (the folder containing the .basex files)
    :param sectors: GCAM sectors to filter to (friendly names will be converted to unfriendly names)
    :param demand_type: 'withdrawals' or 'consumption'
    :return: pandas dataframe with columns 'region', 'sector', 'year', 'value'
    """

    dbpath, dbfile = os.path.split(gcam_db)
    conn = gcamreader.LocalDBConn(dbpath, dbfile)

    # remove subsector and technology if present, convert friendly water demand sector names to internal
    search_sectors = list(set(unfriendly_sector_name(i.split('/')[0]) for i in sectors))

    inputs = {'withdrawals': ['water_td_*_W', '*_water withdrawals', '*_desalinated water'],
              'consumption': ['water_td_*_C', '*_water consumption']}.get(demand_type)

    df = conn.runQuery(easy_query('demand-physical', sector=search_sectors, technology='!water_td_*', input=inputs))

    # add '_BasinName' to region if exists
    df['region'] += df['sector'].apply(extract_basin_name) + df['input'].apply(extract_basin_name)

    # rename unfriendly sector names
    df['sector'] = df['sector'].apply(friendly_sector_name)

    # allow breaking down to the subsector or technology level
    df['sector'] = df['sector'] + '/' + df['subsector'] + '/' + df['technology']
    sorted_sectors = sorted(sectors, reverse=True)
    df['sector'] = df['sector'].map({x: greedy_match(x, sorted_sectors) for x in df['sector'].unique()})
    df = df[df['sector'].isin(sectors)]

    # aggregate
    df = df.groupby(['region', 'sector', 'year'])[['value']].sum().reset_index()

    return df


def extract_basin_name(x):
    """Maps 'water_td_irr_basin_C' to '_basin', and water_td_elec_C to ''"""
    if x.startswith('water_td_irr_'):
        return '_' + x.split('_')[3]
    return ''


# mapping from GCAM water input friendly names to the start of their full names
sector_lookup = {'Domestic': 'water_td_dom_',
                 'Municipal': 'water_td_muni_',
                 'Electricity': 'water_td_elec_',
                 'Manufacturing': 'water_td_ind_',
                 'Mining': 'water_td_pri_',
                 'Livestock': 'water_td_an_',
                 'Irrigation': 'water_td_irr_'}


def friendly_sector_name(x):
    """convert from GCAM water input name to friendly name"""

    for k, v in sector_lookup.items():
        if x.startswith(v):
            return k

    return x


def unfriendly_sector_name(x):
    """convert from friendly name to start of GCAM name"""

    if x in sector_lookup:
        return sector_lookup[x] + '*'

    return x


def greedy_match(x, names):
    for name in names:
        if x.startswith(name):
            return name
    return x


def elec_sector_weights(gcam_db):
    """Get the electricity sector weights from GCAM database"""

    dbpath, dbfile = os.path.split(gcam_db)
    conn = gcamreader.LocalDBConn(dbpath, dbfile)

    df = conn.runQuery(easy_query('demand-physical', input=['elect_td_bld', 'elect_td_ind', 'elect_td_trn']))
    df['sector'] = df['sector'].apply(elec_sector_rename)
    df = df.groupby(['region', 'sector', 'year'])[['value']].sum() / df.groupby(['region', 'year'])[['value']].sum()

    return df.reset_index()


def elec_sector_rename(x):
    """Helper for electricity demand sectors"""
    if x in ('comm heating', 'resid heating', 'comm hot water', 'resid furnace fans', 'resid hot water'):
        return 'Heating'
    elif x in ('comm cooling', 'resid cooling', 'comm refrigeration', 'resid freezers', 'resid refrigerators'):
        return 'Cooling'
    else:
        return 'Other'
