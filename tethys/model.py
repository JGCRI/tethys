"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import os
import yaml
from tethys.region_data import load_region_data, elec_sector_weights
from tethys.spatial_proxies import load_proxies, interp_helper
from tethys.region_map import load_regionmap, region_masks
from tethys.temporal_downscaling import *


class Tethys:
    """Model wrapper for Tethys"""

    def __init__(self, cfg=None):
        self.config = None

        self.years = []
        self.resolution = 0.125
        self.sectors = []
        self.demand_type = 'withdrawals'
        self.perform_temporal = False

        self.dbpath = None
        self.dbfile = None

        self.output_folder = None
        self.output_format = None
        self.reduce_precision = False

        self.regionmaps = None
        self.proxy_catalog = dict()
        self.proxies = None

        self.outputs = None

        if cfg is not None:
            self.load_config(cfg)

    def load_config(self, config_file):
        """Load model parameters from a config.yml"""
        with open(config_file) as file:
            self.config = yaml.safe_load(file)

        project = self.config['project']
        self.sectors = project['sectors']
        self.years = project['years']
        self.resolution = project['resolution']
        self.perform_temporal = project['perform_temporal']

        if self.perform_temporal:
            self.temporal_files = self.config['temporal']

        outputs = self.config['outputs']
        self.output_folder = outputs['folder']
        self.output_format = outputs['format']
        self.reduce_precision = outputs['reduce_precision'] if 'reduce_precision' in outputs else False

        self.regionmaps = xr.concat([region_masks(load_regionmap(target_resolution=self.resolution, mapfile=v))
                                     for v in self.config['maps']], dim='region')

        # for parsing GCAM database
        if 'GCAM' in self.config:
            gcaminputs = self.config['GCAM']
            self.dbpath = gcaminputs['dbpath']
            self.dbfile = gcaminputs['dbfile']

        self.rules = self.config['rules']

        # parse proxy files
        self.proxy_catalog = {}
        for proxy in self.config['proxies']:
            flags = proxy['flags'] if 'flags' in proxy else []
            for variable in proxy['variables']:

                abbreviation = proxy['variables'][variable] if isinstance(proxy['variables'], dict) else variable

                for year in proxy['years']:

                    name = proxy['name'].replace('[VAR]', abbreviation).replace('[YEAR]', str(year))
                    filepath = os.path.join(proxy['folder'], name)

                    if filepath not in self.proxy_catalog:
                        self.proxy_catalog[filepath] = {'variables': set(), 'years': set(), 'flags': flags}

                    self.proxy_catalog[filepath]['variables'].add(variable)
                    self.proxy_catalog[filepath]['years'].add(year)

    def harmonize(self, distribution, sectors=None):

        if sectors is None:
            sectors = distribution.sector.data
        elif isinstance(sectors, str):
            sectors = [sectors]

        inputs = self.inputs[(self.inputs.region.isin(self.regionmaps.region.data)) &
                             (self.inputs.sector.isin(sectors)) &
                             (self.inputs.year.isin(self.years))].set_index(['region', 'sector', 'year'])[
            'value'].to_xarray().fillna(0)
        regionmaps = self.regionmaps.sel(region=inputs.region)

        out = distribution.where(regionmaps, 0)

        # take total of proxy sectors when input condition is for total
        if inputs.sector.size == 1:
            dims = ('sector', 'lat', 'lon')
            inputs = inputs.squeeze(dim='sector', drop=True)
        else:
            dims = ('lat', 'lon')

        sums = out.sum(dim=dims).where(lambda x: x != 0, 1)  # avoid 0/0

        out = out.dot(inputs / sums, dims='region')  # demand_cell = demand_region * (proxy_cell / proxy_region)

        return out

    def run_model(self):
        self.outputs = xr.Dataset()

        self.proxies = load_proxies(self.proxy_catalog, self.resolution, self.years)
        self.inputs = load_region_data(self.dbpath, self.dbfile, self.rules, self.demand_type)

        for supersector, rules in self.rules.items():
            print(f'Downscaling {supersector}')
            if not isinstance(rules, dict):
                rules = {supersector: rules}

            proxies = xr.Dataset(
                {sector: self.proxies.sel(variable=proxy if isinstance(proxy, list) else [proxy]).sum('variable')
                 for sector, proxy in rules.items()}
            ).to_array(dim='sector')

            downscaled = self.harmonize(proxies)

            # handle constraint for entire supersector
            if supersector not in rules and supersector in self.inputs.sector.unique():
                if not set(self.inputs.region[self.inputs.sector.isin(downscaled.sector.data)]).issubset(
                        set(self.inputs.region[self.inputs.sector == supersector])):
                    downscaled = self.harmonize(downscaled, supersector)

            if self.perform_temporal:
                # calculate the monthly distributions (share of annual) for each year
                if supersector == 'Domestic' or supersector == 'Municipal':
                    tas = load_monthly_data(self.temporal_files['tas'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    amplitude = load_monthly_data(self.temporal_files['domr'], self.resolution, method='label')
                    distribution = monthly_distribution_domestic(tas, amplitude)

                elif supersector == 'Electricity':
                    hdd = load_monthly_data(self.temporal_files['hdd'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    cdd = load_monthly_data(self.temporal_files['cdd'], self.resolution, range(self.years[0], self.years[-1] + 1))

                    weights = elec_sector_weights(self.dbpath, self.dbfile)
                    weights = weights[(weights.region.isin(self.inputs.region[self.inputs.sector == 'Electricity'])) &
                                      (weights.region.isin(self.regionmaps.region.data)) &
                                      (weights.year.isin(self.years))].set_index(
                        ['region', 'sector', 'year'])['value'].to_xarray().fillna(0)
                    weights = interp_helper(weights)
                    regionmasks = self.regionmaps.sel(region=weights.region)

                    distribution = monthly_distribution_electricty(hdd, cdd, weights, regionmasks)

                elif supersector == 'Irrigation':
                    irr = load_monthly_data(self.temporal_files['irr'], self.resolution, range(self.years[0], self.years[-1] + 1), method='label')
                    irr_regions = self.inputs.region[(self.inputs.sector == 'Irrigation') &
                                                     (self.inputs.region.isin(self.regionmaps.region.data))
                                                     ].unique()
                    regionmasks = self.regionmaps.sel(region=irr_regions)
                    distribution = monthly_distribution_irrigation(irr, regionmasks)

                else:
                    distribution = xr.DataArray(np.full(12, 1/12, np.float32), coords=dict(month=range(12)))

                downscaled = interp_helper(downscaled) * distribution

            self.outputs.update(downscaled.to_dataset(dim='sector'))

        #self.outputs.to_netcdf(os.path.join(self.output_folder, 'tethys_outputs.nc'))
