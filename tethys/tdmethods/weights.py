from tethys.datareader.gridded import load_file


def temporal_distribution(years, resolution=None, weightfile=None, weightvar='weight', regrid_method='intensive',
                          prenormalized=False, bounds=None):
    """Load a monthly distribution from filename"""

    if hasattr(years, 'temporal_config'):
        model = years
        cfg = (model.temporal_config or {}).get('Weights', {}).get('kwargs', {})
        return temporal_distribution(range(model.years[0], model.years[-1] + 1),
                                     model.resolution, cfg.get('weightfile'), bounds=model.bounds)

    distribution = load_file(weightfile, resolution, years, bounds=bounds, regrid_method=regrid_method,
                             variables=[weightvar])[weightvar]
    if prenormalized is False:
        distribution /= distribution.sum(dim='month').where(lambda x: x != 0, 1)

    return distribution
