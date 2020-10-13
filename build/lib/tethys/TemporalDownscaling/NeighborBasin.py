"""
@Date: 09/09/2017
@author: Xinya Li (xinya.li@pnl.gov)
@Project: Tethys V1.0

License:  BSD 2-Clause, see LICENSE and DISCLAIMER files
Copyright (c) 2017, Battelle Memorial Institute


Modified from class NearDistValue @author: ladmin

"""

class NeighborBasin(object):
    '''
    This is a class to define the neighbor basin for a certain basin (in 235 basins) in Temporal Downscaling.
    
    The three studies (H08, LPJml, PCR-globwb) from year 1971-2010 were investigated for the following situation: 
    1. The aggregated basin-level spatially downscaled irrigation results have values, but no values in the three data sets.
    2. The monthly data profile from neighbor basin is borrowed to temporally downscale the grids related to this basin.
    
    The neighbor basin is chosen from the neighbor basins with the shortest distance to the target basin.
    
    dist.csv file in "reference" package includes the information of the distances of the surrounding basins to the target basin.

    '''


    def __init__(self, in_file):
        # Read dist.csv in
        self.f = in_file
        self.d = {}
        self.d_all = {}
        self.distance = 0.0
        self.build_dist_dict()

        
    def build_dist_dict(self):
        '''
        Read distance information from file for each target basin (235 basins).  
        Add the values for each corresponding neighbor basin with the least distance to the target basin to a dictionary.
        If multiple corresponding basins have the same distance, add all their IDs.
        
        @params: in_file        CSV file containing ordered fields from, to, 
                                distance, and value
        
        RETURNS: dictionary d     Format:  {target: [distance, near1, near2, near3 ...]}
        '''
        with open(self.f) as get:            
            for index, line in enumerate(get):
                # skip header
                if index == 0:
                    continue                 
                # unpack values
                f, t, dst, vl = line.strip().split(',')  # target basin ID, neighbor basin ID, distance, index in the table    
                dist = float(dst)              
                # skip self match or basins with no values
                if f == t:
                    continue              
                else:                    
                    # if a t and dist are not in dict
                    if f not in self.d:                        
                        self.d[f] = [dist, int(t)]
                        self.d_all[f] = [[dist], [int(t)]]
                    # if dist and value are in dict    
                    else:                        
                        if self.d[f][0] > dist:  # if the current distance is less
                            self.d[f] = [dist, int(t)]  # replace the ID                                                                           
                        elif self.d[f][0] == dist:   # if dist is the same as previous                      
                            self.d[f].append(int(t))
                        if len(self.d_all[f][1]) <= 10: # Only stores 10 neighbor basins
                            self.d_all[f][0].append(dist)
                            self.d_all[f][1].append(int(t))