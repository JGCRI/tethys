Getting started
===============

About
-----

The Capacity Expansion Regional Feasibility model (**cerf**) helps us evaluate the feasibility and structure of future electricity capacity expansion plans by siting power plants in areas that have been deemed the least cost option. We can use **cerf** to gain an understanding of topics such as: 1) whether or not future projected electricity expansion plans from models such as GCAM are possible to achieve, 2) where and which on-the-ground barriers to siting (e.g., protected areas, cooling water availability) may influence our ability to achieve certain expansions, and 3) how power plant infrastructure build outs and value may evolve into the future when considering locational marginal pricing (LMP) based on the supply and demand of electricity from a grid operations model.

**cerf** currently operates at a 1 km\ :superscript:`2` \ resolution over the conterminous United States. Each grid cell is given an initial value of suitable (0) or unsuitable (1) based on a collection of suitability criteria gleaned from the literature. **cerf**'s default suitability layers include both those that are common to all thermal technologies as well as technology-specific suitability criteria. Common suitability layers represent categories such as protected lands, critical habitat areas, and much more. Technology-specific suitability layers are those that satisfy requirements that may not be applicable to all technologies. An example would be minimum mean annual flow requirements for cooling water availability for individual thermal technologies.

We introduce a metric named Net Locational Cost (NLC) that is used compete power plant technologies for each grid cell based on the least cost option to site. NLC is calculated by subtracting the Net Operating Value (NOV) of a proposed power plant from the cost of its interconnection to the grid to represent the potential deployment value. Both the NOV parameter which incorporates many technology-specific values such as variable operations and maintenance costs, carbon price, heat rate, etc. and the interconnection cost parameter used for both electricity transmission and gas pipelines are configurable per time step.  All equations used in **cerf** are described in detail in the `documentation <https://immm-sfa.github.io/cerf/user_guide.html#fundamental-equations-and-concepts>`_.


Python version support
----------------------

Officially Python 3.7, 3.8, and 3.9


Installation
------------

**cerf** can be installed via pip by running the following from a terminal window::

    pip install cerf


Dependencies
------------

=============   ================
Dependency      Minimum Version
=============   ================
numpy           1.19.4
pandas          1.1.4
rasterio        1.2.3
xarray          0.16.1
PyYAML          5.4.1
requests        2.25.1
joblib          1.0.1
matplotlib      3.3.3
seaborn         0.11.1
whitebox        1.5.1
fiona           1.8.19
pyproj          3.0.1
rtree           0.9.7
shapely         1.7.1
geopandas       0.9.0
=============   ================


Optional dependencies
---------------------

==================    ================
Dependency            Minimum Version
==================    ================
sphinx_rtd_theme      0.5.1
sphinx_panels         0.6.0
==================    ================
