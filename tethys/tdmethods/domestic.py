import xarray as xr
from tethys.datareader.gridded import load_file


def temporal_distribution(model):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    years = range(model.years[0], model.years[-1] + 1)
    tas = load_file(model.temporal_files['tas'], model.resolution, years, regrid_method='intensive')['tas']
    amplitude = load_file(model.temporal_files['domr'], model.resolution, years, regrid_method='label')['amplitude']

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    distribution = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return distribution
