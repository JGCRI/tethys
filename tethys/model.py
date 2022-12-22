"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import os
import yaml
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

        for sector in self.sectors:
            sector_config = self.config['sectors'][sector]

            regionmap = self.regionmaps[sector_config['map']]
            regions = list(regionmap.names)
            sectors = list(sector_config['proxies'])

            csv_file = sector_config['csv'] if 'csv' in sector_config else None
            query_title = sector_config['query'] if 'query' in sector_config else None
            basin_column = 'subsector' if sector == 'Irrigation' else None

            input_data = load_region_data(csv=csv_file, gcam_db_path=self.gcam_db_path, gcam_db_file=self.gcam_db_file,
                                          query_file=self.query_file, query_title=query_title, basin_column=basin_column,
                                          regions=regions, sectors=sectors, years=self.years)

            sector_config['proxies'] = {k: [v] if isinstance(v, str) else v for k, v in sector_config['proxies'].items()}
            proxies = xr.Dataset({k: sum(self.proxies[i] for i in v) for k, v in sector_config['proxies'].items()}).to_array(dim='sector')

            downscaled = downscale(input_data, proxies, regionmap)

            if 'total_map' in sector_config:
                total_regionmap = self.regionmaps[sector_config['total_map']]
                total_regions = list(total_regionmap.names)

                total_csv_file = sector_config['total_csv'] if 'csv' in sector_config else None
                total_query_title = sector_config['total_query'] if 'query' in sector_config else None

                total_basin_column = 'output' if sector == 'Irrigation' else None

                total_input_data = load_region_data(csv=total_csv_file, gcam_db_path=self.gcam_db_path, gcam_db_file=self.gcam_db_file,
                                              query_file=self.query_file, query_title=total_query_title, basin_column=total_basin_column,
                                              regions=total_regions, sectors=[sector], years=self.years)

                downscaled = downscale(total_input_data, downscaled, total_regionmap)

            if self.perform_temporal:
                # calculate the monthly distributions (share of annual) for each year
                if sector == 'Domestic':
                    tas = load_monthly_data(self.temporal_files['tas'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    amplitude = load_monthly_data(self.temporal_files['domr'], self.resolution, method='label')
                    distribution = monthly_distribution_domestic(tas, amplitude)

                elif sector == 'Electricity':
                    hdd = load_monthly_data(self.temporal_files['hdd'], self.resolution, range(self.years[0], self.years[-1] + 1))
                    cdd = load_monthly_data(self.temporal_files['cdd'], self.resolution, range(self.years[0], self.years[-1] + 1))

                    weights = load_region_data(gcam_db_path=self.gcam_db_path, gcam_db_file=self.gcam_db_file,
                                               query_file=self.query_file, query_title='elec consumption by demand sector',
                                               regions=regions, years=self.years, elec_weights=True)
                    weights = interp_sparse(weights)

                    distribution = monthly_distribution_electricty(hdd, cdd, weights, regionmap)

                elif sector == 'Irrigation':
                    irr = load_monthly_data(self.temporal_files['irr'], self.resolution, range(self.years[0], self.years[-1] + 1), method='label')
                    distribution = monthly_distribution_irrigation(irr, regionmap)

                else:
                    distribution = xr.DataArray(np.full(12, 1/12, np.float32), coords=dict(month=range(12)))

                # interpolate
                downscaled = interp_sparse(downscaled)
                downscaled = downscaled * distribution

            self.outputs.update(downscaled.to_dataset(dim='sector'))

        #self.outputs.to_netcdf(os.path.join(self.output_folder, 'tethys_outputs.nc'))


def downscale(input_data, proxies, regions):
    """Actual downscaling here

    :param input_data: xarray DataArray of region scale demand inputs, with dimensions 'region', 'sector', 'year'
    :param proxies: xarray DataArray giving distribution of demand, with dimensions 'sector', 'year', 'lat', 'lon'
    :param regions: xarray DataArray with labeled regions, dimensions 'lat', 'lon', and attribute names
    :return: out: xarray DataArray with dimensions 'sector', 'year', 'lat', 'lon'
    """

    out = proxies.where(region_masks(regions), 0)

    # take total of proxy sectors when input condition is for total
    dims = ('sector', 'lat', 'lon') if input_data.sector.size == 1 else ('lat', 'lon')

    sums = out.sum(dim=dims).where(lambda x: x != 0, 1)  # avoid 0/0

    out = out.dot(input_data / sums, dims='region')  # demand_cell = demand_region * (proxy_cell / proxy_region)

    return out
