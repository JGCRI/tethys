import xarray as xr
from tethys.temporal_downscaling import load_monthly_data


def monthly_distribution(self):
    """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""

    tas = load_monthly_data(self.temporal_files['tas'], self.resolution, range(self.years[0], self.years[-1] + 1))
    amplitude = load_monthly_data(self.temporal_files['domr'], self.resolution, method='label')

    ranges = tas.max(dim='month') - tas.min(dim='month')
    ranges = xr.where(ranges != 0, ranges, 1)  # avoid 0/0

    out = (((tas - tas.mean(dim='month')) / ranges) * amplitude + 1) / 12

    return out
