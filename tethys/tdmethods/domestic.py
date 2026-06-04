import xarray as xr
from tethys.datareader.gridded import load_file


def temporal_distribution(years, resolution=None, tasfile=None, rfile=None, tasvar='tas', rvar='amplitude', bounds=None):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    if hasattr(years, 'temporal_config'):
        model = years
        cfg = (model.temporal_config or {}).get('Municipal', {}).get('kwargs', {})
        return temporal_distribution(range(model.years[0], model.years[-1] + 1),
                                     model.resolution, cfg.get('tasfile'), cfg.get('rfile'),
                                     bounds=model.bounds)

    tas = load_file(tasfile, resolution, years, bounds=bounds, regrid_method='intensive', variables=[tasvar])[tasvar]
    amplitude = load_file(rfile, resolution, years, bounds=bounds, regrid_method='label', variables=[rvar])[rvar]

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    distribution = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return distribution
