from tethys.spatial_data import load_file


def monthly_distribution(self):
    """Temporal downscaling of irrigation water demand"""

    years = range(self.years[0], self.years[-1] + 1)
    irr = load_file(self.temporal_files['irr'], self.resolution, years, regrid_method='label')['pirrww']

    irr_regions = self.inputs.region[(self.inputs.sector == 'Irrigation') &
                                     (self.inputs.region.isin(self.region_masks.region.data))].unique()

    region_masks = self.region_masks.sel(region=irr_regions)

    irr_grouped = irr.where(region_masks, 0)
    month_sums = irr_grouped.sum(dim=('lat', 'lon'))
    year_sums = month_sums.sum(dim='month').where(lambda x: x != 0, 1)  # avoid 0/0

    out = region_masks.dot(month_sums / year_sums, dims='region')

    return out
