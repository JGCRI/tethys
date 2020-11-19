# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0,os.path.dirname(sys.path[0]))
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','DataReader'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','DataWriter'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','Diagnostics'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','reference'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','SpatialDownscaling'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','TemporalDownscaling'))
sys.path.insert(0,os.path.join(os.path.dirname(sys.path[0]),'tethys','Utils'))
# For Autodocs autosummary
sys.path.insert(0,os.path.dirname(os.path.dirname(sys.path[0])))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','DataReader'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','DataWriter'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','Diagnostics'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','reference'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','SpatialDownscaling'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','TemporalDownscaling'))
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(sys.path[0])),'tethys','Utils'))


# -- Autodoc initial settings -------------------------------------------------
autodoc_mock_imports = ["gcam_reader"]

# -- Project information -----------------------------------------------------

project = 'tethys'
copyright = '2020, Zarrar Khan'
author = 'Zarrar Khan'

# The full version, including alpha/beta/rc tags
release = '1.2.0'


# -- General configuration ---------------------------------------------------

# Adding this line to avoid error: 
# Sphinx error:contents.rst not found
# From: https://github.com/readthedocs/readthedocs.org/issues/2569
master_doc = 'index'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx_rtd_theme', 'sphinx.ext.autodoc', 'sphinx.ext.coverage', 'sphinx.ext.napoleon','sphinx.ext.autosummary']

autosummary_generate = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store','_templates']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"



# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']