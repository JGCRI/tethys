User Guide
==========


Input files
-----------

The following is an overview of the example input files from :ref:`installing-package-data`.


Adapt from https://github.com/JGCRI/tethys/blob/main/docs/ReadMe_IO_Data.pdf

GCAM
^^^^

rgn32
^^^^^

harmonized_inputs
^^^^^^^^^^^^^^^^^

The term "grid" is used to describe the spatial resolution of 0.5 geographic degrees. A global full data map contains a total of 259,200 grid cells (360 x 720) of which 67,420 grid cells are categorized as "land grids" and are considered valid for simulation purposes. In this study, the land grid cells are used to define a "gridded" map according to the coordinates and the indexes of the 67,420 cells on the 360 x 720 grid. The inputs converted using the 67,420 grid cells according to the coordinate data file are called harmonized inputs.

Mostly uniformed dimension and format in this folder: one-row header csv file, 67,420 x 1, 0 means no assignment. Population files may have multiple columns

.. list-table:: harmonized_inputs
   :widths: auto
   :header-rows: 1

   * - File name
     - Description
     - Reference
     - Unit
   * - AEZ.csv
     - AEZ ID for each cell, 18 zones: 1-18
     - 
     -
   * - basin.csv
     - Basin ID for each cell, 235 basins: 1-235
     -
     -
   * - country.csv
     - Country ID for each cell, 249 countries: 1-249
     -
     -
   * - GMIA_cropland.csv
     - Irrigation areas in 2005 in each grid cell
     - Siebert, 2013 
     - km\ :sup:`2`  
   * - HYDE_cropland.csv
     - Irrigation area in 1900-2000 in each grid cell: every 10 years 
     - HYDE 3.1 Final, Klein Goldewijk et al., 2011
     - km\ :sup:`2`  
   * - HYDE_grassland.csv
     - Irrigation areas in 1900-2000 in each grid cell: every 10 years 
     - HYDE 3.1 Final, Klein Goldewijk et al., 2011
     - km\ :sup:`2`
   * - GPW_population.csv
     - Population: 1990-2015 data, every 5 years
     - CIESIN, 2016 
     - 
   * - HYDE_population.csv
     - Population: 1750-2000 data, every 10 years
     - HYDE 3.1 Final, Klein Goldewijk et al., 2011
     - 
   * - livestock_buffalo.csv
     - Number of buffalo in each grid cell
     - Wint and Robinson, 2007.
     - head 
   * - livestock_cattle.csv
     - Number of cattle in each grid cell
     - Wint and Robinson, 2007.
     - head 
   * - livestock_goat.csv
     - Number of goat in each grid cell
     - Wint and Robinson, 2007.
     - head 
   * - livestock_pig.csv
     - Number of pig in each grid cell
     - Wint and Robinson, 2007.
     - head 
   * - livestock_poultry.csv
     - Number of poultry in each grid cell
     - Wint and Robinson, 2007.
     - head 
   * - livestock_sheep.csv
     - Number of sheep in each grid cell
     - Wint and Robinson, 2007.
     - head 
   * - soil_moisture.csv
     - Maximum Soil Moisture
     - FAO, 2003.
     - mm/month 
   * - region32_grids.csv
     - Region ID for each cell, 32 regions: 1-32
     -
     -

TemporalDownscaling
^^^^^^^^^^^^^^^^^^^

Other
^^^^^


Configuration file
------------------

Tethys uses an INI configuration file to specify the input data, options, and output folder. The example "config.ini" is extensively commented.

Output files
------------



Implementation and Architecture
-------------------------------


.. figure:: _static/flowchart.png
  :width: 100%
  :alt: flowchart
  :align: center
  :figclass: align-center
  
  *Flowchart of Tethys*

Downscaling Algorithms
----------------------

Withdrawal data is downscaled spatially first (5 year regional -> 5 year gridded) then temporally (5 year gridded -> monthly gridded).

Spatial
^^^^^^^

For non-agricultural sectors (domestic, electricity, manfufacturing, and mining), water withdrawal in each grid square is assumed to be proportional to that square's population.

.. math::

	W_{grid} = W_{region}\frac{P_{grid}}{P_{region}}
	
Where *W* is withdrawal and *P* is population.



Temporal
^^^^^^^^



