Getting Started
==================================

About
-----------------------------------
Tethys is a water withdrawal downscaling package constructed at the Joint Global Change Research Institute of the Pacific Northwest National Laboratory (http://www.globalchange.umd.edu). It serves to link various hydrological models to the Global Change Analysis Model (GCAM) by disaggregating the geopolitical region and water basin data from GCAM into finer spatial and temporal resolutions.


Prerequisites
-----------------------------------
*	Python (3.7-3.9 should work) https://www.python.org/downloads/ 
*	Java https://www.java.com/en/download/




Installation
-----------------------------------
Currently, tethys can be cloned from https://github.com/JGCRI/tethys using::

    $ git clone https://github.com/JGCRI/tethys


Once downloaded, install as a Python package by running "setup.py" from the command line::

	$ python setup.py install

This will also install the dependencies listed in "requirements.txt". In order to avoid package version conflicts, consider creating a virtual environment for tethys.

In the future, easy installation will be available via pip.


Installing Package Data
-----------------------------------
Example data is available at https://zenodo.org/record/4780604#.YXGH8Z7MJPY. It is 2.1 GB.

Once extracted, change the filepaths in "config.ini" to point to the relevant files on your machine.

Run
-----------------------------------
If the installation was successful, Tethys can be imported with::
	
	from tethys.model import Tethys
	
Then, if the config file is properly set up, the model can be run using::

   dmw = Tethys('config.ini')
   
Logging info should begin printing to the console, and after a few minutes downscaled data and diagnostics files be created.
