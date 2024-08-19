from tethys.datareader.gridded import load_file


def temporal_distribution(years, resolution, weightfile, weightvar='weight', regrid_method='intensive',
                          prenormalized=False, bounds=None):
    """Load a monthly distribution from filename"""

    distribution = load_file(weightfile, resolution, years, bounds=bounds, regrid_method=regrid_method,
                             variables=[weightvar])[weightvar]
    if prenormalized is False:
        distribution /= distribution.sum(dim='month').where(lambda x: x != 0, 1)

    return distribution
