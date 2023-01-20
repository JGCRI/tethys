from tethys.datareader.gridded import load_file


def temporal_distribution(model):
    """Temporal downscaling of irrigation water demand"""

    years = range(model.years[0], model.years[-1] + 1)
    irr = load_file(model.temporal_files['irr'], model.resolution, years, regrid_method='label')['pirrww']

    irr_regions = model.inputs.region[(model.inputs.sector == 'Irrigation') &
                                      (model.inputs.region.isin(model.region_masks.region.data))].unique()

    region_masks = model.region_masks.sel(region=irr_regions)

    irr_grouped = irr.where(region_masks, 0)
    month_sums = irr_grouped.sum(dim=('lat', 'lon'))
    year_sums = month_sums.sum(dim='month').where(lambda x: x != 0, 1)  # avoid 0/0

    distribution = region_masks.dot(month_sums / year_sums, dims='region')

    return distribution
