from tethys.datareader.gridded import load_file
from tethys.datareader.maps import load_region_map


def temporal_distribution(years, resolution=None, regionfile=None, irrfile=None, irrvar='pirrww', bounds=None):
    """Temporal downscaling of irrigation water demand"""

    if hasattr(years, 'temporal_config'):
        model = years
        cfg = dict((model.temporal_config or {}).get('Irrigation', {}).get('kwargs', {}) or {})
        cfg.setdefault('bounds', model.bounds)
        return temporal_distribution(range(model.years[0], model.years[-1] + 1), model.resolution, **cfg)

    irr = load_file(irrfile, resolution, years, bounds=bounds, regrid_method='label', variables=[irrvar])[irrvar]

    region_masks = load_region_map(regionfile, masks=True, target_resolution=resolution, bounds=bounds)

    irr_grouped = irr.where(region_masks, 0)
    month_sums = irr_grouped.sum(dim=('lat', 'lon'))
    year_sums = month_sums.sum(dim='month').where(lambda x: x != 0, 1)  # avoid 0/0

    distribution = region_masks.dot(month_sums / year_sums, dims='region')

    return distribution
