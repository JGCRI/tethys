"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import os
os.environ['SPARSE_AUTO_DENSIFY'] = '1'  # so that outputs are written
import yaml
import xarray as xr

from tethys.utils.data_parser import load_proxies, load_regionmap, load_region_data, downscale


class Tethys:
    """Model wrapper for Tethys"""

    def __init__(self, cfg=None):
        self.config = None

        self.years = []
        self.resolution = 0.125
        self.sectors = []
        self.demand_types = ['withdrawals']
        self.perform_temporal = False

        self.gcam_db_path = None
        self.gcam_db_file = None
        self.query_file = None

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
        self.demand_types = project['demand_types']
        self.perform_temporal = project['perform_temporal']

        outputs = self.config['outputs']
        self.output_folder = outputs['folder']
        self.output_format = outputs['format']
        self.reduce_precision = outputs['reduce_precision'] if 'reduce_precision' in outputs else False

        self.regionmaps = xr.Dataset({k: load_regionmap(target_resolution=self.resolution, **v) for k, v in self.config['maps'].items()})

        # for parsing GCAM database
        if 'GCAM' in self.config:
            gcaminputs = self.config['GCAM']
            self.gcam_db_path = gcaminputs['gcam_db_path']
            self.gcam_db_file = gcaminputs['gcam_db_file']
            self.query_file = gcaminputs['query_file']

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

    def run_model(self):
        self.outputs = xr.Dataset()

        self.proxies = load_proxies(self.proxy_catalog, self.resolution, self.years)

        for sector in self.config['sectors']:
            if 'csv' in sector:
                df = load_region_data(csv=sector['csv'])
            elif 'query' in sector:
                df = load_region_data(gcam_db_path=self.gcam_db_path, gcam_db_file=self.gcam_db_file,
                                      query_file=self.query_file, query_title=sector['query'])
            else:
                pass  # TODO: errors

            sector['proxies'] = {k: [v] if isinstance(v, str) else v for k, v in sector['proxies'].items()}
            proxies = xr.Dataset({k: sum(self.proxies[i] for i in v) for k, v in sector['proxies'].items()})
            proxies = proxies.to_array(dim='sector')

            regions = self.regionmaps[sector['map']]

            self.outputs.update(downscale(df, proxies, regions).to_dataset(dim='sector'))
        self.outputs.to_netcdf(os.path.join(self.output_folder, 'tethys_outputs.nc'))
