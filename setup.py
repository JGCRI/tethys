import re
from setuptools import setup, find_packages


def readme():
    """Return the contents of the project README file."""
    with open('README.md') as f:
        return f.read()


def get_requirements():
    """Return a list of package requirements from the requirements.txt file."""
    with open('requirements.txt') as f:
        return f.read().split()


version = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", open('tethys/__init__.py').read(), re.M).group(1)

setup(
    name='tethys-downscaling',
    version=version,
    description='Spatial and Temporal Downscaling of Global Water Demands',
    url='https://github.com/JGCRI/tethys',
    packages=find_packages(),
    license='BSD-2-Clause',
    author='Isaac Thompson, Chris Vernon',
    python_requires='>=3.9, <4',
    include_package_data=True,
    install_requires=[
        'PyYAML>=6.0',
        'gcamreader>=1.2.5',
        'numpy>=1.22',
        'pandas>=1.2.4',
        'netCDF4>=1.6',
        'dask[complete]>=2022.12.1',
        'dask_geopandas>=0.3.1',
        'xarray>=2022.09.0',
        'rioxarray>=0.12.4',
        'tqdm>=4.66.2',
        'matplotlib>=3.8.3',
        'bokeh!=3.0.*,>=2.4.2',
        'geopandas>=0.14.3',
        'hvplot>=0.9.2',
    ],
    extras_require={
        'dev': [
            'build~=0.5.1',
            'nbsphinx~=0.8.6',
            'setuptools~=57.0.0',
            'sphinx>=5',
            'sphinx-panels~=0.6.0',
            'sphinx-rtd-theme~=0.5.2',
            'sphinx-mathjax-offline~=0.0.1',
            'twine>=3.4.1',
            'click-default-group>=1.2.4',
        ]
    }
)
