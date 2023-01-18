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
First of all you'll need to have `Python <https://www.python.org/downloads/>`_ installed.

If you plan on querying a GCAM database, you'll need `Java <https://openjdk.org>`_ installed and added to your path.


Currently, **tethys** can be cloned from https://github.com/JGCRI/tethys using::

    $ git clone https://github.com/JGCRI/tethys

The next commands need to be run from within the tethys directory you just downloaded, so change directory with::

    $ cd tethys

Once downloaded, install as a Python package by running *setup.py* from the command line::

    $ python setup.py install

This will automatically install the dependencies. In order to avoid package version conflicts, consider using a virtual environment.

In the future, easy installation will be available via pip.


Example Data
------------


Run
---
Verify the installation was successful by running the following in Python

.. code-block:: python

  from tethys import run_model

  m = run_model('tethys\example\config_minimal.yml')

   
