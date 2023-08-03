"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import os
import yaml
import importlib
import numpy as np
import pandas as pd
import xarray as xr
from tethys.datareader.regional import load_region_data
from tethys.datareader.gridded import load_file, interp_helper
from tethys.datareader.maps import load_region_map


class Tethys:
    """Model wrapper for Tethys"""

    def __init__(self, config_file=None, years=None, resolution=0.125, bounds=None, demand_type='withdrawals',
                 gcam_db=None, csv=None, output_dir=None, supersector_iterations=0,
                 downscaling_rules=None, proxy_files=None, map_files=None, temporal_config=None):
        """Parameters can be specified in a YAML file or passed directly, with the config file taking precedence

        :param config_file: path to YAML configuration file containing these parameters
        :param years: list of years to be included spatial downscaling
        :param resolution: resolution in degrees for spatial downscaling
        :param bounds: list [lat_min, lat_max, lon_min, lon_max] to crop to
        :param demand_type: choice between “withdrawals” (default) or “consumption”
        :param gcam_db: relative path to a GCAM database
        :param csv: relative path to csv file containing inputs
        :param output_dir: directory to write outputs to
        :param supersector_iterations: number of times to repeat applying individual and total sector constraints, default 0
        :param downscaling_rules: mapping from water demand sectors to proxy variables
        :param proxy_files: mapping of spatial proxy files to their years/variables
        :param map_files: list of files containing region maps
        :param temporal_config: mapping of sector to temporal downscaling method and arguments
        """

        self.root = None

        # project level settings
        self.years = years
        self.resolution = resolution
        self.bounds = bounds
        self.demand_type = demand_type

        # GCAM database info
        self.gcam_db = gcam_db

        # csv as alternative
        self.csv = csv

        # outputs
        self.output_dir = output_dir

        self.downscaling_rules = downscaling_rules
        self.supersector_iterations = supersector_iterations

        self.proxy_files = proxy_files
        self.map_files = map_files

        self.temporal_config = temporal_config

        # data we'll load or generate later
        self.region_masks = None
        self.proxies = None
        self.inputs = None
        self.outputs = None

        # settings in YAML override settings passed directly to __init__
        if config_file is not None:
            with open(config_file) as file:
                config = yaml.safe_load(file)
            config = {k: v for k, v in config.items() if k in vars(self)}
            vars(self).update(config)

        if self.root is None:
            if config_file is not None:
                self.root = os.path.dirname(config_file)
            else:
                self.root = os.getcwd()

        if self.output_dir is not None:
            self.output_dir = os.path.join(self.root, self.output_dir)

        self._parse_proxy_files()

    def _parse_proxy_files(self):
        """Handle several shorthand expressions in the proxy catalog"""
        out = dict()

        # name may be something like "ssp1_{YEAR}.tif", which actually refers to multiple files
        # such as "ssp1_2010.tif" and "ssp1_2020.tif" when info['years'] == [2010, 2020]
        for name, info in self.proxy_files.items():
            # promote strs to list
            if isinstance(info['variables'], str):
                info['variables'] = [info['variables']]

            if isinstance(info['years'], int):
                info['years'] = [info['years']]

            # flags are optional
            if 'flags' in info:
                if isinstance(info['flags'], str):
                    info['flags'] = [info['flags']]
            else:
                info['flags'] = []

            for variable in info['variables']:

                # file name may use an abbreviation of the variable name
                # if info['variables'] is a dict of form {variable: abbreviation}
                abbreviation = info['variables'][variable] if isinstance(info['variables'], dict) else variable

                for year in info['years']:
                    # determine the actual name of the file containing variable variable for year year
                    filename = name.replace('{variable}', abbreviation).replace('{year}', str(year))

                    if filename not in out:
                        out[filename] = {'variables': [], 'years': [], 'flags': info['flags']}

                    if variable not in out[filename]['variables']:
                        out[filename]['variables'].append(variable)
                    if year not in out[filename]['years']:
                        out[filename]['years'].append(year)

        self.proxy_files = out

    def _load_proxies(self):
        """Load all proxies from the catalog, regrid to target spatial resolution, and interpolate to target years"""
        print('Loading Proxy Data')
        # align each variable spatially
        dataarrays = [da for filename, info in self.proxy_files.items() for da in load_file(
            os.path.join(self.root, filename), self.resolution, bounds=self.bounds, **info).values()]

        print('Interpolating Proxies')
        # interpolate each variable, then merge to one array
        self.proxies = xr.merge(interp_helper(xr.concat([da for da in dataarrays if da.name == variable], 'year', coords='minimal'),
                                              self.years) for variable in set(da.name for da in dataarrays)).to_array()

    def _load_region_masks(self):
        self.region_masks = xr.concat([load_region_map(os.path.join(self.root, filename), masks=True,
                                                       target_resolution=self.resolution, bounds=self.bounds)
                                       for filename in self.map_files], dim='region')

    def _load_inputs(self):
        if self.csv is not None:
            self.inputs = pd.read_csv(os.path.join(self.root, self.csv))
        else:
            sectors = [j for i in self.downscaling_rules.values() if isinstance(i, dict) for j in i] + \
                      list(self.downscaling_rules.keys())
            self.inputs = load_region_data(os.path.join(self.root, self.gcam_db), sectors, self.demand_type)

        # filter inputs to valid regions and years
        self.inputs = self.inputs[(self.inputs.region.isin(self.region_masks.region.data)) &
                                  (self.inputs.year.isin(self.years))]
        # replace "/" with "_" because it causes problems with netcdf variable names
        self.inputs['sector'] = self.inputs.sector.str.replace('/', '_')

    def downscale(self, distribution, inputs, region_masks):
        """Actual spatial downscaling happens here

        :param distribution: DataArray (sector, year, lat, lon) spatial distribution of proxies
        :param inputs: DataArray (region, sector, year) demand values by region, sector, year
        :param region_masks: DataArray (lat, lon, region) of bools, True if (lat, lon) belongs to region
        :return: distribution scaled to match inputs in all regions
        """

        # take total of proxy sectors when input condition is for total
        if inputs.sector.size == 1:
            dims = ('sector', 'lat', 'lon')
            inputs = inputs.squeeze(dim='sector', drop=True)
        else:
            dims = ('lat', 'lon')

        out = distribution.where(region_masks, 0)
        sums = out.sum(dim=dims).where(lambda x: x != 0, 1)  # avoid 0/0
        out = xr.dot(out, inputs / sums, dims='region')  # demand_cell = demand_region * (proxy_cell / proxy_region)

        return out

    def run_model(self):
        self.outputs = xr.Dataset()

        self._load_proxies()
        self._load_region_masks()
        self._load_inputs()

        for supersector, rules in self.downscaling_rules.items():

            print(f'Downscaling {supersector}')

            if not isinstance(rules, dict):
                rules = {supersector: rules}

            proxies = xr.Dataset(
                {sector.replace('/', '_'):
                    self.proxies.sel(variable=proxy if isinstance(proxy, list) else [proxy]).sum('variable')
                 for sector, proxy in rules.items()}
            ).to_array(dim='sector')

            inputs = self.inputs[self.inputs.sector.isin(proxies.sector.data)].groupby(
                ['region', 'sector', 'year'])['value'].sum().to_xarray().fillna(0).astype(np.float32)

            region_masks = self.region_masks.sel(region=inputs.region)

            downscaled = self.downscale(proxies, inputs, region_masks)

            # handle constraint for entire supersector
            if supersector not in rules and supersector in self.inputs.sector.unique():
                # detect if supersector uses different regions than the sectors, or is just the total
                if not set(self.inputs.region[self.inputs.sector == supersector]).issubset(
                        set(self.inputs.region[self.inputs.sector.isin(downscaled.sector.data)])):

                    inputs_total = self.inputs[self.inputs.sector == supersector].set_index(
                        ['region', 'sector', 'year'])['value'].to_xarray().fillna(0).astype(np.float32)

                    region_masks_total = self.region_masks.sel(region=inputs_total.region)

                    # alternate between applying total and individual sector constraints so that both are met
                    for i in range(self.supersector_iterations):
                        downscaled = self.downscale(downscaled, inputs_total, region_masks_total)
                        downscaled = self.downscale(downscaled, inputs, region_masks)

                    # in a lot of cases this could be optimized by solving the intersections at region scale first,
                    # then downscaling once, but harder to implement, especially if differing regions are not subsets

            # write spatial downscaling outputs
            if self.output_dir is not None:
                filename = os.path.join(self.output_dir, f'{supersector}_{self.demand_type}.nc')
                encoding = {sector: {'zlib': True, 'complevel': 5} for sector in downscaled.sector.data}
                downscaled.to_dataset(dim='sector').to_netcdf(filename, encoding=encoding)
                downscaled = xr.open_dataset(filename).to_array(dim='sector')  # hopefully this keeps dask happy

            if self.temporal_config is not None:
                # calculate the monthly distributions (share of annual) for each year

                # this is how we'll do this for now
                if supersector in self.temporal_config:
                    module = f'tethys.tdmethods.' + self.temporal_config[supersector]['method']
                    temporal_distribution = getattr(importlib.import_module(module), 'temporal_distribution')
                    years = range(self.years[0], self.years[-1] + 1)
                    kwargs = self.temporal_config[supersector]['kwargs']
                    distribution = temporal_distribution(years=years, resolution=self.resolution,
                                                         bounds=self.bounds, **kwargs)
                else:
                    # fall back to uniform distribution
                    distribution = xr.DataArray(np.full(12, 1/12, np.float32), coords=dict(month=range(1, 13)))

                downscaled = interp_helper(downscaled) * distribution

                # write temporal downscaling outputs
                if self.output_dir is not None:
                    filename = os.path.join(self.output_dir, f'{supersector}_{self.demand_type}_monthly.nc')
                    encoding = {sector: {'zlib': True, 'complevel': 5} for sector in downscaled.sector.data}
                    downscaled.to_dataset(dim='sector').to_netcdf(filename, encoding=encoding)
                    downscaled = xr.open_dataset(filename).to_array(dim='sector')  # hopefully this keeps dask happy

            self.outputs.update(downscaled.to_dataset(dim='sector'))

    def reaggregate(self, region_masks=None):
        """Reaggregate from grid cells to regions

        :param region_masks: boolean mask of regions, if other than the input regions
        :return: dataframe with columns region, sector, year, value
        """
        if region_masks is None:
            region_masks = self.region_masks

        da = self.outputs.where(region_masks, 0).sum(dim=('lat', 'lon'))
        df = da.to_dataframe().drop(columns=['spatial_ref'])

        return df


def run_model(config_file):
    """Run a Tethys configuration"""
    config_file = os.path.join(os.getcwd(), config_file)
    result = Tethys(config_file=config_file)
    result.run_model()
    return result
