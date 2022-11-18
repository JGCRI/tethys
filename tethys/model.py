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
from tethys.region_data import load_region_data
from tethys.spatial_proxies import load_proxies, interp_sparse
from tethys.region_map import load_regionmap
from tethys.temporal_downscaling import *


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

        if self.perform_temporal:
            self.temporal_files = self.config['temporal']

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

            downscaled = downscale(df, proxies, regions)

            if self.perform_temporal:
                # calculate the monthly distributions (share of annual) for each year
                if sector['name'] == 'Domestic':
                    tas = load_monthly_data(self.temporal_files['tas'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    amplitude = load_monthly_data(self.temporal_files['domr'], self.resolution, method='label')
                    distribution = monthly_distribution_domestic(tas, amplitude)

                elif sector['name'] == 'Electricity':
                    hdd = load_monthly_data(self.temporal_files['hdd'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    cdd = load_monthly_data(self.temporal_files['cdd'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    weights = load_region_data(gcam_db_path=self.gcam_db_path, gcam_db_file=self.gcam_db_file,
                                               query_file=self.query_file, query_title='elec consumption by demand sector')
                    distribution = monthly_distribution_electricty(hdd, cdd, weights, regions)

                elif sector['name'] == 'Irrigation':
                    irr = load_monthly_data(self.temporal_files['irr'], self.resolution, range(self.years[0], self.years[-1] + 1), method='label')
                    distribution = monthly_distribution_irrigation(irr, regions)

                else:
                    distribution = xr.DataArray(np.full(12, 1/12, np.float32), coords=dict(month=range(12)))

                # interpolate
                downscaled = interp_sparse(downscaled)
                downscaled = downscaled * distribution

            self.outputs.update(downscaled.to_dataset(dim='sector'))

        #self.outputs.to_netcdf(os.path.join(self.output_folder, 'tethys_outputs.nc'))


def downscale(df, proxies, regions):
    """Actual downscaling here

    :param df: pandas dataframe of region scale demand inputs, with columns 'region', 'sector', 'year', 'value'
    :param proxies: xarray DataArray giving distribution of demand, with dimensions 'sector', 'year', 'lat', 'lon'
    :param regions: xarray DataArray with labeled regions, dimensions 'lat', 'lon', and attribute names
    :return: out: xarray DataArray with dimensions 'sector', 'year', 'lat', 'lon'
    """
    regionids = pd.Series(regions.names, name='regionid').astype(int).sort_index().rename_axis('region').to_xarray()

    index = pd.MultiIndex.from_product([regionids.region.to_series(), proxies.sector.to_series(), proxies.year.to_series()])
    input_data = df.set_index(['region', 'sector', 'year']).reindex(index, fill_value=0)['value'].to_xarray()

    # groupby was slow so we do this hack with sparse arrays
    # multiply the proxy by a bool array region mask to group, then operate on each layer
    groups = regions == regionids
    out = proxies * groups

    sums = out.sum(dim=('lat', 'lon'))
    sums = xr.where(sums != 0, sums, 1)  # avoid 0/0

    out *= input_data / sums  # demand_cell = demand_region * (proxy_cell / proxy_region), but calculate efficiently

    out = out.sum(dim='region')

    return out
