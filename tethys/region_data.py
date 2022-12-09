import numpy as np
import pandas as pd
import gcamreader


def load_region_data(df=None, csv=None, query=None, query_file=None, query_title=None, conn=None,
                     gcam_db_path=None, gcam_db_file=None, basin_column=None, elec_weights=False,
                     regions=None, sectors=None, years=None):
    # mess of a function

    if csv is not None:
        df = pd.read_csv(csv)
    elif df is None:
        if conn is None:
            conn = gcamreader.LocalDBConn(gcam_db_path, gcam_db_file, suppress_gabble=False)
        if query is None:
            query = next(i for i in gcamreader.parse_batch_query(query_file) if i.title == query_title)
        df = conn.runQuery(query)

    df.columns = df.columns.str.lower()

    df['sector'] = df['sector'].map(rename_sector)
    df['value'] = df['value'].astype(np.float32)

    if basin_column is not None:
        df['region'] += '_' + df[basin_column].apply(lambda x: x.strip('_W').strip('_C').split('_')[-1])

    df = df.groupby(['region', 'sector', 'year'])[['value']].sum().reset_index()

    if elec_weights:
        df['sector'] = df['sector'].map(elec_sector)
        df = df.groupby(['region', 'sector', 'year'])[['value']].sum() / df.groupby(['region', 'year'])[['value']].sum()
        df = df.reset_index()

    if regions is None:
        regions = df['region'].unique()
    if sectors is None:
        sectors = df['sector'].unique()
    if years is None:
        years = df['year'].unique()

    index = pd.MultiIndex.from_product([regions, sectors, years], names=['region', 'sector', 'year'])
    out = df.set_index(['region', 'sector', 'year']).reindex(index, fill_value=0)['value'].to_xarray()

    return out


def rename_sector(x):
    """Helper for converting full GCAM sector names to Tethys demand categories"""
    if x in ('domestic water', 'municipal water') or x.startswith('water_td_dom_'):
        return 'Domestic'
    elif x.startswith('elec') or x.startswith('water_td_elec_'):
        return 'Electricity'
    elif x.startswith('industr') or x.startswith('water_td_ind_'):
        return 'Manufacturing'
    elif x in ('regional coal', 'nuclearFuelGenIII', 'regional natural gas', 'unconventional oil production', 'regional oil', 'nuclearFuelGenII') or x.startswith('water_td_pri_'):
        return 'Mining'
    elif x.startswith('water_td_irr_'):
        return 'Irrigation'
    elif x.startswith('water_td_an_'):
        return 'Livestock'
    return x


def elec_sector(x):
    """Helper for electricity demand sectors"""
    if x in ('comm heating', 'resid heating', 'comm hot water', 'resid furnace fans', 'resid hot water'):
        return 'Heating'
    elif x in ('comm cooling', 'resid cooling', 'comm refrigeration', 'resid freezers', 'resid refrigerators'):
        return 'Cooling'
    else:
        return 'Other'
