"""
@Date: 09/20/2022
@author: Isaac Thompson (isaac.thompson@pnnl.gov)
@Project: Tethys V2.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2022, Battelle Memorial Institute

"""
import os
from configobj import ConfigObj

import gcamreader

from tethys.region_data import RegionData
from tethys.region_map import RegionMap
from tethys.gridded_data import GriddedData


class Tethys:
    """Model wrapper for Tethys"""

    def __init__(self, cfg=None):
        self.resolution = 0.125
        self.nlat = round(180 / self.resolution)
        self.nlon = round(360 / self.resolution)
        self.years = []
        self.nyears = len(self.years)
        self.demand_types = []
        self.sectors = []
        self.gcam_db_path = None
        self.gcam_db_file = None
        self.query_file = None
        self.gcam_usa = False
        self.regionmaps = dict()
        self.regiondata = dict()
        self.proxies = None
        self.outputs = dict()
        if cfg is not None:
            self.load_config(cfg)

    def load_config(self, config_file):
        """Load model parameters from a config.ini"""
        self.config = ConfigObj(config_file)

        project = self.config.get('Project')
        self.outputfolder = project.get('OutputFolder')
        self.sectors = project.get('Sectors', ['Domestic', 'Electricity', 'Manufacturing', 'Mining', 'Livestock', 'Irrigation'])
        if isinstance(self.sectors, str):
            self.sectors = [self.sectors]
        self.resolution = float(project.get('Resolution', 0.125))
        self.nlat = round(180 / self.resolution)
        self.nlon = round(360 / self.resolution)
        self.years = project.get('Years', range(2010, 2101, 5))
        if isinstance(self.years, str):
            self.years = [self.years]
        self.years = [int(year) for year in self.years]
        self.nyears = len(self.years)
        self.demand_types = project.get('DemandTypes', 'Withdrawals')
        if isinstance(self.demand_types, str):
            self.demand_types = [self.demand_types]
        self.perform_temporal = int(project.get('PerformTemporal', 0))

        # names and paths to region npz files
        self.mapfiles = self.config.get('RegionMaps').items()

        # parse proxy files
        self.proxyfiles = {}
        for sectionname in self.config.sections:
            if sectionname.startswith('Proxy'):
                section = self.config.get(sectionname)
                folder = section.get('Folder')
                subsectors = section.get('Subsectors', None)
                years = section.get('Years', None)
                flags = section.get('Flags', None)
                for key, value in section.items():
                    if key not in ('Folder', 'Subsectors', 'Years', 'Flags'):
                        proxy, year = key.split('_')
                        if proxy != 'Subsectors':  # reserve this as keyword for files with multiple proxies (demeter)
                            subsectors = [proxy]
                        if year != 'Years':
                            years = [year]
                        for subsector in subsectors:
                            if subsector not in self.proxyfiles:
                                self.proxyfiles[subsector] = {'flags': flags, 'years': {}}
                            for y in years:
                                self.proxyfiles[subsector]['years'][int(y)] = \
                                    os.path.join(folder, value.replace('YYYY', y))

        # for parsing GCAM database
        gcaminputs = self.config.get('GCAMInputs')
        self.csv_file = gcaminputs.get('CSV_file', None)
        self.gcam_db_path = gcaminputs.get('GCAM_DBpath', None)
        self.gcam_db_file = gcaminputs.get('GCAM_DBfile', None)
        self.query_file = gcaminputs.get('QueryFile', None)
        self.gcam_usa = True if gcaminputs.get('GCAMUSA', 'False') == 'True' else False

        # parse rules related to spatial proxies
        self.rules = {}
        for sector in self.sectors:
            self.rules[sector] = {}
            section = self.config.get(sector)
            self.rules[sector]['subsectors'] = section.get('Subsectors', [sector])
            self.rules[sector]['parts'] = []
            for subsector in self.rules[sector]['subsectors']:
                parts = section.get(subsector)
                if isinstance(parts, str):
                    parts = [parts]
                self.rules[sector]['parts'].append(parts)

            self.rules[sector]['map1'] = section.get('Map1', self.mapfiles[0][0])
            self.rules[sector]['map2'] = section.get('Map2', None)

            self.rules[sector]['query1'] = section.get('Query1', None)
            self.rules[sector]['query2'] = section.get('Query2', None)

        if self.perform_temporal:
            temporal_params = self.config.get('Temporal')
            folder = temporal_params.get('Folder')
            self.irr_file = os.path.join(folder, temporal_params.get('pirrww_file', ''))
            self.temp_file = os.path.join(folder, temporal_params.get('temp_file', ''))
            self.domr_file = os.path.join(folder, temporal_params.get('DomesticR', ''))

    def load_maps(self):
        self.regionmaps = {}
        for mapname, filename in self.mapfiles:
            self.regionmaps[mapname] = RegionMap(self.resolution, filename)

    def load_proxies(self):
        mask = self.regionmaps[self.mapfiles[0][0]].mask
        self.proxies = GriddedData(list(self.proxyfiles.keys()), self.years, self.resolution, mask, self.proxyfiles)

    def load_regiondata(self):
        queries = {i.title: i for i in gcamreader.parse_batch_query(self.query_file)}
        self.regiondata = {}
        conn = None
        if self.gcam_db_path is not None:
            conn = gcamreader.LocalDBConn(self.gcam_db_path, self.gcam_db_file, suppress_gabble=False)
        for sector in self.sectors:
            self.regiondata[sector] = {}
            subsectors = self.rules[sector]['subsectors']
            for demand in self.demand_types:
                print(f'Loading Region Data for {sector} Water {demand}')
                regionmap = self.regionmaps[self.rules[sector]['map1']]
                query = queries[self.rules[sector]['query1'].replace('Demand', demand)]
                self.regiondata[sector][demand] = {'data1': RegionData(sector, subsectors, regionmap, self.years, conn, query, self.csv_file)}
                if self.rules[sector]['query2'] is not None:
                    regionmap = self.regionmaps[self.rules[sector]['map2']]
                    query = queries[self.rules[sector]['query2'].replace('Demand', demand)]
                    self.regiondata[sector][demand]['data2'] = RegionData(sector, [sector], regionmap, self.years, conn, query, self.csv_file)
        # weights for temporal downscaling of electricity
        if self.perform_temporal and 'Electricity' in self.sectors:
            subsectors = ('Heating', 'Cooling', 'Other')
            regionmap = self.regionmaps['Regions']
            query = queries['elec consumption by demand sector']
            self.elecdemand = RegionData('elecdemand', subsectors, regionmap, self.years, conn, query)
            self.elecdemand.subsector_ratio()

    def downscale(self, sector, demand):
        print(f'Downscaling {sector} water {demand}')
        self.outputs[sector][demand] = self.proxies.extract(self.rules[sector]['subsectors'], self.rules[sector]['parts'])
        self.outputs[sector][demand].harmonize(self.regiondata[sector][demand]['data1'])
        if 'data2' in self.regiondata[sector][demand]:
            self.outputs[sector][demand].harmonize(self.regiondata[sector][demand]['data2'])

    def run_model(self):
        self.load_maps()
        self.load_proxies()
        self.load_regiondata()
        for sector in self.sectors:
            self.outputs[sector] = {}
            for demand in self.demand_types:
                self.downscale(sector, demand)
        if self.perform_temporal:
            for demand in self.demand_types:
                if 'Domestic' in self.sectors:
                    self.outputs['Domestic'][demand].temp_dom(self.temp_file, self.domr_file)
                if 'Electricity' in self.sectors:
                    self.outputs['Electricity'][demand].temp_elec(self.temp_file, self.elecdemand)
                if 'Irrigation' in self.sectors:
                    regionmap = self.regionmaps[self.rules['Irrigation']['map1']]
                    self.outputs['Irrigation'][demand].temp_irr(self.irr_file, regionmap)
                if 'Manufacturing' in self.sectors:
                    self.outputs['Manufacturing'][demand].temp_uniform()
                if 'Mining' in self.sectors:
                    self.outputs['Mining'][demand].temp_uniform()
                if 'Livestock' in self.sectors:
                    self.outputs['Livestock'][demand].temp_uniform()
        # save outputs
        for sector in self.sectors:
            for demand in self.demand_types:
                filename = os.path.join(self.outputfolder, f'{sector}{demand}.nc')
                self.outputs[sector][demand].save(filename)
                if self.perform_temporal:
                    filename = os.path.join(self.outputfolder, f'{sector}{demand}Temporal.nc')
                    self.outputs[sector][demand].save_temporal(filename)
