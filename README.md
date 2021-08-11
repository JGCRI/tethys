[![DOI](https://zenodo.org/badge/104476654.svg)](https://zenodo.org/badge/latestdoi/104476654)
[![build](https://github.com/JGCRI/tethys/actions/workflows/build.yml/badge.svg)](https://github.com/JGCRI/tethys/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/JGCRI/tethys/branch/master/graph/badge.svg?token=EzEcfk940f)](https://codecov.io/gh/JGCRI/tethys)
[![docs](https://github.com/JGCRI/tethys/actions/workflows/docs.yml/badge.svg)](https://github.com/JGCRI/tethys/actions/workflows/docs.yml)

# Model Documentation
https://tethys-readthedocs.readthedocs.io

# Summary
Tethys serves as a critical step to link Xanthos (a global hydrologic model) and the Global Change Analysis Model (GCAM). The spatial resolution of GCAM is geopolitical regional scale for energy and economy systems (32 regions), and river basins for the land, agriculture, and water systems (235 water basins). GCAM is often used as a boundary condition and coupled to sectoral models, such as the Community Land Model and Xanthos, which typically operate at finer spatial and temporal scales than GCAM. For example, Xanthos is a globally gridded hydrology model that operates at monthly scale. Resolving such a mismatch in spatial and temporal scales facilitated coupling these models together. It is also helpful for understanding seasonal patterns of water use and acquiring high resolution water use data. The main objective of Tethys is to reconstruct global monthly gridded (0.5 geographic degree) water withdrawal datasets by spatial and temporal downscaling water withdrawal estimates at region/basin and annual scale. As an open-access software, Tethys applies statistical downscaling algorithms, to spatially and temporally downscale water withdrawal data from annual region/basin scale into monthly grid scale. In our study, the water withdrawals are separated into six sectors: irrigation, livestock, domestic, electricity (generation), manufacturing and mining.

# Get Started with Tethys
Set up Tethys using the following steps:
1.  Install Tethys from GitHub using:
    ```bash
    python -m pip install git+https://github.com/JGCRI/tethys.git
    ```
    
2.  Download the example data using the following in a Python prompt:
    ```python
    import tethys
    
    # the directory that you want to download and extract the example data to
    data_dir = "<my data download location>"
    
    # download and unzip the package data to your local machine
    tethys.get_package_data(data_dir)
    ```

3.  Setup your configuration file (.ini).  Inside the "example" directory that you just downloaded (`data_dir` from step 2 above) there will be two example configuration files:
- `data_dir`/example/config.ini
- `data_dir`/example/configDemeter.ini
Before you can run these examples please find and replace all absolute paths in each of these files from "C:/Z/models/tethysExampleFolders/example_v1_3_0/..." to "`data_dir`/example/...".

4.  To run Tethys:

    ```python
    import tethys
    
    # the path and file name that my example configuration (.ini) file was downloaded to
    config_file = '<path to my example config file>/config.ini'
    
    # run Tethys 
    tethys.run_model(config_file=config_file)
    ```

# Citation
Vernon, C.R.,  (2019, May 29). JGCRI/tethys: Tethys v2.0.0 (Version v1.3.0). Zenodo. UPDATE TO V2.0.0

# Supporting Documents
Li, X., Vernon, C.R., Hejazi, M.I., Link, R.P., Huang, Z., Liu, L. and Feng, L., 2018. Tethys – A Python Package for Spatial and Temporal Downscaling of Global Water Withdrawals. Journal of Open Research Software, 6(1), p.9. DOI: http://doi.org/10.5334/jors.197

# Contact Us
For questions, technical supporting and user contribution, please contact:

Zarrar Khan <zarrar.khan@pnnl.gov>

Chris Vernon <chris.vernon@pnnl.gov>

