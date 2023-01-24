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


Example Data
------------


Run
---
Verify the installation was successful by running the following in Python

.. code-block:: python

  import tethys

  result = tethys.run_model('tethys\example\config_example.yml')

