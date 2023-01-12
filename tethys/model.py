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
from tethys.spatial_proxies import load_proxy_file, interp_helper
from tethys.region_map import load_region_map
from tethys.temporal_downscaling import *


class Tethys:
    """Model wrapper for Tethys"""

    def __init__(self, config_file='', years=None, resolution=0.125, demand_type='withdrawals',
                 perform_temporal=False, dbpath=None, dbfile=None, csv=None, write_outputs=False, output_folder=None,
                 output_file=None, compress_outputs=True, downscaling_rules=None, proxy_files=None, map_files=None,
                 temporal_files=None):
        """ # TODO
        """

        self.root = os.path.dirname(config_file)

        # project level settings
        self.years = years
        self.resolution = resolution
        self.demand_type = demand_type
        self.perform_temporal = perform_temporal

        # GCAM database info
        self.dbpath = dbpath
        self.dbfile = dbfile

        # csv as alternative
        self.csv = csv

        # outputs
        self.write_outputs = write_outputs
        self.output_folder = output_folder
        self.output_file = output_file
        self.compress_outputs = compress_outputs

        self.downscaling_rules = downscaling_rules

        self.proxy_files = proxy_files
        self.map_files = map_files
        self.temporal_files = temporal_files

        # data we'll load or generate later
        self.region_masks = None
        self.proxies = None
        self.inputs = None
        self.outputs = None

        # settings in YAML override settings passed directly to __init__
        if config_file != '':
            with open(config_file) as file:
                config = yaml.safe_load(file)
            config = {k: v for k, v in config.items() if k in vars(self)}
            vars(self).update(config)

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
                      load_proxy_file(os.path.join(self.root, filename), self.resolution, **info).values()]

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
            self.inputs = load_region_data(os.path.join(self.root, self.dbpath), self.dbfile, sectors, self.demand_type)

    def harmonize(self, distribution, sectors=None):
        """Actual spatial downscaling happens here"""

        if sectors is None:
            sectors = distribution.sector.data
        elif isinstance(sectors, str):
            sectors = [sectors]

        inputs = self.inputs[(self.inputs.region.isin(self.region_masks.region.data)) &
                             (self.inputs.sector.isin(sectors)) &
                             (self.inputs.year.isin(self.years))].set_index(['region', 'sector', 'year'])[
            'value'].to_xarray().fillna(0).astype(np.float32)

        region_masks = self.region_masks.sel(region=inputs.region)

        out = distribution.where(region_masks, 0)

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
                                      (weights.region.isin(self.region_masks.region.data)) &
                                      (weights.year.isin(self.years))].set_index(
                        ['region', 'sector', 'year'])['value'].to_xarray().fillna(0)
                    weights = interp_helper(weights)
                    region_masks = self.region_masks.sel(region=weights.region)

                    distribution = monthly_distribution_electricty(hdd, cdd, weights, region_masks)

                elif supersector == 'Irrigation':
                    irr = load_monthly_data(self.temporal_files['irr'], self.resolution, range(self.years[0], self.years[-1] + 1), method='label')
                    irr_regions = self.inputs.region[(self.inputs.sector == 'Irrigation') &
                                                     (self.inputs.region.isin(self.region_masks.region.data))
                                                     ].unique()
                    regionmasks = self.region_masks.sel(region=irr_regions)
                    distribution = monthly_distribution_irrigation(irr, regionmasks)

                else:
                    distribution = xr.DataArray(np.full(12, 1/12, np.float32), coords=dict(month=range(12)))

                downscaled = interp_helper(downscaled) * distribution

            self.outputs.update(downscaled.to_dataset(dim='sector'))

        if self.write_outputs:
            print('Writing Outputs')
            if self.compress_outputs:
                # TODO: could give users more control over this? or tell them to use self.outputs directly?
                encoding = {variable: {'zlib': True, 'complevel': 5} for variable in self.outputs}
                self.outputs.to_netcdf(os.path.join(self.output_folder, self.output_file), encoding=encoding)
            else:
                self.outputs.to_netcdf(os.path.join(self.output_folder, self.output_file))
