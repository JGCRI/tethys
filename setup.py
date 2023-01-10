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
    name='tethys',
    version=version,
    description='Spatial and Temporal Downscaling of Global Water Demands',
    url='https://github.com/JGCRI/tethys',
    packages=find_packages(),
    package_data={'tethys': ['reference/*']},
    license='BSD2-Simplified',
    author='Chris R. Vernon',
    author_email='chris.vernon@pnnl.gov',
    include_package_data=True,
    install_requires=[
        'PyYAML~=6.0',
        'gcamreader>=1.2.5',
        'numpy>=1.22',
        'pandas~=1.2.4',
        'netCDF4~=1.6',
        'dask~=2022.12.1',
        'xarray==2022.09.0',
        'rioxarray~=0.12.4',
        'requests~=2.20.0',
        'setuptools~=57.0.0'
    ],
    extras_require={
        'dev': [
            'build~=0.5.1',
            'nbsphinx~=0.8.6',
            'setuptools~=57.0.0',
            'sphinx~=4.0.2',
            'sphinx-panels~=0.6.0',
            'sphinx-rtd-theme~=0.5.2',
            'sphinx-mathjax-offline~=0.0.1',
            'twine~=3.4.1'
        ]
    }
)
