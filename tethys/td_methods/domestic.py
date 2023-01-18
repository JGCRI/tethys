import xarray as xr
from tethys.spatial_data import load_file


def monthly_distribution(self):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    years = range(self.years[0], self.years[-1] + 1)
    tas = load_file(self.temporal_files['tas'], self.resolution, years, regrid_method='label')['tas']
    amplitude = load_file(self.temporal_files['domr'], self.resolution, years, regrid_method='label')['amplitude']

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    out = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return out
