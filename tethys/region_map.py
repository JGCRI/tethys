import numpy as np
from PIL import Image
from tethys.utils.data_parser import regrid


class RegionMap:

    def __init__(self, resolution: float, npzfile=None, mask=None):
        self.resolution = resolution
        self.nlat = round(180 / resolution)
        self.nlon = round(360 / resolution)
        self.map = None
        self.key = None
        self.mask = mask
        self.flatmap = None
        if npzfile is not None:
            self.load_npz(npzfile)
            self.extensify(n=2)
            self.flatten()

    def flatten(self):
        if self.mask is None:
            self.mask = self.map != 0
        self.flatmap = self.map[self.mask]

    def load_bil_map(self, filename):
        # hardcoded to work with the moirai bil files
        # really just here to help convert to npz so we can use that instead
        temp = np.fromfile(filename, dtype=np.float32).reshape(2160, 4320)
        temp[temp == -9999] = 0
        if temp.shape != (self.nlat, self.nlon):
            temp = regrid(temp, self.resolution, thematic=True)
        self.map = temp.astype(np.uint16)

    def load_csv_key(self, filename, skiprows=1):
        self.key = np.loadtxt(filename, dtype=[('name', 'U128'), ('id', np.uint16)], skiprows=skiprows, delimiter=',')

    def save_npz(self, filename):
        np.savez_compressed(filename, map=self.map, key=self.key)

    def load_npz(self, filename: str):
        """Load map and key from an npz file

        :param filename: path to npz file
        """

        data = np.load(filename)
        self.map = data['map']
        if self.map.shape != (self.nlat, self.nlon):
            self.map = regrid(self.map, self.resolution, thematic=True)
        self.key = data['key']

    def intersection(self, other):
        # assumes that regions are numbered 1 through n and sorted, and same land mask
        # here for complete workflow to region-basin map
        # redo with pandas at some point
        out = RegionMap(self.resolution)
        key, out.map = np.unique(np.stack((self.map, other.map)).reshape(2, -1), axis=1, return_inverse=True)
        out.map = out.map.reshape(out.nlat, out.nlon)
        out.key = np.zeros(key.shape[1] - 1, dtype=[('name', 'U128'), ('id', np.uint16)])
        out.key['id'] = np.arange(len(out.key)) + 1
        for i in range(len(out.key)):
            out.key['name'][i] = self.key['name'][key[0, i+1]-1] + '_' + other.key['name'][key[1, i+1]-1]
        return out

    def extensify(self, n=1):
        """Expand nonzero regions into cells without a region"""
        for i in range(n):
            for shift in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                self.map = np.where(self.map == 0, np.roll(self.map, shift, axis=(0, 1)), self.map)

    def filter(self, region=None, minid=0, maxid=65535):
        if region is not None:
            self.key = self.key[np.char.startswith(self.key['name'], region)]
        else:
            self.key = self.key[(self.key['id'] >= minid) & (self.key['id'] <= maxid)]
        for i in np.unique(self.map):
            if i not in self.key['id']:
                self.map[self.map == i] = 0

    def reindex(self):
        self.key.sort(order=['id'])
        _, self.map = np.unique(self.map, return_inverse=True)
        self.key['id'] = np.arange(len(self.key)) + 1

    def get_bounds(self):
        if self.mask is None:
            self.mask = self.map != 0
        indices = np.nonzero(self.mask)
        min_row, min_col = np.min(indices, axis=0)
        max_row, max_col = np.max(indices, axis=0)

        return self.mask[min_row:max_row + 1, min_col:max_col + 1]

    def show(self):
        temp = self.map.astype(np.float32)
        temp *= 255/temp.max()  # normalize to (0, 255)
        temp = temp.repeat(4, axis=0).repeat(4, axis=1)  # make higher res so windows photos app shows more detail
        Image.fromarray(temp.astype(np.uint8), 'L').show()
