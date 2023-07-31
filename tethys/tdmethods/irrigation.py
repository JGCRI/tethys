from tethys.datareader.gridded import load_file
from tethys.datareader.maps import load_region_map


def temporal_distribution(years, resolution, regionfile, irrfile, irrvar='pirrww'):
    """Temporal downscaling of irrigation water demand"""

    irr = load_file(irrfile, resolution, years, regrid_method='label', variables=[irrvar])[irrvar]

    region_masks = load_region_map(regionfile, masks=True, target_resolution=resolution)

    irr_grouped = irr.where(region_masks, 0)
    month_sums = irr_grouped.sum(dim=('lat', 'lon'))
    year_sums = month_sums.sum(dim='month').where(lambda x: x != 0, 1)  # avoid 0/0

    distribution = region_masks.dot(month_sums / year_sums, dims='region')

    return distribution
