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
    license='BSD2-Simplified',
    author='Chris R. Vernon',
    author_email='chris.vernon@pnnl.gov',
    include_package_data=True,
    install_requires=[
        'configobj~=5.0.6',
        'numpy~=1.20.3',
        'pandas~=1.2.4',
        'scipy~=1.6.3',
        'requests~=2.20.0',
        'gcamreader~=1.2.4'
    ],
    extras_require={
        'dev': [
            'build~=0.5.1',
            'nbsphinx~=0.8.6',
            'setuptools~=57.0.0',
            'sphinx~=4.0.2',
            'sphinx-panels~=0.6.0',
            'sphinx-rtd-theme~=0.5.2',
            'twine~=3.4.1'
        ]
    }
)
