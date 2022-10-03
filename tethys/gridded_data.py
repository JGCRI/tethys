import numpy as np
import netCDF4 as nc4
from PIL import Image

from tethys.utils.data_parser import regrid, load_tiff, load_nc, from_monthly_npz


class GriddedData:
    def __init__(self, subsectors, years, resolution, mask=None, files=None):
        self.subsectors = subsectors
        self.nsubsectors = len(subsectors)
        self.years = years
        self.nyears = len(years)
        self.resolution = resolution
        self.nlat = int(180 / resolution)
        self.nlon = int(360 / resolution)
        # ~4x memory savings by only storing land cells, mask helps convert back to lat lon array
        self.mask = np.full((self.nlat, self.nlon), True) if mask is None else mask
        self.nflat = np.count_nonzero(self.mask)
        self.flatarray = np.zeros((self.nsubsectors, self.nyears, self.nflat), dtype=np.float32)

        if files is not None:
            self.load(files)

    def load(self, files):
        """Load data as described by files

        files is of form {'subsector': {'years': {2010: 'path/to/subsector_2010.nc'}}}
        """
        for i, subsector in enumerate(self.subsectors):
            print(f'Loading Proxy Data for {subsector}')
            flags = files[subsector]['flags']
            # "round" down to earlier year if no exact match
            datayears = [max(y for y in files[subsector]['years'].keys()
                             if y <= year or y == min(files[subsector]['years'].keys()))
                         for year in self.years]
            for year, filename in files[subsector]['years'].items():
                if year in datayears:
                    temp = None
                    if filename.endswith('.tif'):
                        temp = load_tiff(filename)
                    elif filename.endswith('.nc'):
                        temp = load_nc(filename, subsector)
                    else:
                        print('CANT HANDLE THIS FILE TYPE')
                    if temp.shape != (self.nlat, self.nlon):
                        temp = regrid(temp, self.resolution, preserve_sum=flags != 'PCTAREA')
                    if flags == 'PCTAREA':
                        areas = np.cos(np.radians(np.arange(-90 + self.resolution/2, 90, self.resolution))) * \
                                (111.32 * 110.57) * self.resolution * self.resolution
                        temp *= areas.reshape(-1, 1)

                    self.flatarray[i, [j for j, y in enumerate(datayears) if y == year]] = temp[self.mask]

    def extract(self, subsectors, parts=None):
        """Create a new GriddedData object from combinations of existing subsectors"""
        if parts is None:
            parts = [[i] for i in subsectors]
        out = GriddedData(subsectors, self.years, self.resolution, self.mask)
        for i, subsector in enumerate(subsectors):
            for p in parts[i]:
                out.flatarray[i] += self.flatarray[self.subsectors.index(p)]
        return out

    def harmonize(self, regiondata):
        """Spatial downscaling really happens here"""

        axes = (0, 2) if regiondata.nsubsectors == 1 else 2  # keep susbectors separate, unless applying constraint to sum of sectors
        for i in range(len(regiondata.regionmap.key)):
            print(f'Downscaling {regiondata.regionmap.key["name"][i]}, {i} of {len(regiondata.regionmap.key)}')
            mask = np.equal(regiondata.regionmap.flatmap, regiondata.regionmap.key['id'][i])

            region_total = np.sum(self.flatarray, where=mask, axis=axes, keepdims=True)
            region_total[region_total == 0] = 1  # so we can treat 0/0 as 0

            scale = regiondata.array[:, i].reshape(-1, self.nyears, 1) / region_total
            np.multiply(self.flatarray, scale, out=self.flatarray, where=mask)

    def interp_annual(self):
        """Interpolate from 5-year (or whatever interval) to annual timesteps"""
        summed = self.flatarray.sum(axis=0)
        nyears = self.years[-1] - self.years[0] + 1  # include endpoints
        out = np.zeros((nyears, self.nflat), dtype=np.float32)
        for i in range(len(self.years) - 1):
            start = self.years[i] - self.years[0]
            end = self.years[i+1] - self.years[0]
            slope = (summed[i+1] - summed[i]) / (end - start)
            out[start:end] = summed[i] + slope * np.arange(end - start).reshape(-1, 1)
        out[-1] = summed[-1]
        return out.reshape(nyears, 1, self.nflat)

    def temp_irr(self, pirrww_file, regionmap):
        """Temporal downscaling of irrigation water demand"""
        self.temporal = from_monthly_npz(pirrww_file, 'pirrww', self.years[0], self.years[-1], self.resolution, self.mask)
        for i in range(len(regionmap.key)):
            mask = np.equal(regionmap.flatmap, regionmap.key['id'][i])
            if np.count_nonzero(mask) > 0:
                monthsums = np.sum(self.temporal, where=mask, axis=2, keepdims=True)
                yearsums = np.sum(monthsums, axis=1, keepdims=True)
                yearsums[yearsums == 0] = 1
                self.temporal[:, :, mask] = monthsums / yearsums
        self.temporal *= self.interp_annual()

    def temp_dom(self, tas_file, domr_file):
        """Temporal downscaling for domestic water demand using algorithm from Wada et al. (2011)"""
        self.temporal = from_monthly_npz(tas_file, 'tas', self.years[0], self.years[-1], self.resolution, self.mask)
        ranges = np.max(self.temporal, axis=1, keepdims=True) - np.min(self.temporal, axis=1, keepdims=True)
        ranges[ranges == 0] = 1
        self.temporal -= np.mean(self.temporal, axis=1, keepdims=True)
        self.temporal /= ranges
        domr = np.load(domr_file)['R']
        domr[domr == -9999] = 0
        domr = regrid(domr, self.resolution, thematic=True)[self.mask]
        self.temporal *= domr
        self.temporal += 1
        self.temporal /= 12
        self.temporal *= self.interp_annual()

    def temp_elec(self, temp_file, elec_weights):
        """Temporal downscaling of water demand for electricity generatin using algorithm from Voisin et al. (2013)"""
        hdd = from_monthly_npz(temp_file, 'hdd', self.years[0], self.years[-1], self.resolution, self.mask)
        cdd = from_monthly_npz(temp_file, 'cdd', self.years[0], self.years[-1], self.resolution, self.mask)
        hdd_sums = np.sum(hdd, axis=1, keepdims=True)
        cdd_sums = np.sum(cdd, axis=1, keepdims=True)
        hdd = np.where((hdd_sums < 650) & (cdd_sums >= 450), cdd, hdd)
        cdd = np.where((cdd_sums < 450) & (hdd_sums >= 650), hdd, cdd)
        hdd = np.where((hdd_sums < 650) & (cdd_sums < 450), 1/12, hdd)
        cdd = np.where((hdd_sums < 650) & (cdd_sums < 450), 1/12, cdd)
        hdd_sums = np.sum(hdd, axis=1, keepdims=True)
        cdd_sums = np.sum(cdd, axis=1, keepdims=True)
        hdd_sums[hdd_sums == 0] = 1
        cdd_sums[cdd_sums == 0] = 1
        hdd /= hdd_sums
        cdd /= cdd_sums

        self.temporal = np.full_like(hdd, 1/12, dtype=np.float32)
        weights = elec_weights.interp_annual()
        for i in range(len(elec_weights.regionmap.key)):
            mask = np.equal(elec_weights.regionmap.flatmap, elec_weights.regionmap.key['id'][i])
            hdd[:, :, mask] *= weights[0, i].reshape(-1, 1, 1)
            cdd[:, :, mask] *= weights[1, i].reshape(-1, 1, 1)
            self.temporal[:, :, mask] *= weights[2, i].reshape(-1, 1, 1)
        self.temporal += hdd
        self.temporal += cdd
        self.temporal *= self.interp_annual()

    def temp_uniform(self):
        """Divide demand evenly among months"""
        self.temporal = np.full((self.years[-1] - self.years[0] + 1, 12, self.nflat), 1/12, dtype=np.float32)
        self.temporal *= self.interp_annual()

    def unflatten(self, subsector, year):
        out = np.zeros((self.nlat, self.nlon), dtype=np.float32)
        if subsector == 'Total':
            out[self.mask] = self.flatarray.sum(axis=0)[self.years.index(year)]
        else:
            out[self.mask] = self.flatarray[self.subsectors.index(subsector), self.years.index(year)]
        return out

    def show(self, subsector='Total', year=None):
        """Show plot of subsector during year"""
        if year is None:
            year = self.years[0]
        temp = self.unflatten(subsector, year)
        m = np.max(temp)
        if m != 0:
            temp /= m  # normalize (0, 1)
        temp = np.sqrt(np.sqrt(temp))  # 4th root plots better (squishes large values)
        temp *= 255  # normalize to (0, 255)
        temp = temp.repeat(4, axis=0).repeat(4, axis=1)  # make higher res so windows photos app shows more detail
        Image.fromarray(temp.astype(np.uint8), 'L').show()  # show the image in system default viewer

    def save(self, filename):
        """Save array to NetCDF file"""

        datagrp = nc4.Dataset(filename, 'w')

        datagrp.createDimension('year', self.nyears)
        datagrp.createDimension('lat', self.nlat)
        datagrp.createDimension('lon', self.nlon)

        year = datagrp.createVariable('year', 'i4', ('year',))
        year.units = 'Year'
        lat = datagrp.createVariable('lat', 'f4', ('lat',))
        lon = datagrp.createVariable('lon', 'f4', ('lon',))
        demand = datagrp.createVariable('demand', 'f4', ('year', 'lat', 'lon'), compression='zlib')
        demand.units = 'km^3/year'

        year[:] = np.asarray(self.years)
        lat[:] = np.arange(-90 + self.resolution/2, 90, self.resolution)
        lon[:] = np.arange(-180 + self.resolution/2, 180, self.resolution)

        unflattened = np.full((self.nyears, self.nlat, self.nlon), np.nan, dtype=np.float32)
        unflattened[:, self.mask] = np.sum(self.flatarray, axis=0)
        demand[:] = unflattened

        datagrp.close()

    def save_temporal(self, filename):
        """Save array to NetCDF file"""

        datagrp = nc4.Dataset(filename, 'w')

        datagrp.createDimension('time', self.temporal.shape[0] * 12)
        datagrp.createDimension('lat', self.nlat)
        datagrp.createDimension('lon', self.nlon)

        year = datagrp.createVariable('year', 'i4', ('time',))
        month = datagrp.createVariable('month', 'i4', ('time',))
        lat = datagrp.createVariable('lat', 'f4', ('lat',))
        lon = datagrp.createVariable('lon', 'f4', ('lon',))
        data = datagrp.createVariable('value', 'f4', ('time', 'lat', 'lon'), compression='zlib')

        year[:] = np.arange(self.years[0], self.years[-1] + 1).repeat(12)
        month[:] = np.tile(np.arange(12), self.temporal.shape[0])
        lat[:] = np.arange(-90 + self.resolution/2, 90, self.resolution)
        lon[:] = np.arange(-180 + self.resolution/2, 180, self.resolution)

        unflattened = np.full((self.temporal.shape[0], 12, self.nlat, self.nlon), np.nan, dtype=np.float32)
        unflattened[:, :, self.mask] = self.temporal
        data[:] = unflattened.reshape(-1, self.nlat, self.nlon)

        datagrp.close()
