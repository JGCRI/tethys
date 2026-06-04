import os
import pandas as pd
import xarray as xr

import gcamreader

from tethys.datareader.easy_query import easy_query
from tethys.datareader.regional import extract_resource_name
from tethys.utils.region_to_id_mapping import name_to_id_mapping


class get_source_shares:
    def __init__(self, gcam_db, basin_name_mapping="basin_name_mapping_im3", demand_type='withdrawals', region_masks=None, years=None):
        """
        Initialize get_source_shares with parameters for GCAM database and basin mapping.

        :param gcam_db: Path to the GCAM database file.
        :param basin_name_mapping: Basin name mapping dictionary, can change to other mapping in name_to_id_mapping.
        :param demand_type: Type of demand, either 'withdrawals' or 'consumption'.
        :param region_masks: xarray DataArray containing region masks.
        :param years: List of years to be included in the shares.
        """
        dbpath, dbfile = os.path.split(gcam_db)
        self.conn = gcamreader.LocalDBConn(dbpath, dbfile)
        self.basin_name_mapping = basin_name_mapping
        self.demand_type = demand_type
        self.region_masks = region_masks
        self.years = years

    def calculate_shares(self):
        """
        Query the GCAM database, process water data for the specified demand type,
        and calculate runoff and groundwater shares by region and year.

        :return: Processed DataFrame with calculated shares.
        """
        # query GCAM database for water used by source for the configured demand type
        if self.demand_type not in ('withdrawals', 'consumption'):
            raise ValueError(f"Unsupported demand_type: {self.demand_type!r}")
        query_type = f"*_water {self.demand_type}"
        shares_df = self.conn.runQuery(easy_query('production', replace_filters=True, resource=query_type))
        # extract and clean resource names (e.g., remove '_water withdrawals')
        shares_df['resource'] = shares_df['resource'].apply(extract_resource_name)

        # rest of the mappings should be fine, old GCAM versions have typos in basin names
        if self.basin_name_mapping == "basin_name_mapping_im3":
            shares_df['resource'] = shares_df['resource'].str.replace('_', ' ').str.replace('-', ' ')  # replace '_' and '-' with spaces

        # map resource names to short basin names and concatenate region and resource to work with region_masks
        shares_df['resourcemap'] = shares_df['resource'].map(name_to_id_mapping[self.basin_name_mapping])
        shares_df['region_resourcemap'] = shares_df['region'] + '_' + shares_df['resourcemap']

        # calculate shares of runoff and groundwater
        shares_df['share'] = shares_df.groupby(
            ['scenario', 'region', 'region_resourcemap', 'year']
        )['value'].transform(lambda x: x / x.sum() if x.sum() != 0 else 0)

        # capture basins that are mostly belonging to other countries
        if self.basin_name_mapping == 'basin_name_mapping_im3':
            shares_df = shares_df.replace({'region_resourcemap': {
                'Canada_FraserR': 'USA_FraserR',
                'Canada_GreatLakes': 'USA_GreatLakes',
                'Mexico_MexCstNW': 'USA_MexCstNW',
                'Canada_NelsonR': 'USA_NelsonR',
            }})

        # filter shares based on the region masks from the config file, otherwise all regions would be included
        shares_df = shares_df[shares_df['region_resourcemap'].isin(self.region_masks.region.values)]

        return shares_df

    def generate_gridded_shares(self, shares_df):
        """
        Generate gridded shares by subresource (e.g., runoff, groundwater).

        :param shares_df: DataFrame containing shares calculated by `calculate_shares`.
        :return: Dictionary of gridded shares by subresource.
        """
        gridded_shares_by_subresource = {}
        for subresource in shares_df.subresource.unique():
            gridded_shares_by_year = []
            for year in self.years:
                gridded_shares = None
                for basin in shares_df.region_resourcemap.unique():
                    gridded_shares = xr.where(
                        self.region_masks.sel(region=basin).load(),
                        shares_df[
                            (shares_df['year'] == year) &
                            (shares_df['region_resourcemap'] == basin) &
                            (shares_df['subresource'] == subresource)
                        ].iloc[0].share,
                        0 if gridded_shares is None else gridded_shares,
                        keep_attrs=False,
                    )
                gridded_shares_by_year.append(gridded_shares)

            # Stack years for the subresource
            gridded_shares_by_subresource[subresource] = xr.concat(
                gridded_shares_by_year,
                dim=pd.Index(self.years, name="year"),
            ).rename('share')

        return gridded_shares_by_subresource
