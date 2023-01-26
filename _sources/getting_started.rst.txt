Getting Started
===============
This page walks you through the steps of installing **tethys** and running an example. But first:

.. note:: This page is currently under construction in preparation for version 2

Motivation
----------
Integrated human-Earth systems models, such as GCAM, can project future water demand at a coarse, regionally-relevant scale by modeling long-term interactions between multiple sectors under a variety of scenarios, while gridded hydrology models simulate physical processes at a much finer spatial and temporal resolution. **tethys** facilitates coupling between these kinds of models by providing finer-scale water demand data while maintaining consistency with coarser-scale global dynamics.

.. figure:: _static/motivation.png
  :width: 100%
  :alt: spatial downscaling
  :align: center
  :figclass: align-center

While **tethys** is designed to integrate seamlessly with GCAM, it has the ability to downscale region-scale water demand data from other sources as well.


Installation
------------
As a prerequisite, you'll need to have `Python <https://www.python.org/downloads/>`_ installed, and if you plan on querying a GCAM database, `Java <https://openjdk.org>`_ must be installed and added to your path.

**tethys** can be installed from GitHub using pip::

  pip install git+https://github.com/JGCRI/tethys@dev

This will automatically install the dependencies. In order to avoid package version conflicts, consider using a virtual environment.

Try importing **tethys** to confirm that installation was succesful:

.. code-block:: python

  import tethys
  
  tethys.__version__  # should print '2.0.0'


Example Data
------------

Example data and configurations can be downloaded from Zenodo `here <https://doi.org/10.5281/zenodo.7569651>`_, or by using the following:

.. code-block:: python
  
  tethys.get_example_data()
  
The download decompresses to about 4.5GB. By default, it will make a directory called ``example`` at the root of the **tethys** pacakge, but you can specify another path.


Run
---
With the example data downloaded, a simple configuration can be run

.. code-block:: python

  # assuming you downloaded to the default location
  config_file = tethys.__file__.strip('__init__.py') + 'example\\config_example.yml'

  result = tethys.run_model(config_file)

