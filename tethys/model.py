"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import os
import importlib

import yaml
import numpy as np
import pandas as pd
import xarray as xr

from tethys.datareader.regional import load_region_data
from tethys.datareader.gridded import load_file, interp_helper
from tethys.datareader.maps import load_region_map


class Tethys:
    """Model wrapper for Tethys"""

    def __init__(
        self, 
        config_file=None, 
        years=None, 
        resolution=0.125, 
        demand_type='withdrawals',
        perform_temporal=False, 
        gcam_db=None, 
        csv=None, 
        output_file=None,
        downscaling_rules=None, 
        proxy_files=None, 
        map_files=None, 
        temporal_files=None, 
        temporal_methods=None
    ):
        """Parameters can be specified in a YAML file or passed directly, with the config file taking precedence

        :param config_file: path to YAML configuration file containing these parameters
        :param years: list of years to be included spatial downscaling
        :param resolution: resolution in degrees for spatial downscaling
        :param demand_type: choice between “withdrawals” (default) or “consumption”
        :param perform_temporal: choice between False (default) or True
        :param gcam_db: relative path to a GCAM database
        :param csv: relative path to csv file containing inputs
        :param output_file: name of file to write outputs to
        :param downscaling_rules: mapping from water demand sectors to proxy variables
        :param proxy_files: mapping of spatial proxy files to their years/variables
        :param map_files: list of files containing region maps
        :param temporal_files: mapping of sector to temporal downscaling method
        :param temporal_methods: files that will be accessible during temporal downscaling
        """
        self.root = None

        # project level settings
        self.years = years
        self.resolution = resolution
        self.demand_type = demand_type
        self.perform_temporal = perform_temporal

        # GCAM database info
        self.gcam_db = gcam_db

        # csv as alternative
        self.csv = csv

        # outputs
        self.output_file = output_file

        self.downscaling_rules = downscaling_rules

        self.proxy_files = proxy_files
        self.map_files = map_files
        self.temporal_files = temporal_files

        self.temporal_methods = temporal_methods

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

        if self.temporal_methods is None:
            self.temporal_methods = {
                'domestic': 'domestic',
                'municipal': 'domestic',
                'electricity': 'electricity',
                'irrigation': 'irrigation'
            }
        else:
            self.temporal_methods = {k.lower(): v for k, v in self.temporal_methods.items()}

        if self.temporal_files is not None:
            self.temporal_files = {k: os.path.join(self.root, v) for k, v in self.temporal_files.items()}

        if self.output_file is not None:
            self.output_file = os.path.join(self.root, self.output_file)

        self._parse_proxy_files()

    def _parse_proxy_files(self):
        """Handle several shorthand expressions in the proxy catalog"""
        out = dict()

        # name may be something like "ssp1_[YEAR].tif", which actually refers to multiple files
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
        dataarrays = [da for filename, info in self.proxy_files.items() for da in
                      load_file(os.path.join(self.root, filename), self.resolution, **info).values()]

        print('Interpolating Proxies')
        # interpolate each variable, then merge to one array
        self.proxies = xr.merge(interp_helper(xr.concat([da for da in dataarrays if da.name == variable], 'year'),
                                              self.years) for variable in set(da.name for da in dataarrays)).to_array()

    def _load_region_masks(self):
        self.region_masks = xr.concat([load_region_map(os.path.join(self.root, filename), masks=True,
                                                       target_resolution=self.resolution)
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
                {sector: self.proxies.sel(variable=proxy if isinstance(proxy, list) else [proxy]).sum('variable')
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

                    downscaled = self.downscale(downscaled, inputs_total, region_masks_total)

            if self.perform_temporal:
                # calculate the monthly distributions (share of annual) for each year

                # this is how we'll do this for now
                if supersector.lower() in self.temporal_methods:
                    module = f'tethys.tdmethods.{self.temporal_methods[supersector.lower()]}'
                    distribution = getattr(importlib.import_module(module), 'temporal_distribution')(self)
                else:
                    distribution = xr.DataArray(np.full(12, 1/12, np.float32), coords=dict(month=range(1, 13)))

                downscaled = interp_helper(downscaled) * distribution

            self.outputs.update(downscaled.to_dataset(dim='sector'))

        if self.output_file is not None:
            print('Writing Outputs')
            # cannot have '/' in netcdf variable name
            self.outputs = self.outputs.rename({name: name.replace('/', '_') for name in list(self.outputs)})
            # compression
            encoding = {variable: {'zlib': True, 'complevel': 5} for variable in self.outputs}
            self.outputs.to_netcdf(self.output_file, encoding=encoding)

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
