import numpy as np
import pandas as pd


class RegionData:
    def __init__(self, subsectors, regionmap, years, conn=None, query=None):
        self.subsectors = subsectors
        self.nsubsectors = len(self.subsectors)
        self.regionmap = regionmap
        self.regions = list(self.regionmap.key['name'])
        self.nregions = len(self.regions)
        self.years = years
        self.nyears = len(self.years)
        self.array = None
        if query is not None:
            self.from_db(conn, query)

    def from_db(self, conn, query):
        df = conn.runQuery(query)
        if 'Irrigation' in query.title:  # make region names of the form region_basin
            df['region'] += '_' + df.iloc[:, 5].apply(lambda x: x.split('_')[-2])  # column 5 is input/output
        elif query.title == 'elec consumption by demand sector':
            df['sector'] = df['sector'].map(elec_sector)
        if len(self.subsectors) == 1:  # lets us prettify single sector names and force GCAMUSA names
            df['sector'] = self.subsectors[0]
        pivot = pd.pivot_table(df, values='value', index=['sector', 'region'], columns='Year', fill_value=0, aggfunc=np.sum)
        pivot = pivot.reindex(index=pd.MultiIndex.from_product([self.subsectors, self.regions]), columns=self.years, fill_value=0)
        self.array = pivot.to_numpy().reshape(self.nsubsectors, self.nregions, self.nyears)

    def subsector_ratio(self):
        """Set subsector values to fraction of total"""
        sums = self.array.sum(axis=0, keepdims=True)
        sums[sums == 0] = 1
        self.array /= sums

    def interp_annual(self):
        """Convert from 5-year time steps to annual"""
        nyears = self.years[-1] - self.years[0] + 1  # include endpoints
        out = np.zeros((self.nsubsectors, self.nregions, nyears), dtype=np.float32)
        for i in range(len(self.years) - 1):
            start = self.years[i] - self.years[0]
            end = self.years[i + 1] - self.years[0]
            slope = (self.array[:, :, i + 1] - self.array[:, :, i]) / (end - start)
            out[:, :, start:end] = self.array[:, :, i, np.newaxis] + slope[:, :, np.newaxis] * np.arange(end - start)
        out[:, :, -1] = self.array[:, :, -1]
        return out


def elec_sector(x):
    """Helper for electricity demand sectors"""
    if x in ('comm heating', 'resid heating', 'comm hot water', 'resid furnace fans', 'resid hot water'):
        return 'Heating'
    elif x in ('comm cooling', 'resid cooling', 'comm refrigeration', 'resid freezers', 'resid refrigerators'):
        return 'Cooling'
    else:
        return 'Other'
