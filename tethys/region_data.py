import gcamreader
from tethys.utils.easy_query import easy_query


def load_region_data(dbpath, dbfile, rules, demand_type='withdrawals'):

    conn = gcamreader.LocalDBConn(dbpath, dbfile)

    df = conn.runQuery(easy_query('demand-physical', sector=rules_to_sectors(rules), technology='!water_td_*',
                                  input=[f'*_water {demand_type}', f'water_td_*_{demand_type[0].upper()}']))

    # add '_BasinName' to region if exists
    df['region'] += df['sector'].apply(extract_basin_name) + df['input'].apply(extract_basin_name)

    df['sector'] = df['sector'].apply(pretty_sector_name)

    df = df.groupby(['region', 'sector', 'year'])[['value']].sum().reset_index()

    return df


def extract_basin_name(x):
    """Maps 'water_td_irr_basin_C' to '_basin', and water_td_elec_C to ''"""
    if x.startswith('water_td_irr_'):
        return '_' + x.split('_')[3]
    return ''


sector_lookup = {'Domestic': 'water_td_dom_',
                 'Municipal': 'water_td_muni_',
                 'Electricity': 'water_td_elec_',
                 'Manufacturing': 'water_td_ind_',
                 'Mining': 'water_td_pri_',
                 'Livestock': 'water_td_an_',
                 'Irrigation': 'water_td_irr_'}


def pretty_sector_name(x):

    for k, v in sector_lookup.items():
        if x.startswith(v):
            return k

    return x


def ugly_sector_name(x):

    if x in sector_lookup:
        return sector_lookup[x] + '*'

    return x


def rules_to_sectors(rules):
    sectors = []
    for k, v in rules.items():
        sectors.append(ugly_sector_name(k))
        if isinstance(v, dict):
            sectors.extend(v.keys())
    return sectors


def elec_sector_weights(dbpath, dbfile):

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
