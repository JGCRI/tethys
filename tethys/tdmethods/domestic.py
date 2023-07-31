import xarray as xr
from tethys.datareader.gridded import load_file


def temporal_distribution(years, resolution, tasfile, rfile, tasvar='tas', rvar='amplitude'):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    tas = load_file(tasfile, resolution, years, regrid_method='intensive', variables=[tasvar])[tasvar]
    amplitude = load_file(rfile, resolution, years, regrid_method='label', variables=[rvar])[rvar]

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    distribution = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return distribution
